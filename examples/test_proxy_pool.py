# Example: Proxy Pool Test
# Tests connectivity through each proxy tier.
# Run: python examples/test_proxy_pool.py

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXIES = {
    "direct": None,  # No proxy (baseline)
    "rotator": "http://localhost:8080",  # Rota proxy rotator
    "tor-1": "socks5://localhost:9050",
    "tor-2": "socks5://localhost:9052",
    "self-hosted": "http://localhost:3128",  # Squid/HAProxy
}

TEST_URLS = [
    "https://httpbin.org/ip",
    "https://api.ipify.org?format=json",
    "https://bolagsverket.se",
]

def test_proxy(name: str, proxy_url: str | None, test_url: str) -> dict:
    start = time.perf_counter()
    try:
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        resp = requests.get(test_url, proxies=proxies, timeout=15)
        latency = (time.perf_counter() - start) * 1000
        return {
            "proxy": name,
            "url": test_url,
            "success": resp.status_code == 200,
            "status_code": resp.status_code,
            "latency_ms": round(latency, 1),
            "ip": resp.json().get("ip", resp.json().get("origin", "?")) if "json" in resp.headers.get("content-type", "") else "?",
            "size": len(resp.text),
        }
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return {
            "proxy": name,
            "url": test_url,
            "success": False,
            "error": str(e)[:100],
            "latency_ms": round(latency, 1),
        }

def main():
    results = []
    tasks = [(name, proxy, url) for name, proxy in PROXIES.items() for url in TEST_URLS]

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(test_proxy, name, proxy, url): (name, url) for name, proxy, url in tasks}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = "OK" if result["success"] else "FAIL"
            ip = result.get("ip", "?")
            print(f"  {result['proxy']:15s} → {result['url']:50s} {result['latency_ms']:6.0f}ms  {ip:20s}  {status}")

    with open("proxy_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to proxy_test_results.json")

if __name__ == "__main__":
    main()
