# Sequentum Enterprise — Visual Web Scraping + RPA

> **Tool:** Sequentum Enterprise v2.82 | **License:** Paid ($199-$400/mo) | **Simon has this licensed**
> **Key Feature:** Visual element matching — record workflows by clicking, not writing selectors

Visual web scraping platform with built-in Cloudflare bypass, JavaScript rendering, and visual workflow recording. The platform's primary escalation for complex, stateful portals that resist programmatic scraping.

## What it solves

Some registries and company sites have:
- Dynamic element IDs that change every page load
- Complex multi-step navigation (login → search → results → detail)
- Anti-bot that targets headless browsers specifically
- Visual-only content (charts, images, non-standard layouts)

Sequentum handles all four: you record a workflow once by clicking through the site, and it replays the clicks with visual element matching (finds buttons by appearance, not by ID). Built-in CF bypass handles the anti-bot layer.

## Key Features

1. **Visual Element Matching** — Finds elements by how they look, not by CSS selectors. Survives DOM structure changes.
2. **Built-in CF Bypass** — Handles Cloudflare challenges automatically
3. **Record + Replay** — Record a workflow once, replay 100,000 times
4. **Data Export** — CSV, JSON, SQL Server, direct API push
5. **Agent Management** — Multiple agents, scheduled runs, error alerts
6. **JavaScript Rendering** — Full browser engine for SPAs

## When It's Needed (vs OSS Alternatives)

| Situation | OSS Approach | Why Sequentum Wins |
|---|---|---|
| German Handelsregister (CF + stateful) | Browser-Use agent | Sequentum has native CF bypass + visual matching |
| Italian CCIAA (complex multi-step) | Playwright script | Visual matching survives DOM changes; scripts break |
| Polish CEIDG (gov portal, anti-bot) | CloakBrowser + script | Record-once-replay-forever vs per-site coding |
| Hungarian e-cégjegyzék (stateful wizard) | Browser-Use | Wizards with 10+ steps are brittle for agents |
| Any registry with 2FA | Cannot automate | Sequentum can pause for manual 2FA, then resume |

## Orchestrator Integration

```python
import requests
import json
import time

SEQUENTUM_API = "http://localhost:8081/api"  # Your Sequentum Enterprise instance

def sequentum_run_agent(agent_name: str, inputs: dict) -> list[dict]:
    """Trigger a Sequentum agent, wait for completion, return results."""

    # 1. Start agent
    resp = requests.post(f"{SEQUENTUM_API}/agents/run", json={
        "agentName": agent_name,
        "inputs": inputs,  # e.g., {"orgNumber": "559000-0001", "country": "SE"}
    })
    run_id = resp.json()["runId"]

    # 2. Poll for completion
    while True:
        status = requests.get(f"{SEQUENTUM_API}/runs/{run_id}/status").json()
        if status["status"] == "completed":
            break
        if status["status"] in ("failed", "error"):
            raise Exception(f"Sequentum run failed: {status.get('error')}")
        time.sleep(5)

    # 3. Fetch results
    results = requests.get(f"{SEQUENTUM_API}/runs/{run_id}/data").json()
    return results["rows"]

# Example: Extract German company data
data = sequentum_run_agent("handelsregister-de-extract", {
    "companyName": "Mercedes-Benz AG",
    "court": "Stuttgart",
})
# Returns: [{name, hr_number, address, directors: [...]}]
```

## Workflow Recording Pipeline

```
1. Open Sequentum Enterprise
2. Click "Record New Agent"
3. Navigate: handelsregister.de → Search → Enter company name → Submit
4. Click through: Results list → Company detail → Extract fields
5. Save agent as "handelsregister-de-extract"
6. Test replay: does it work with a different company name?
7. Deploy: wire into orchestrator via API above
```

## Agent Library (Pre-Built for Platform)

| Agent Name | Target | Steps | Notes |
|---|---|---|---|
| `bolagsverket-se-extract` | Bolagsverket.se | Search → Detail → Officers | Simple, little anti-bot |
| `brreg-no-extract` | Brreg.no | Search → Detail → Roles | Open API exists, use API instead |
| `handelsregister-de-extract` | Handelsregister.de | Search → Captcha → Detail → Extract | **Primary use case** — CF + stateful |
| `cciaa-it-extract` | Registro Imprese (IT) | Login → Search → Visura → Extract | Login + complex form |
| `firmenbuch-at-extract` | Firmenbuch (AT) | Login → Search → Detail → Extract | Stateful portal |
| `ceidg-pl-extract` | CEIDG (PL) | Search → Results → Detail → Extract | Gov portal with anti-bot |
| `kbo-be-extract` | KBO (BE) | Search → Detail → Extract | Open data download exists, skip agent |
| `e-cegjegyzek-hu-extract` | e-cégjegyzék (HU) | Login → Search → Multi-step wizard | **Primary use case** — wizard-based |

## License Seat Management

Sequentum seats are limited. The orchestrator treats them as a resource pool:

```python
class SequentumPool:
    def __init__(self, max_seats: int = 1):
        self.semaphore = asyncio.Semaphore(max_seats)

    async def run_agent(self, agent_name: str, inputs: dict) -> list[dict]:
        async with self.semaphore:  # Queue if all seats busy
            return await sequentum_run_agent(agent_name, inputs)

# Orchestrator auto-escalates to Sequentum only when faster methods fail
# Treats seats as the most expensive resource — used last
sequentum = SequentumPool(max_seats=1)  # 1 seat = 1 concurrent agent
```

## Cost per Extraction

| Cost Item | Amount |
|---|---|
| License (monthly) | $199-400 |
| Infrastructure | $0 (runs on existing hardware) |
| Time per extraction | 30-90 seconds (depends on site complexity) |
| Cost per 1000 extractions | ~$5-10 (license amortized) |

## Related

- [Screaming Frog](screaming-frog.md) — the Tier 1 bulk crawler (use first)
- [UiPath](uipath.md) — the enterprise RPA alternative
- [Ranorex](ranorex.md) — desktop automation alternative
- [Browser-Use](browser-use.md) — the OSS AI-agent alternative
- [Stealth Bypass Chain](stealth-bypass-chain.md)
