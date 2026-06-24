# Rota — Proxy Rotation Engine + Proxy Pool Management

> **Repo:** https://github.com/Rota-Framework/Rota (check GitHub) | **Language:** Python | **License:** MIT

Self-hosted proxy rotation engine with dashboard, health monitoring, user-pools, and request routing. Manages the platform's proxy fabric — free lists, self-hosted proxies, Tor circuits, and optional residential pools — with automatic failover and latency-weighted selection.

## What it solves

Raw proxy lists are always partially dead. Without rotation, your IP gets rate-limited or banned. Without health monitoring, you send requests into dead endpoints and waste time. Rota gives you:
- Auto-scraping of free proxy lists
- Health checks (latency + success rate)
- Weighted rotation (favor fast proxies)
- Cooldown on rate-limit detection
- Per-site proxy pools (keep residential IPs for the CF sites, datacenter for the easy ones)

## Install

```bash
git clone https://github.com/Rota-Framework/Rota
cd Rota
docker compose up -d
# Dashboard at http://localhost:5555
```

## Architecture (Self-Hosted Pool)

```
┌─────────────────────────────────────────────────────┐
│                    Rota Engine                       │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Free List│  │ Self-    │  │  Tor Circuits     │  │
│  │ Scraper  │  │ Hosted   │  │  (socks5:9050..)  │  │
│  │ (auto)   │  │ (manual) │  │                   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘  │
│       │              │                │              │
│       └──────────────┼────────────────┘              │
│                      ▼                               │
│            ┌─────────────────┐                       │
│            │  Health Monitor │  ← latency + success  │
│            └────────┬────────┘     per proxy+target  │
│                     ▼                                │
│            ┌─────────────────┐                       │
│            │ Pool Router     │  ← site→pool mapping  │
│            └────────┬────────┘                       │
│                     ▼                                │
│            ┌─────────────────┐                       │
│            │  Weighted Pick  │  ← latency-weighted   │
│            └────────┬────────┘                       │
│                     ▼                                │
│  ┌─────────────────────────────────────┐             │
│  │  HTTP API → proxy://rotator:8080    │             │
│  └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘
```

## Free Proxy Sources (auto-scraped)

Rota's free-list scraper harvests from:
- **Proxyscrape** — HTTP/SOCKS5, thousands deep, updated every 5 min
- **Free-proxy-list.net** — HTTPS-proxies, hourly refresh
- **Geonode** — 300+ proxies with country filtering
- **Spys.one** — detailed proxy metadata
- **OpenProxy.space** — hourly updated list

Reality check: ~60-80% of free proxies are dead at any moment. Rota health-checks and only routes through alive ones. Still, free pools are for bulk, non-sensitive work (open registries). WAF-protected sites need the self-hosted/Tor tier.

## Self-Hosted Proxy Tier

```bash
# Set up 5 cheap VPS instances as proxy nodes
# Each runs Squid + HAProxy:
sudo apt install squid haproxy
# Configure Squid to listen on :3128
# Configure HAProxy to rotate between Squid instances
# Register in Rota:
curl -X POST http://localhost:5555/api/proxies \
  -d '{"url": "http://vps1:3128", "tag": "self-hosted", "weight": 10}'
# × 5 VPS = 10-20 simultaneous connections per proxy
```

## Tor Integration (Free Residential-Like IPs)

```bash
# Install Tor, configure for multiple circuits
sudo apt install tor
# /etc/tor/torrc — add:
# SocksPort 9050
# SocksPort 9052
# SocksPort 9054
# ... (one per instance, each = different exit node)
# Register Tor circuits in Rota:
curl -X POST http://localhost:5555/api/proxies \
  -d '{"url": "socks5://127.0.0.1:9050", "tag": "tor", "weight": 2}'
```

Tor gives genuinely different IPs from residential ranges. Slower (~2-5s per request) but nearly impossible to block en masse. Use for critical WAF-bypass, not bulk.

## Crawlee Integration

```python
from crawlee.proxy_configuration import ProxyConfiguration

proxy_config = ProxyConfiguration(
    proxy_options=[{"url": "http://localhost:5555/api/proxy?pool=rotating"}]
)
crawler = PlaywrightCrawler(proxy_configuration=proxy_config, ...)
```

## Per-Site Pool Strategy

| Site Type | Pool | Reason |
|---|---|---|
| Open registries (Companies House, CVR) | Free list | No anti-bot, bulk OK |
| Soft anti-bot (Bolagsverket, Brreg) | Self-hosted | IP reputation matters |
| CF-protected (Handelsregister.de) | Tor + CloakBrowser | Need residential-like + stealth |
| DataDome (some .fr sites) | Self-hosted + CloakBrowser | Custom UA + proxy consistency |

## Speed

- Free pool latency: 0.5-3s average
- Self-hosted: 0.1-0.3s (same DC as workers)
- Tor: 2-5s (slow, but stealthy)
- Dashboard monitoring: real-time, <50ms overhead

## Related

- [Stealth Bypass Chain](stealth-bypass-chain.md) — when to use which proxy tier
- [FlareSolverr](flaresolverr.md) — already includes proxy support
- [CloakBrowser](cloakbrowser.md) — proxy + GeoIP matching
- [Fake Identity Stack](fake-identity-stack.md)
