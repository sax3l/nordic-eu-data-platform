# Proxy Fabric — Multi-Tier Proxy Architecture

> **Purpose:** The platform's complete proxy strategy across all tiers — from free public proxies to self-hosted residential pools. Defines which proxy tier to use for which site type.

## Proxy Tiers

```
Tier 0: Direct (no proxy)
  │  Use: Open APIs with no anti-bot
  │  Sites: CVR (DK), Companies House (UK), SIRENE (FR), KVK (NL)
  │  Speed: Fastest, 500+ req/min
  │  Cost: $0
  ▼
Tier 1: Free Public Pool (auto-scraped by Rota)
  │  Use: Light anti-bot, bulk low-priority work
  │  Sites: Open registries with soft rate limiting
  │  Speed: 200-500 req/min (filtered for alive proxies)
  │  Reliability: 60-80% alive at any moment
  │  Cost: $0
  ▼
Tier 2: Self-Hosted Datacenter Pool
  │  Use: Medium anti-bot, consistent IP reputation needed
  │  Setup: 5 cheap VPS ($5/mo each) running Squid + HAProxy
  │  Sites: Bolagsverket, Brreg, CVR search, most EU registries
  │  Speed: 100-200 req/min
  │  Cost: $25-50/mo
  ▼
Tier 3: Tor Circuit Pool
  │  Use: Aggressive anti-bot (Cloudflare, DataDome)
  │  Setup: Local Tor daemon with 4-8 parallel circuits
  │  Sites: Handelsregister.de, sites with strict IP blocks
  │  Speed: 10-20 req/min (slow but stealthy)
  │  Cost: $0 (free — uses Tor network)
  ▼
Tier 4: Residential (paid, optional)
  │  Use: When all else fails — genuine residential IPs
  │  Providers: Bright Data, Oxylabs, IPRoyal (none free)
  │  Cost: $5-15/GB
  │  Note: Avoid if possible — use Tor + stealth browser instead
```

## Proxy Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Proxy Decision Engine                     │
├──────────────────────────────────────────────────────────────┤
│  Input: site_config.waf, method_stats.host_block_rate         │
│  Output: proxy_tier to use                                    │
│                                                               │
│  Rules:                                                       │
│  1. waf=none → Tier 0 (direct, no proxy)                     │
│  2. waf=soft → Tier 1 first, escalate to Tier 2 if blocked   │
│  3. waf=cf → Tier 2 first, escalate to Tier 3 if blocked     │
│  4. waf=datadome → Tier 3 (Tor) from the start               │
│  5. stateful_portal → Fixed Tier 2 (sticky session needed)   │
│  6. block_rate > 50% → Escalate proxy tier                   │
└──────────────────────────────────────────────────────────────┘
```

## Self-Hosted Pool Setup

```bash
# On each VPS (Ubuntu 22.04):
sudo apt update && sudo apt install squid apache2-utils

# /etc/squid/squid.conf:
http_port 3128
acl allowed_ips src 192.168.1.0/24  # Your worker IPs only
http_access allow allowed_ips
http_access deny all
# Optional: rotate outgoing IP if VPS has multiple IPs
# tcp_outgoing_address 1.2.3.4
# tcp_outgoing_address 1.2.3.5

sudo systemctl restart squid

# Register in Rota:
curl -X POST http://localhost:5555/api/proxies \
  -H "Content-Type: application/json" \
  -d '{"url": "http://vps-ip:3128", "tag": "self-hosted", "weight": 10}'
```

## Tor Setup (Multiple Circuits)

```bash
sudo apt install tor

# /etc/tor/torrc:
SocksPort 9050
SocksPort 9052
SocksPort 9054
SocksPort 9056
MaxCircuitDirtiness 300  # Rotate circuit every 5 minutes
NewCircuitPeriod 60       # Try new circuits every 60s

sudo systemctl restart tor

# Test each circuit gives a different IP:
curl --socks5 localhost:9050 https://api.ipify.org
curl --socks5 localhost:9052 https://api.ipify.org
# Should show different IPs
```

## Health Monitor

```python
import asyncio
import httpx

async def health_check_proxy(proxy_url: str, test_url: str = "https://httpbin.org/ip") -> bool:
    """Check if a proxy is alive and working."""
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
            resp = await client.get(test_url)
            return resp.status_code == 200
    except:
        return False

async def health_check_pool():
    proxies = await get_all_proxies()
    results = {}
    for proxy in proxies:
        results[proxy["url"]] = await health_check_proxy(proxy["url"])
    alive = sum(1 for v in results.values() if v)
    dead = len(results) - alive
    print(f"Pool health: {alive}/{len(results)} alive, {dead} dead")
    return results
```

## Country-Specific Proxy Requirements

| Country | Registry | Proxy Tier | Reason |
|---|---|---|---|
| SE | Bolagsverket API | Tier 0 (direct) | Open API, no anti-bot |
| SE | Bolagsverket web | Tier 1 (free) | Light rate limiting |
| NO | Brreg API | Tier 0 (direct) | Open API |
| DK | CVR API | Tier 0 (direct) | Open API |
| FI | PRH API | Tier 0 (direct) | Open API |
| UK | Companies House | Tier 0 (direct) | Open API |
| FR | SIRENE API | Tier 0 (direct) | Open API |
| NL | KVK API | Tier 0 (direct) | Open API |
| DE | Handelsregister | Tier 3 (Tor) | CF + aggressive anti-bot |
| IT | Registro Imprese | Tier 3 (Tor) | Stateful portal + CF |
| AT | Firmenbuch | Tier 3 (Tor) | Login-gated |
| ES | Registro Mercantil | Tier 2 (self-hosted) | Moderate anti-bot |
| PL | CEIDG | Tier 1 (free) | Gov portal, light anti-bot |
| PL | KRS | Tier 2 (self-hosted) | Moderate anti-bot |
| CZ | Obchodní rejstřík | Tier 1 (free) | Open web portal |
| HU | e-cégjegyzék | Tier 3 (Tor) | Stateful wizard |
| BE | KBO | Tier 0 (direct) | Open data download |
| IE | CRO | Tier 0 (direct) | Open API |
| CH | ZEFIX | Tier 1 (free) | Open web search |
| IS | RSK | Tier 2 (self-hosted) | Moderate anti-bot |
| PT | RACIUS | Tier 3 (Tor) | Paid per extract |

## Related

- [Rota Proxy Rotation](rota-proxy.md) — the engine managing Tiers 0-1
- [Stealth Bypass Chain](stealth-bypass-chain.md) — when proxy + stealth must work together
- [CloakBrowser](cloakbrowser.md) — uses proxy + GeoIP matching per persona
