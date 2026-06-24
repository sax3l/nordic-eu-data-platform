# Fake Identity Stack — Coherent Persona Generation

> **Purpose:** Generate consistent, realistic personas for browser sessions. Each persona has a matching fingerprint, proxy location, browser profile, and contact details. Used by the account creation pipeline and session rotation system.

## What it solves

Rotating proxies alone is not enough. Modern anti-bot (Cloudflare, DataDome) checks: browser fingerprint, TLS/JA3, screen resolution, WebGL, canvas, fonts, timezone, locale, and language headers. All of these must be consistent with the proxy's geolocation. A Swedish IP with a Chinese timezone is a dead giveaway.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Persona Factory                           │
├─────────────────────────────────────────────────────────────┤
│  1. Country selection → GeoIP + locale + timezone          │
│  2. Browser build → User-Agent + platform + WebGL          │
│  3. Hardware profile → screen, fonts, device memory         │
│  4. Contact details → name, email, phone (Faker)           │
│  5. Persist → CloakBrowser profile + credential vault       │
└─────────────────────────────────────────────────────────────┘
```

## Generate a Coherent Persona

```python
from faker import Faker
import random
import json

LOCALE_MAP = {
    "SE": "sv_SE",
    "NO": "nb_NO",
    "DK": "da_DK",
    "FI": "fi_FI",
    "DE": "de_DE",
    "FR": "fr_FR",
    "IT": "it_IT",
    "ES": "es_ES",
    "NL": "nl_NL",
    "PL": "pl_PL",
    "UK": "en_GB",
    "US": "en_US",
}

GEO_MAP = {
    "SE": {"lat": 59.3293, "lon": 18.0686, "tz": "Europe/Stockholm"},
    "NO": {"lat": 59.9139, "lon": 10.7522, "tz": "Europe/Oslo"},
    "DK": {"lat": 55.6761, "lon": 12.5683, "tz": "Europe/Copenhagen"},
    "FI": {"lat": 60.1699, "lon": 24.9384, "tz": "Europe/Helsinki"},
    "DE": {"lat": 52.5200, "lon": 13.4050, "tz": "Europe/Berlin"},
    "FR": {"lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
    "IT": {"lat": 41.9028, "lon": 12.4964, "tz": "Europe/Rome"},
    "ES": {"lat": 40.4168, "lon": -3.7038, "tz": "Europe/Madrid"},
    "NL": {"lat": 52.3676, "lon": 4.9041, "tz": "Europe/Amsterdam"},
    "PL": {"lat": 52.2297, "lon": 21.0122, "tz": "Europe/Warsaw"},
    "UK": {"lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
}

BROWSER_BUILDS = [
    # Chrome on Windows (most common — use this 60% of the time)
    {
        "name": "Chrome-Win10",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "platform": "Win32",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "max_touch_points": 0,
        "hardware_concurrency": 16,
        "device_memory": 8,
    },
    # Chrome on Mac
    {
        "name": "Chrome-Mac",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "platform": "MacIntel",
        "webgl_vendor": "Apple",
        "webgl_renderer": "Apple M1 Pro",
        "max_touch_points": 0,
        "hardware_concurrency": 10,
        "device_memory": 16,
    },
    # Firefox on Windows
    {
        "name": "Firefox-Win10",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "platform": "Win32",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "max_touch_points": 0,
        "hardware_concurrency": 16,
        "device_memory": 8,
    },
    # Edge on Windows
    {
        "name": "Edge-Win10",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "platform": "Win32",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "max_touch_points": 0,
        "hardware_concurrency": 16,
        "device_memory": 8,
    },
]

SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080, "weight": 60},   # Most common
    {"width": 2560, "height": 1440, "weight": 25},
    {"width": 1366, "height": 768, "weight": 10},     # Laptops
    {"width": 3840, "height": 2160, "weight": 5},     # 4K
]

def generate_persona(country: str = "SE") -> dict:
    """Generate a complete, coherent persona for one browser session."""

    locale = LOCALE_MAP.get(country, "en_US")
    geo = GEO_MAP.get(country, GEO_MAP["US"])
    faker = Faker(locale)

    # Browser build (weighted: Chrome 60%, Firefox 25%, Edge 15%)
    build = random.choices(
        BROWSER_BUILDS,
        weights=[0.45, 0.15, 0.25, 0.15],  # Chrome-Win, Chrome-Mac, Firefox, Edge
        k=1
    )[0]

    # Screen resolution (weighted)
    screens = []
    for s in SCREEN_RESOLUTIONS:
        screens.extend([s] * s["weight"])
    screen = random.choice(screens)

    # Faker personal details (matching locale)
    first = faker.first_name()
    last = faker.last_name()

    # Add slight random variation to geo (same city, different location)
    geo_variation = {
        "lat": geo["lat"] + random.uniform(-0.1, 0.1),
        "lon": geo["lon"] + random.uniform(-0.1, 0.1),
        "tz": geo["tz"],
    }

    return {
        # Identity
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}@catchall-domain.com",
        "company": faker.company(),
        "job_title": faker.job(),
        "phone": faker.phone_number(),

        # Browser fingerprint
        "user_agent": build["user_agent"],
        "platform": build["platform"],
        "webgl_vendor": build["webgl_vendor"],
        "webgl_renderer": build["webgl_renderer"],
        "max_touch_points": build["max_touch_points"],
        "hardware_concurrency": build["hardware_concurrency"],
        "device_memory": build["device_memory"],
        "screen": screen,
        "build_name": build["name"],

        # Geo
        "geolocation": geo_variation,
        "locale": locale,
        "timezone": geo["tz"],

        # Session
        "country": country,
        "proxy_tier": "self-hosted",  # Default — escalate if needed
    }

# Generate 200 personas (spread across countries)
def generate_persona_pool(countries: list[str] = None, pool_size: int = 200) -> list[dict]:
    if countries is None:
        countries = ["SE", "NO", "DK", "FI", "DE", "FR", "IT", "ES", "NL", "PL", "UK"]

    pool = []
    for _ in range(pool_size):
        country = random.choice(countries)
        pool.append(generate_persona(country))

    # Save to disk
    with open("persona_pool.json", "w") as f:
        json.dump(pool, f, indent=2)

    return pool
```

## Integration with CloakBrowser

```python
import requests

def create_cloak_profile(persona: dict, proxy_url: str) -> str:
    """Create a persistent CloakBrowser profile matching this persona."""
    resp = requests.post("http://localhost:3000/api/profiles", json={
        "name": f"persona-{persona['country']}-{persona['first_name'].lower()}",
        "os": "windows" if "Win" in persona["platform"] else "mac",
        "browser": "chrome" if "Chrome" in persona["user_agent"] else "firefox",
        "userAgent": persona["user_agent"],
        "screen": f"{persona['screen']['width']}x{persona['screen']['height']}",
        "geolocation": f"{persona['geolocation']['lat']},{persona['geolocation']['lon']}",
        "locale": persona["locale"],
        "timezone": persona["timezone"],
        "webglVendor": persona["webgl_vendor"],
        "webglRenderer": persona["webgl_renderer"],
        "hardwareConcurrency": persona["hardware_concurrency"],
        "deviceMemory": persona["device_memory"],
        "proxy": proxy_url,
    })
    return resp.json()["cdp_endpoint"]
```

## Coherency Rules (DO NOT BREAK)

1. Geo must match: proxy IP geolocation = timezone = locale = WebGL language
2. Browser must match: User-Agent platform = navigator.platform = WebGL vendor
3. Screen must be common: use 1920×1080 or 2560×1440 — never rare combos
4. Don't mix: Swedish proxy + French locale + Mac platform + Win32 WebGL = instant detection
5. Session stickiness: one persona = one CloakBrowser profile = one consistent fingerprint across requests

## Related

- [CloakBrowser](cloakbrowser.md) — uses these personas
- [Stealth Bypass Chain](stealth-bypass-chain.md) — where personas fit in the chain
- [Account Creation](account-creation.md) — uses personas for signup
- [Rota Proxy](rota-proxy.md) — proxy assigned per persona
