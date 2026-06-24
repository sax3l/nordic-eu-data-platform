# CloakBrowser — Ultimate Stealth Browser (2026)

> **Repo:** https://github.com/CloakHQ/CloakBrowser | **Stars:** ~27K | **Language:** C++/Python | **License:** MIT

Source-level patched Chromium. Passes 30/30 bot-detection benchmarks (FpCollect, CreepJS, Incolumitas, Pixelscan, etc.). Not JS-patch-level — actual C++ source modifications. Drop-in replacement for Playwright/Puppeteer/Selenium via CDP.

## What it solves

Every other stealth solution (undetected-chromedriver, playwright-stealth, camoufox) patches JS properties. CloakBrowser patches the **C++ source** — navigator properties, hardware sensors, font enumeration, WebGL fingerprints, audio contexts, canvas. Cloudflare Turnstile, DataDome, Akamai, Imperva — all bypassed.

## Install

```bash
# Docker (recommended — clean isolation per worker)
docker pull cloakhq/cloakbrowser
docker run --rm -p 9222:9222 cloakhq/cloakbrowser

# Or direct binary
# Download from https://github.com/CloakHQ/CloakBrowser/releases
```

## Playwright Integration (primary path)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Connect to CloakBrowser CDP instead of launching own browser
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.new_context(
        geolocation={"longitude": 18.0686, "latitude": 59.3293},  # Stockholm
        locale="sv-SE",
        timezone_id="Europe/Stockholm",
        permissions=["geolocation"],
    )
    page = context.new_page()
    page.goto("https://cloudflare-protected-site.com", wait_until="networkidle")
    print(page.content())
    page.close()
    browser.close()
```

## Proxy + GeoIP Matching

```python
browser = p.chromium.connect_over_cdp("http://localhost:9222")
context = browser.new_context(
    proxy={
        "server": "http://local-proxy-rotator:8080",
        "username": os.getenv("PROXY_USER"),
        "password": os.getenv("PROXY_PASS"),
    },
    geolocation={"longitude": 13.4050, "latitude": 52.5200},  # Berlin
    locale="de-DE",
    timezone_id="Europe/Berlin",
)
```

## Fingerprint Rotation

CloakBrowser-Manager (Docker GUI) persists profiles:
```bash
# Each profile = unique fingerprint + cookies + localStorage
docker run -d --name cb-manager -p 3000:3000 cloakhq/cloakbrowser-manager
# API: POST /profiles → returns CDP ws endpoint for that profile
```

Via API:
```python
import requests
resp = requests.post("http://localhost:3000/api/profiles", json={
    "os": "windows",
    "browser": "chrome",
    "geolocation": "Stockholm",
    "proxy": "http://rotator:8080",
})
profile = resp.json()
# Connect: profile["cdp_endpoint"] = "ws://localhost:9222/devtools/browser/UUID"
```

## Speed

- Headless mode: ~300-500ms per page load
- Headful mode (needed for toughest sites): ~800-1200ms
- Memory: ~200MB per instance
- Parallelism: 5-10 instances on 32GB RAM

## In the Fallback Chain

```
Position: Browser Tier (Tier 3)
Preceded by: FlareSolverr → Camoufox → Botasaurus
Succeeded by: Sequentum (RPA tier, for visual-only portals)
```

CloakBrowser is the **last free tier** before licensed tools. If it fails, the site requires visual RPA (Sequentum/UiPath) or is a pure API-gated portal.

## Known Limits

- Cloudflare 5-second shield sometimes requires headful mode
- HCaptcha Enterprise still needs external solver
- DataDome Device Check passes 95% of the time but not 100%
- Per-instance CDP port — orchestrate with port manager

## Related

- [CloakBrowser vs Camoufox vs Undetected-playwright benchmarks](stealth-benchmarks.md)
- [Stealth Bypass Chain](stealth-bypass-chain.md)
- [Account Creation Pipeline](account-creation.md)
