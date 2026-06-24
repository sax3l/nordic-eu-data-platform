# Crawlee — Production Crawler Framework

> **Repo:** https://github.com/apify/crawlee | **Stars:** ~23K | **Language:** Python + Node.js | **License:** Apache 2.0

Apify's open-source crawler framework. Handles queuing, auto-scaling, proxy rotation, retries, session management, and browser automation. The platform's primary orchestration layer for bulk web harvesting.

## What it solves

Raw Playwright/Puppeteer has no queue management, no auto-retry, no request routing, no session pool. Crawlee adds all of that without locking into a platform — fully OSS, fully local. Drop in Playwright as the crawler backend, get production-grade crawling infrastructure.

## Install

```bash
# Python
pip install crawlee[playwright]

# Node.js
npm install crawlee playwright
```

## Core Patterns

### Basic Crawler with Playwright (Python)

```python
import asyncio
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.router import Router

router = Router[PlaywrightCrawlingContext]()

@router.default_handler
async def default_handler(context: PlaywrightCrawlingContext) -> None:
    title = await context.page.title()
    await context.push_data({"url": context.request.loaded_url, "title": title})

async def main():
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=100,
        headless=True,
        browser_type="chromium",
        request_handler=router,
    )
    await crawler.run(["https://example.com"])

asyncio.run(main())
```

### Proxy Rotation + Routing

```python
from crawlee.proxy_configuration import ProxyConfiguration

proxy_config = ProxyConfiguration(
    proxy_options=[
        {"url": "http://proxy1:8080"},
        {"url": "http://proxy2:8080"},
    ]
)

crawler = PlaywrightCrawler(
    proxy_configuration=proxy_config,
    session_pool_max_size=50,  # session-per-proxy rotation
)
```

### Adaptive Request Handler (our pattern)

```python
@router.default_handler
async def handler(context: PlaywrightCrawlingContext) -> None:
    url = context.request.url

    # Report back to adaptive router
    await context.push_data({
        "url": url,
        "status": context.response.status,
        "latency_ms": context.crawling_context.get("timing", {}).get("total_ms", 0),
        "body_size": len(await context.page.content()),
        "captcha_detected": await check_captcha(context.page),
    })

    # Auto-enqueue found links
    await context.enqueue_links()
```

### Enqueue from a list (batch mode)

```python
from crawlee.storages.request_list import RequestList

orgnr_list = [f"https://example.com/org/{nr}" for nr in range(5590000000, 5590001000)]
rlist = await RequestList.open(urls=orgnr_list)

crawler = PlaywrightCrawler(request_list=rlist, request_handler=router)
await crawler.run()
```

## Speed

- HTTP-only (BeautifulSoup): ~500-1000 requests/min per worker
- Playwright headless: ~60-100 pages/min per worker
- Auto-scaling: spawns workers up to `max_concurrency` (typically CPU cores × 2)
- 50 workers on Docker swarm = ~3000-5000 pages/min

## In the Adaptive Router

```
┌──────────────┐
│ sources.yaml  │ ─── enqueue ──► Crawlee RequestQueue
└──────────────┘                        │
                                        ▼
                              ┌─────────────────┐
                              │ Adaptive Handler │
                              │ (per-host bandit)│
                              └──────┬──────────┘
                                     │ method chosen by bandit
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
    curl_cffi                 Playwright+Stealth           CloakBrowser
    (static sites)            (JS-heavy sites)             (WAF-protected)
```

## Related

- [FlareSolverr Integration](flaresolverr.md)
- [Rota Proxy Rotation](rota-proxy.md)
- [Stealth Bypass Chain](stealth-bypass-chain.md)
- [CloakBrowser](cloakbrowser.md)
