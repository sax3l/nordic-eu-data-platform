# Adaptive Router — Multi-Armed Bandit Method Selector
# Used by the orchestrator and workers to pick the best method per host.

import asyncio
import json
import time
from collections import defaultdict
from typing import Optional

METHOD_COST = {
    "curl_cffi": 1,
    "cloudscraper": 2,
    "flaresolverr": 3,
    "crawlee": 4,
    "playwright": 5,
    "cloakbrowser": 6,
    "browser_use": 7,
    "sequentum": 8,
    "uipath": 9,
    "ranorex": 10,
}

METHOD_TIERS = {
    "cheap": ["curl_cffi", "cloudscraper"],
    "medium": ["flaresolverr", "crawlee"],
    "heavy": ["playwright", "cloakbrowser"],
    "rpa": ["sequentum", "uipath", "ranorex"],
}

class AdaptiveRouter:
    def __init__(self):
        self.stats: dict = defaultdict(lambda: defaultdict(lambda: {
            "successes": 0, "failures": 0, "blocks": 0,
            "latencies": [], "last_used": 0,
        }))

    def record(self, host: str, method: str, success: bool, latency_ms: float, blocked: bool = False):
        s = self.stats[host][method]
        if success:
            s["successes"] += 1
        else:
            s["failures"] += 1
        if blocked:
            s["blocks"] += 1
        s["latencies"].append(latency_ms)
        if len(s["latencies"]) > 100:
            s["latencies"] = s["latencies"][-100:]
        s["last_used"] = time.time()

    def choose_method(self, host: str, available_methods: list[str]) -> str:
        """Pick the best method for this host. Cheapest that currently works wins."""
        if host not in self.stats or not self.stats[host]:
            # Unknown host — try cheapest first
            return min(available_methods, key=lambda m: METHOD_COST.get(m, 99))

        stats = self.stats[host]
        best_method = None
        best_score = -1

        for method in available_methods:
            s = stats.get(method)
            if s is None:
                # Never tried — give it a chance
                score = 0.6 - (METHOD_COST.get(method, 99) * 0.01)
            else:
                total = s["successes"] + s["failures"]
                if total == 0:
                    score = 0.5
                else:
                    success_rate = s["successes"] / total
                    # Penalize blocked methods heavily
                    block_penalty = (s["blocks"] / max(total, 1)) * 0.5
                    # Reward low latency
                    avg_latency = sum(s["latencies"][-20:]) / max(len(s["latencies"][-20:]), 1)
                    latency_score = min(1.0, 1000 / max(avg_latency, 1))
                    score = (success_rate * 0.6) + (latency_score * 0.3) - block_penalty

            if score > best_score:
                best_score = score
                best_method = method

        return best_method or available_methods[0]

    def choose_fallback(self, host: str, failed_method: str, available_methods: list[str]) -> str:
        """Choose the next method to try after one failed."""
        self.record(host, failed_method, False, 0)
        remaining = [m for m in available_methods if m != failed_method]
        if not remaining:
            return available_methods[0]
        # Escalate to next tier
        return self.choose_method(host, remaining)

    def get_success_rate(self, host: str, method: str) -> float:
        s = self.stats[host].get(method)
        if not s:
            return 0.0
        total = s["successes"] + s["failures"]
        return s["successes"] / total if total > 0 else 0.0

    def to_dict(self) -> dict:
        """Export stats for persistence."""
        result = {}
        for host, methods in self.stats.items():
            result[host] = {}
            for method, s in methods.items():
                result[host][method] = {
                    "successes": s["successes"],
                    "failures": s["failures"],
                    "blocks": s["blocks"],
                    "success_rate": s["successes"] / max(s["successes"] + s["failures"], 1),
                    "avg_latency_ms": sum(s["latencies"][-20:]) / max(len(s["latencies"][-20:]), 1) if s["latencies"] else 0,
                    "last_used": s["last_used"],
                }
        return result

class AIMDController:
    """Additive Increase / Multiplicative Decrease concurrency control."""
    def __init__(self, max_concurrency: int = 10, min_concurrency: int = 1):
        self.concurrency = 1
        self.max = max_concurrency
        self.min = min_concurrency
        self.consecutive_successes = 0
        self.consecutive_failures = 0

    def on_success(self):
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        if self.consecutive_successes >= 5:
            self.concurrency = min(self.max, self.concurrency + 1)
            self.consecutive_successes = 0

    def on_failure(self, status: int = 0):
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        if status in (429, 403) or self.consecutive_failures >= 3:
            self.concurrency = max(self.min, int(self.concurrency * 0.5))
            self.consecutive_failures = 0

    def on_block(self):
        self.consecutive_failures += 1
        self.concurrency = max(self.min, int(self.concurrency * 0.3))

    @property
    def is_throttled(self) -> bool:
        return self.concurrency <= 2
