# Stealth Bypass Chain — Complete Anti-Detection Strategy

> **Purpose:** The platform's defense-in-depth against Cloudflare, DataDome, Akamai, Imperva, and custom anti-bot. A laminated escalation chain from cheapest to strongest.

## The Chain (sense → adapt → escalate)

```
LEVEL 0: Direct HTTP (curl_cffi TLS impersonation)
   │  Fails with: 403, 429, CF challenge page, empty body
   ▼
LEVEL 1: cloudscraper (Python, automatic CF solve)
   │  Fails with: advanced JS challenge, Turnstile, DataDome
   ▼
LEVEL 2: FlareSolverr (Docker proxy, CF JS challenge)
   │  Fails with: Turnstile, DataDome, Akamai, Imperva
   ▼
LEVEL 3: Camoufox (Firefox-based, randomized fingerprint)
   │  Fails with: Chrome-only sites, advanced fingerprinting
   ▼
LEVEL 4: Botasaurus (Selenium+stealth, anti-CF tuned)
   │  Fails with: stateful portals, login-gated, DataDome
   ▼
LEVEL 5: nodriver / Patchright (undetected Playwright/Selenium)
   │  Fails with: extreme fingerprinting, canvas/WebGL detection
   ▼
LEVEL 6: CloakBrowser (C++ source-patched Chromium, 30/30 benchmarks)
   │  Fails with: HCaptcha Enterprise, some Imperva modes
   ▼
LEVEL 7: Browser-Use agent + CloakBrowser (AI-driven interaction)
   │  Fails with: stateful login-gated portals with 2FA
   ▼
LEVEL 8: Sequentum / UiPath / Ranorex (licensed RPA, visual interaction)
```

## Per-WAF Strategy Matrix

### Cloudflare (all modes)

| Mode | Detection | Bypass Chain |
|---|---|---|
| Standard (no challenge) | Just proxies | Level 0-1 (curl_cffi, cloudscraper) |
| IUAM (I'm Under Attack) | Browser check JS | Level 2-3 (FlareSolverr, Camoufox) |
| JS Challenge | 5-second challenge | Level 2-3 (FlareSolverr with session) |
| Turnstile (no CAPTCHA) | Device fingerprinting | Level 6 (CloakBrowser, headful + consistent profile) |
| Turnstile + HCaptcha | Device + human check | Level 6 + external CAPTCHA solver or human fallback |
| WAF Rule (strict) | IP reputation + request pattern | All levels + proxy rotation (Tor preferred) |

### DataDome

| Signal | Bypass |
|---|---|
| TLS/JA3 fingerprint | curl_cffi (Level 0) or CloakBrowser CDP (Level 6) |
| Browser fingerprint | CloakBrowser (source-patched, not JS-patched) |
| Behavioral (mouse/keyboard) | Playwright with human-like delays (0.1-0.5s random) between actions |
| IP reputation | Residential-like IPs (Tor circuits, self-hosted on residential VPS) |
| Request pattern | Spread requests across sessions, randomized inter-request delays 1-10s |

**Best approach:** Level 6 (CloakBrowser) + Tor proxy + headful mode + randomized interaction delays. DataDome is the most aggressive after CF — if CloakBrowser fails with DataDome, escalate to Level 8 (Sequentum with real-human-interaction recording).

### Akamai

Akamai's bot detection is primarily behavioral + TLS fingerprinting. curl_cffi with TLS impersonation (Level 0) often works directly. If not:

1. CloakBrowser (Level 6) — passes behavioral checks natively
2. Headful mode — Akamai sometimes gates specifically on headless
3. Consistent session — cookie persistence across requests

### Imperva (formerly Incapsula)

Oldest, weakest, most predictable. FlareSolverr (Level 2) typically handles it. If not, Camoufox (Level 3) or any stealth browser.

## Identity Rotation (the missing piece)

The bypass chain above focuses on *getting through*. Identity rotation focuses on *not getting burned*. Without it, even the best bypass is detected after N requests from the same "fingerprint".

### Coherent Identity Per Session

Never rotate identity mid-session. Each session = one consistent "persona":
- Fixed User-Agent (from a common real browser build)
- Fixed screen resolution (1920×1080 or 2560×1440 — common, don't use rare combos)
- Fixed platform (Win32, MacIntel, Linux x86_64)
- Fixed WebGL vendor + renderer (matches the platform)
- Fixed timezone + locale (matches the proxy GeoIP)
- Fixed font list (from the OS the persona "uses")
- Fixed canvas fingerprint (deterministic per persona, not random)

### Profile Pool

```python
# 200 pre-generated consistent persona profiles
personas = [
    {
        "name": "windows-chrome-stockholm-01",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "Win32",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "timezone": "Europe/Stockholm",
        "locale": "sv-SE",
        "geolocation": {"latitude": 59.3293, "longitude": 18.0686},
        "proxy": "socks5://tor-circuit-3:9050",
    },
    # ... 199 more, spread across 20 geo-locations × 10 browser builds each
]
```

### When to Rotate

| Trigger | Action |
|---|---|
| 403/429 response | Rotate proxy + persona immediately (not just proxy) |
| CF challenge page | Rotate proxy only (persona may be fine) |
| Successful 200 for 10+ min | Rotate proxy, keep persona (stretch session) |
| End of batch job | Rotate everything for next batch |

## Proxy Tier Assignment

| Site Risk | Proxy Type | Rotation Speed |
|---|---|---|
| Open API (no anti-bot) | Free list or datacenter | Every 100 requests |
| Soft CF (only rate limit) | Self-hosted VPS pool | Every 50 requests |
| Aggressive CF | Tor circuits (4-5 per worker) | Every 10 requests |
| DataDome / Akamai | Tor + session stickiness | Every 5 requests |
| Stateful portal (login) | Fixed residential-like (no rotation) | Never during session |

## Speed vs Stealth Tradeoff

| Mode | Requests/min (per worker) | Anti-bot survival |
|---|---|---|
| Full stealth (CloakBrowser + Tor + headful + human delays) | 3-5 | 98% |
| Moderate stealth (CloakBrowser + self-hosted proxy + headless) | 20-30 | 90% |
| Light stealth (FlareSolverr + session reuse) | 100-200 | 70% |
| No stealth (curl_cffi only) | 500-1000 | 50% |

The adaptive router auto-selects based on: success rate, block rate, and `waf` field from `sources.yaml`.

## Secret Checklist per Site Registration

Before scraping a new registry:

1. **Check sources.yaml** — `waf`, `method`, `proxy_tier` fields
2. **Probe with Level 0** — curl_cffi direct, see what happens
3. **If blocked** → walk up the chain until success
4. **Log the winning level** → bandit remembers for this host
5. **Re-probe every 4 hours** — registries change; keep adapting

## Related

- [CloakBrowser](cloakbrowser.md) — Level 6 implementation
- [Rota Proxy Rotation](rota-proxy.md) — proxy pool management
- [FlareSolverr](flaresolverr.md) — Level 2 CF solver
- [Account Creation Pipeline](account-creation.md) — uses full persona profiles
- [Sources Registry](../../sources/sources.yaml) — waf/method per site
