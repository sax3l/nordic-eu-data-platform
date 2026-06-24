# Example: Bypass Test Suite
# Tests each method in the stealth bypass chain against known CF/WAF sites.
# Run: python examples/test_bypass_chain.py
# Purpose: Verify the chain works before running production jobs.

import asyncio
import time
import json
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# Test Sites (known WAF-protected targets)
# =============================================================================

TEST_SITES = {
    # Cloudflare (various protection levels)
    "cf-standard": "https://httpbin.org/headers",  # No CF, baseline
    "cf-basic": "https://bolagsverket.se",         # Light CF
    "cf-medium": "https://cloudflare.com",         # CF itself (strongest CF)

    # Other WAFs
    "datadome": "https://www.footlocker.com",       # DataDome
    "akamai": "https://www.ibm.com",                # Often Akamai

    # EU Registries
    "bolagsverket": "https://bolagsverket.se",
    "handelsregister": "https://www.handelsregister.de",
    "companies-house": "https://find-and-update.company-information.service.gov.uk",
}

# =============================================================================
# Methods in the bypass chain
# =============================================================================

@dataclass
class MethodResult:
    method: str
    url: str
    success: bool
    status_code: int
    latency_ms: float
    content_size: int
    error: Optional[str] = None

async def test_curl_cffi(url: str) -> MethodResult:
    """Level 0: curl_cffi with TLS impersonation."""
    import curl_cffi.requests as curlreq
    start = time.perf_counter()
    try:
        resp = curlreq.get(url, impersonate="chrome124", timeout=15)
        latency = (time.perf_counter() - start) * 1000
        success = resp.status_code == 200 and len(resp.text) > 500
        return MethodResult("curl_cffi", url, success, resp.status_code, latency, len(resp.text))
    except Exception as e:
        return MethodResult("curl_cffi", url, False, 0, (time.perf_counter() - start) * 1000, 0, str(e)[:100])

async def test_cloudscraper(url: str) -> MethodResult:
    """Level 1: cloudscraper for basic CF bypass."""
    import cloudscraper
    start = time.perf_counter()
    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, timeout=15)
        latency = (time.perf_counter() - start) * 1000
        success = resp.status_code == 200 and len(resp.text) > 500
        return MethodResult("cloudscraper", url, success, resp.status_code, latency, len(resp.text))
    except Exception as e:
        return MethodResult("cloudscraper", url, False, 0, (time.perf_counter() - start) * 1000, 0, str(e)[:100])

async def test_flaresolverr(url: str) -> MethodResult:
    """Level 2: FlareSolverr proxy."""
    import requests
    start = time.perf_counter()
    try:
        resp = requests.post("http://localhost:8191/v1", json={
            "cmd": "request.get", "url": url, "maxTimeout": 30000
        }, timeout=35)
        data = resp.json()
        latency = (time.perf_counter() - start) * 1000
        success = data.get("solution", {}).get("status") == 200
        content_size = len(data.get("solution", {}).get("response", ""))
        return MethodResult("flaresolverr", url, success, 200 if success else 0, latency, content_size)
    except Exception as e:
        return MethodResult("flaresolverr", url, False, 0, (time.perf_counter() - start) * 1000, 0, str(e)[:100])

async def test_playwright(url: str) -> MethodResult:
    """Level 5-6: Playwright (optionally via CloakBrowser CDP)."""
    from playwright.async_api import async_playwright
    start = time.perf_counter()
    try:
        async with async_playwright() as p:
            cdp_endpoint = "http://localhost:9222"  # CloakBrowser CDP
            try:
                browser = await p.chromium.connect_over_cdp(cdp_endpoint)
            except:
                browser = await p.chromium.launch(headless=True)

            page = await browser.new_page()
            resp = await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            status = resp.status if resp else 0
            await browser.close()
            latency = (time.perf_counter() - start) * 1000
            success = status == 200 and len(content) > 500
            return MethodResult("playwright", url, success, status, latency, len(content))
    except Exception as e:
        return MethodResult("playwright", url, False, 0, (time.perf_counter() - start) * 1000, 0, str(e)[:100])

# =============================================================================
# Test Runner
# =============================================================================

async def run_bypass_tests():
    results = []

    for site_name, url in TEST_SITES.items():
        print(f"\n{'='*60}\nTesting {site_name}: {url}")

        for test_fn in [test_curl_cffi, test_cloudscraper, test_flaresolverr, test_playwright]:
            result = await test_fn(url)
            status = "OK" if result.success else "FAIL"
            print(f"  {result.method:20s} → HTTP {result.status_code} {result.latency_ms:8.0f}ms {result.content_size:8d}B  {status}")
            if result.error:
                print(f"    Error: {result.error}")
            results.append(result.__dict__)

    # Summary table
    print(f"\n{'='*60}\nBYPASS CHAIN TEST RESULTS")
    print(f"{'Method':<20s} {'Site':<25s} {'Status':>5s} {'Latency':>10s} {'Result':>6s}")
    print("-" * 75)
    for r in results:
        print(f"{r['method']:<20s} {r['url']:<45s} {r['status_code']:>4d} {r['latency_ms']:9.0f}ms {'OK' if r['success'] else 'FAIL':>6s}")

    # Save to JSON
    with open("bypass_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to bypass_test_results.json")

    # Recommendations
    print(f"\nRECOMMENDED METHODS PER SITE:")
    by_site = {}
    for r in results:
        by_site.setdefault(r["url"], []).append(r)
    for site, methods in by_site.items():
        successful = [m["method"] for m in methods if m["success"]]
        if successful:
            print(f"  {site}: Use {successful[0]} (cheapest success)")

if __name__ == "__main__":
    asyncio.run(run_bypass_tests())
