# FlareSolverr — Cloudflare Challenge Solver

> **Repo:** https://github.com/FlareSolverr/FlareSolverr | **Stars:** ~14K | **Language:** Python | **License:** MIT

Proxy server that sits between your scraper and Cloudflare-protected sites. Solves IUAM (I'm Under Attack Mode), JS challenges, and Turnstile automatically. Docker-native with a simple HTTP API — send a request, get back the unblocked page.

## What it solves

Cloudflare's browser check, 5-second shield, and JS challenges block raw HTTP requests. FlareSolverr spins up a headless browser, solves the challenge, stores the session cookies, and proxies your request. After the challenge is solved, subsequent requests to the same domain reuse the session.

## Install

```bash
docker pull flaresolverr/flaresolverr:latest
docker run -d --name flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  -e LOG_HTML=false \
  -e CAPTCHA_SOLVER=none \
  flaresolverr/flaresolverr:latest
```

## API

```python
import requests

resp = requests.post("http://localhost:8191/v1", json={
    "cmd": "request.get",
    "url": "https://cloudflare-protected-site.com",
    "maxTimeout": 60000,
    "session": "session-pool-1",  # reuse session cookies
    "proxy": {"url": "http://rotator:8080"},  # optional proxy
})
data = resp.json()
# data["solution"]["response"] → HTML content
# data["solution"]["cookies"] → session cookies
# data["solution"]["status"] → 200
# data["solution"]["headers"] → response headers
```

## Crawlee Integration

```python
from crawlee.playwright_crawler import PlaywrightCrawler

# Use FlareSolverr as the proxy
crawler = PlaywrightCrawler(
    proxy_configuration=ProxyConfiguration(
        proxy_options=[{"url": "http://localhost:8191"}]
    ),
    request_handler=handler,
)
# Or call it pre-crawl to get cookies, then inject into crawler session
```

## Session Reuse (critical for speed)

```python
# Session solves challenge ONCE, then cookies persist
def get_via_flaresolverr(url, session_id):
    resp = requests.post("http://localhost:8191/v1", json={
        "cmd": "request.get",
        "url": url,
        "session": session_id,  # Must be unique per site
        "maxTimeout": 60000,
    })
    return resp.json()

# First request solves challenge (~5-10s), subsequent are instant
session = "bolagsverket-se-001"
get_via_flaresolverr("https://bolagsverket.se", session)  # ~7s
get_via_flaresolverr("https://bolagsverket.se/foretag/559000-0001", session)  # ~0.3s
```

## In the Fallback Chain

```
Position: CF / Anti-Bot Tier (Tier 2)
Preceded by: cloudscraper (lighter, but weaker)
Succeeded by: Camoufox → CloakBrowser (heavier, more capable)
```

Used as the first escalation when cloudscraper fails. If FlareSolverr also fails, the site is either:
- DataDome/Akamai/Imperva (needs CloakBrowser)
- Turnstile with HCaptcha fallback (needs external solver)
- Requiring browser fingerprint consistency (needs CloakBrowser profiles)

## Speed

- First request (cold session): 5-15s (challenge solve time)
- Subsequent requests (warm session): 0.2-0.5s
- Container memory: ~500MB
- Max sessions: ~20 per container (session pool memory)

## Limits

- Breakable by CF updates (weekly patches, but FlareSolverr updates respond within days)
- Session cookies expire (typically 30 min — auto-refresh)
- Not a full browser — can't interact with DOM (that's CloakBrowser/Playwright tier)
- HCaptcha/Turnstile needs CAPTCHA_SOLVER configured with 3rd party key
- DataDome: inconsistent (FlareSolverr targets CF specifically)

## Related

- [cloudscraper runbook](cloudscraper.md)
- [CloakBrowser](cloakbrowser.md)
- [Stealth Bypass Chain](stealth-bypass-chain.md)
- [Rota Proxy Rotation](rota-proxy.md)
