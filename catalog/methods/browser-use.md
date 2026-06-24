# Browser-Use + AI Agents — AI-Driven Web Automation

> **Browser-Use:** https://github.com/browser-use/browser-use | **Stars:** ~83K | **Language:** Python
> **Skyvern:** https://github.com/Skyvern-AI/skyvern | **Stars:** ~15K
> **Stagehand:** https://github.com/browserbase/stagehand | **Stars:** ~8K | **Language:** TypeScript
> **LaVague:** https://github.com/lavague-ai/LaVague | **Stars:** ~5K | **Language:** Python

AI agents that control real browsers via natural language commands. They navigate, click, fill forms, scroll, extract data — with self-healing selectors that adapt when the DOM changes. The platform's UI-automation tier for portals with no API (German Handelsregister, Italian Registro Imprese, Austrian Firmenbuch, Hungarian e-cégjegyzék).

## Browser-Use — Primary (Best-in-Class)

Uses Playwright + your local LLM (Ollama/LM Studio) to drive a real browser. You say "go to handelsregister.de, search for company X, extract all officers" — it does it, handling multi-step flows, pagination, and anti-bot challenges. 81% success rate against Cloudflare in benchmarks.

```bash
pip install browser-use
playwright install chromium
```

### Minimal Extraction Example

```python
from browser_use import Agent
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:14b", base_url="http://localhost:11434")

agent = Agent(
    task=(
        "Go to https://www.handelsregister.de. Search for company 'Mercedes-Benz AG'. "
        "Extract: legal name, registration court, register number, registered address, "
        "and all current managing directors with their titles. "
        "Return as JSON."
    ),
    llm=llm,
    use_vision=True,        # Screenshots → vision model for UI understanding
    headless=False,          # German registries often block headless
    stealth_mode=True,       # Anti-detection patches
)
result = await agent.run()
print(result.extracted_content())
```

### Multi-Step Flow (Login → Search → Extract → Paginate)

```python
agent = Agent(
    task=(
        "1. Navigate to https://portal.example-registry.se/login"
        "2. Login with credentials from env vars LOGIN_EMAIL and LOGIN_PASSWORD"
        "3. Search for org number 559000-0001"
        "4. Extract all board members, their birth years, and roles"
        "5. Click through to subsidiary listings if present"
        "6. Return complete JSON with all extracted fields"
    ),
    llm=llm,
    use_vision=True,
    save_conversation_path="logs/session_{timestamp}.json",
    max_actions_per_step=3,   # Limit actions per LLM call for stability
    max_failures=5,           # Retry on failure before giving up
)
result = await agent.run()
```

### Self-Healing Selectors

```python
agent = Agent(
    task="Extract company directors from the table on the page",
    llm=llm,
    # Browser-Use auto-detects when a selector fails and retries with alternatives
    # No need to write brittle CSS selectors — the LLM finds elements by context
    planner_llm=llm,  # Separate LLM for planning (optional, improves accuracy)
)
```

## Skyvern — Best for Form-Heavy Workflows

Skyvern specializes in form navigation and data entry with high reliability.

```bash
docker run -d -p 8080:8080 skyvernai/skyvern
```

### Key Capability: Form Filling

Skyvern's advantage over Browser-Use: it maps pages to a layout tree, identifies form fields by label/semantic meaning (not just DOM position), and fills them correctly even when form structures differ between sites. Use for:
- Registry search forms (Handelsregister, CCIAA)
- Account creation flows
- Multi-page data entry

## Stagehand — TypeScript, Playwright-Native, Production-Grade

```bash
npm install @browserbasehq/stagehand playwright
```

```typescript
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod"; // schema for extraction

const stagehand = new Stagehand({ env: "LOCAL", headless: false });
await stagehand.init();

await stagehand.page.goto("https://example-registry.com/search");

// Stagehand uses Zod schemas to define extraction targets
const result = await stagehand.page.extract({
  instruction: "extract all companies from the search results table",
  schema: z.object({
    companies: z.array(z.object({
      name: z.string(),
      registration_number: z.string(),
      status: z.string(),
    }))
  })
});
```

## LaVague — Simplified, Natural Language

```bash
pip install lavague
```

Simplest API of the four. Best for one-off exploration, not production pipelines.

## The Agent Orchestration Pattern

```
┌──────────────────────────────────────────────────┐
│              Orchestrator (Crawlee)               │
├──────────────────────────────────────────────────┤
│  For each target:                                │
│    1. Try HTTP tier (curl_cffi / direct API)     │
│    2. If blocked → try CF tier (FlareSolverr)    │
│    3. If blocked → try Stealth Browser (Cloak)   │
│    4. If stateful portal → Browser-Use Agent     │
│       - Login (from credential vault)            │
│       - Navigate search form                     │
│       - Extract structured data                  │
│       - Handle pagination                        │
│    5. If all else fails → Sequentum/UiPath RPA   │
└──────────────────────────────────────────────────┘
```

## Which Agent When

| Situation | Tool | Reason |
|---|---|---|
| German Handelsregister (CF + stateful) | Browser-Use + CloakBrowser | 81% CF bypass + multi-step form nav |
| Italian CCIAA (form-heavy, no CF) | Skyvern | Better form handling |
| Companies House (open API) | None needed | Direct JSON API, skip agent entirely |
| Austrian Firmenbuch (stateful portal) | Browser-Use | Login + search + extract pattern |
| Hungarian e-cégjegyzék | Stagehand (TS) | Better TS+Crawlee integration |
| Belgian KBO (open bulk) | None | Open data download |
| Any JSON/XML API | None | curl_cffi, cheapest tier |

## Local LLM for Agent Control

All four tools work with local models. Browser-Use + Qwen2.5-14B is the proven combination. Phi-4-14B is also strong for structured output. Llama-3.1-8B works but may hallucinate more on complex multi-step flows.

## Speed

- Browser-Use agent: 30-60s per full extraction (multiple page interactions)
- Skyvern form flow: 20-40s per form completion
- Stagehand: 20-30s per extraction
- Cost: $0.00 (local LLM) vs $0.05-0.15 per run (Claude API)

## Related

- [CloakBrowser](cloakbrowser.md) — the stealth browser layer under the agent
- [LM Studio + Ollama](lmstudio-ollama.md) — the local LLM brain
- [Account Creation Pipeline](account-creation.md) — agent-driven signup
- [Stealth Bypass Chain](stealth-bypass-chain.md)
- [Sequentum RPA](sequentum.md) — the licensed fallback when OSS agents fail
