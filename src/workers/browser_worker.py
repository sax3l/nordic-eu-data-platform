# Browser Worker — General Scraping Worker
# Polls Redis for scraping jobs, executes with adaptive method selection.
# Part of the nordic-eu-data-platform worker pool.

import asyncio
import json
import os
import time
import traceback
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
import httpx
import trafilatura
from playwright.async_api import async_playwright

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://platform:changeme@localhost:5432/nordic_eu_data")
CLOAKBROWSER_CDP = os.getenv("CLOAKBROWSER_CDP", "http://localhost:9222")
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "3"))

redis_client = redis.from_url(REDIS_URL)
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# ============================================================================
# METHOD HANDLERS (cheapest first)
# ============================================================================

async def scrape_http(url: str, timeout: int = 15) -> Optional[str]:
    """Level 0: Direct HTTP with TLS impersonation."""
    import curl_cffi.requests as curlreq
    try:
        resp = curlreq.get(url, impersonate="chrome124", timeout=timeout)
        return resp.text if resp.status_code == 200 else None
    except Exception:
        return None

async def scrape_flaresolverr(url: str, timeout: int = 30) -> Optional[str]:
    """Level 2: FlareSolverr CF bypass."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post("http://flaresolverr:8191/v1", json={
                "cmd": "request.get", "url": url, "maxTimeout": 25000
            })
            data = resp.json()
            if data.get("solution", {}).get("status") == 200:
                return data["solution"]["response"]
    except Exception:
        pass
    return None

async def scrape_playwright(url: str, timeout: int = 30) -> Optional[str]:
    """Level 5-6: Playwright with CloakBrowser CDP."""
    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(CLOAKBROWSER_CDP)
            except Exception:
                browser = await p.chromium.launch(headless=True)

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()
            resp = await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            content = await page.content()
            await browser.close()
            return content if resp and resp.status == 200 else None
    except Exception:
        return None

# ============================================================================
# EXTRACTION
# ============================================================================

def extract_text(html: str) -> str:
    """Strip boilerplate, return clean text."""
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    return text or ""

async def llm_extract(text: str, instruction: str) -> dict:
    """Extract structured data via local LLM."""
    if len(text) < 50:
        return {}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/chat/completions",
                json={
                    "model": "phi4:14b",
                    "messages": [{"role": "user", "content": f"{instruction}\n\nText: {text[:4000]}"}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                }
            )
            return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception:
        return {}

# ============================================================================
# WORKER LOOP
# ============================================================================

METHODS = [
    ("curl_cffi", scrape_http),
    ("flaresolverr", scrape_flaresolverr),
    ("playwright", scrape_playwright),
]

async def process_job(task: dict):
    """Process a single scraping job."""
    task_id = task.get("id", "unknown")
    url = task.get("url")
    job_type = task.get("type", "scrape")

    print(f"[{task_id}] Processing {url}")

    start = time.perf_counter()
    result = {"task_id": task_id, "url": url, "success": False, "method": None}

    # Try methods in order (cheapest first)
    for method_name, method_fn in METHODS:
        try:
            content = await method_fn(url)
            if content and len(content) > 100:
                latency = (time.perf_counter() - start) * 1000
                result["success"] = True
                result["method"] = method_name
                result["latency_ms"] = latency
                result["content_size"] = len(content)

                # Extract text
                text = extract_text(content)

                # LLM enrichment if requested
                if job_type == "enrich":
                    contacts = await llm_extract(text, "Extract all people with names, titles, emails, and phones. Return JSON array.")
                    company = await llm_extract(text, "Extract company info: name, org number, address, website, industry. Return JSON.")
                    result["contacts"] = contacts
                    result["company"] = company

                result["text"] = text[:1000]
                break
        except Exception as e:
            print(f"[{task_id}] {method_name} failed: {e}")
            continue

    if result["success"]:
        print(f"[{task_id}] SUCCESS via {result['method']} ({result['latency_ms']:.0f}ms)")
    else:
        result["error"] = "All methods failed"
        print(f"[{task_id}] FAILED: all methods exhausted")

    # Store result
    await redis_client.hset("results", task_id, json.dumps(result, default=str))

async def main():
    print(f"Browser worker starting. Methods: {[m[0] for m in METHODS]}")
    print(f"Max concurrent: {MAX_CONCURRENT}")

    while True:
        result = await redis_client.blpop("queue:scrape", timeout=30)
        if result is None:
            continue

        _, task_json = result
        task = json.loads(task_json)

        async with semaphore:
            asyncio.create_task(process_job(task))

if __name__ == "__main__":
    asyncio.run(main())
