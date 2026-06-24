# Browser-AI brains catalog

> Open-source / free AI agents and perception tools evaluated as the "brains" for the adaptive
> harvesting layer of the Nordic-EU data platform. Stars and recency confirmed via web search
> June 2026 — treat figures as approximate, they move.

## Scope & compliance reminder

Per `docs/COMPLIANCE.md`, these tools are deployed against **primary official sources with no API**
(DE Handelsregister, IT Registro Imprese, court/registry portals behind anti-bot JS) and the open web
within robots.txt + rate limits. They are **not** to be pointed at competitor ICP tools (Apollo,
ZoomInfo, Cognism…) for bulk extraction behind their login — Tier 5 is benchmark/feature-intel only.
The adaptive limiter must respect `429`/`Retry-After` regardless of which brain is driving.

## Where these fit in our architecture

The platform has three layers that these tools plug into:

- **Adaptive router** — decides, per source/task, *which tier of automation* to use. Cheapest viable
  tier first: (1) HTTP + parser, (2) deterministic Playwright script, (3) **AI-driven browser agent**
  (this catalog), escalating only when the DOM is stubborn / changed / anti-bot. The router needs the
  agent layer to expose a uniform "run task → structured result + trace + cost" contract and to emit a
  reusable script on success (so next run drops back to tier 2).
- **Worker pool** — horizontally scaled, sandboxed browser workers. Needs a browser-infra layer
  (sessions, proxies, CAPTCHAs, fingerprint) decoupled from the reasoning layer so we can swap brains.
- **Local cheap inference** — a self-hosted VLM/LLM (Qwen2-VL / Llama-class on our own GPU) used for
  the high-volume grunt perception so we are not paying per-token to a frontier API for every page.

The matrix below maps each tool to one of: **orchestrator** (decides multi-step plans), **UI-driver**
(turns intent into clicks/types on stubborn UI), **perception** (turns pixels→structured elements),
**infra** (browser sandbox/sessions), **extraction** (page→structured records), **benchmark/eval**
(measure agent quality — not run in prod).

---

## 1. Browser-Use — **must-adopt (primary orchestrator/UI-driver)**

- **Repo:** https://github.com/browser-use/browser-use — ~78k stars
- **License:** MIT
- **What it does:** The de-facto leading OSS browser-agent framework. An `Agent` takes a natural-
  language objective + a pluggable LLM (OpenAI/Anthropic/**Ollama/local**), reads the DOM/accessibility
  tree (with optional screenshots), and drives Playwright to completion. Self-healing harness, emits
  action traces.
- **Fit:** Primary **orchestrator + UI-driver** for tier-3 escalations in the router. When a
  deterministic script breaks on a registry portal, the router hands the objective + last-known
  selectors to Browser-Use; on success we capture its action trace and regenerate a tier-2 script.
- **Hardware/cost:** Free framework. Cost = whatever LLM you wire in. Runs fine against a local Ollama
  model for cheap bulk; frontier API only for hard pages. No GPU needed for the framework itself.
- **Maturity:** Very high — largest community, fast releases, Rust beta agent, production users.
- **Integration note:** Pip install, `Agent(task=…, llm=…, browser=…)`. Point its Playwright at a
  **Steel/Browserbase CDP endpoint** to run inside our worker pool. Wrap one call per worker; the
  router supplies `task` + budget, gets back `result + trace + screenshots`.

## 2. Skyvern — **must-adopt (vision fallback for stubborn UI)**

- **Repo:** https://github.com/Skyvern-AI/skyvern — ~21.9k stars
- **License:** AGPL-3.0 ⚠️ (copyleft — fine for internal/SaaS backend use; keep it as an isolated
  service, do not statically link into proprietary distributed code).
- **What it does:** Vision-LLM browser automation. Screenshots the page, a VLM locates the target
  element visually and acts — so it works on sites it has never seen, no selector maintenance. Bring-
  your-own LLM (OpenAI/Anthropic/Gemini/**Ollama**), Playwright-compatible SDK + no-code workflow
  builder, form-filling specialist.
- **Fit:** **UI-driver of last resort** in the router. When Browser-Use's DOM approach fails (canvas-
  rendered tables, obfuscated DOM, heavy anti-bot like some EU court portals), the router escalates to
  Skyvern's pure-vision path. Its form-filling robustness is valuable for registry search forms.
- **Hardware/cost:** Free. VLM cost dominates; pair with local OmniParser + local VLM to cut it.
- **Maturity:** High — YC-backed, funded, active, 2k+ forks of community mirrors.
- **Integration note:** Run as its own containerized service (AGPL isolation) exposing an HTTP task
  API; the router calls it only on the vision-fallback branch. Feed it the same Steel session.

## 3. Stagehand (Browserbase) — **must-adopt (deterministic+AI hybrid for extraction)**

- **Repo:** https://github.com/browserbase/stagehand — ~22.5k stars
- **License:** MIT
- **What it does:** SDK that mixes **deterministic Playwright** with three AI primitives —
  `act` / `extract` / `observe` — plus an autonomous `agent`. Auto-caching + self-healing: replays
  cached actions with **no LLM call** until the page changes, then re-invokes AI. `extract` returns
  schema-validated structured data (Zod). Multi-provider via Vercel AI SDK.
- **Fit:** Best tool for the **extraction** stage *and* for the router's tier-2↔tier-3 boundary. Its
  caching model **is** our "drop back to deterministic" pattern, built in: run AI once to learn a
  registry's layout, then it executes cached/cheap until layout drift triggers re-learning. `extract`
  with a Zod schema gives the worker pool clean records (orgnr, officers, addresses) for the fusion
  layer.
- **Hardware/cost:** Free SDK; LLM cost minimized by caching. Pairs with Browserbase cloud (paid) but
  runs equally on local Playwright + Steel.
- **Maturity:** Very high — MIT, 700k+ weekly downloads, multi-language SDKs.
- **Integration note:** TypeScript-first (Python SDK exists). Define one Zod schema per source type;
  the router stores the per-source action cache so re-runs are near-free. Strongest "structured
  extraction with provenance" story of the batch.

## 4. Steel (steel-browser) — **must-adopt (browser infra for the worker pool)**

- **Repo:** https://github.com/steel-dev/steel-browser — ~1.8k stars (org claims 6.5k across repos)
- **License:** Apache-2.0
- **What it does:** Open-source, self-hostable **browser-as-a-service** sandbox. Puppeteer/CDP control
  of Chrome with session management (cookies/localStorage persistence), built-in **proxy rotation**,
  custom extensions, and page→markdown/readability/screenshot/PDF endpoints. Connect via Puppeteer,
  Playwright, or Selenium.
- **Fit:** This is the **infra layer of the worker pool** — not a brain. It gives every brain above a
  consistent, isolated, proxy-rotated, fingerprint-managed Chrome over CDP. Lets us scale workers and
  swap reasoning frameworks without touching browser plumbing. Its page→markdown endpoint is a cheap
  tier-1.5 for simple sources before any agent runs.
- **Hardware/cost:** Free + self-hosted (we run it; only cost is compute/proxies). Avoids per-session
  Browserbase fees at scale.
- **Maturity:** Medium-high — public beta, active, well-documented Python/Node SDKs.
- **Integration note:** Deploy as the pool's browser backend; Browser-Use / Skyvern / Stagehand all
  attach to its CDP endpoint. Centralize compliance here: robots/rate-limit/`Retry-After` enforcement
  and proxy/geo selection live at this layer so every brain inherits them.

## 5. Microsoft OmniParser — **must-adopt (local perception engine)**

- **Repo:** https://github.com/microsoft/OmniParser — ~24k stars
- **License:** MIT (icon-caption model weights have their own terms — check before redistribution)
- **What it does:** Pure-vision screen parser. Turns a screenshot into structured, **labelled
  interactable elements** (bounding boxes + functional captions + interactable/not flag). v2 hits SOTA
  on ScreenSpot-Pro. Model-agnostic — feeds any VLM/LLM grounded coordinates.
- **Fit:** Our **local cheap-inference perception engine**. Instead of paying a frontier VLM to "find
  the search box" on every page, OmniParser runs on our own GPU and hands grounded elements to a small
  local LLM (or to Skyvern/Browser-Use) for the decision. Slashes per-page vision cost across the
  high-volume worker pool — exactly the "local cheap inference" slot.
- **Hardware/cost:** Free. Needs a **GPU** (works on a single mid-range card; v2 is light enough for
  one worker-class GPU). One-time model download.
- **Maturity:** High — Microsoft Research, active, v2 + OmniTool released.
- **Integration note:** Stand up as an internal "parse-screenshot→elements" microservice. The worker
  takes a Steel screenshot → OmniParser → grounded elements → local VLM picks the action → Steel
  executes. This is the cost-control backbone; wire it under Skyvern's and Browser-Use's vision path.

## 6. Playwright-MCP — **adopt (clean tool surface for our agents)**

- **Repo:** https://github.com/microsoft/playwright-mcp — ~33.5k stars
- **License:** Apache-2.0
- **What it does:** Official Microsoft MCP server exposing Playwright as MCP tools. Drives the browser
  via the **accessibility tree** (structured, no vision model needed) — navigate/click/type/snapshot,
  plus a code-exec escape hatch. Works with any MCP client.
- **Fit:** The **uniform tool interface** between our orchestration agents and the browser. Rather than
  each brain bolting onto Playwright directly, our own router-agent (Claude/local LLM) calls
  Playwright-MCP tools — accessibility-tree-first means cheap, deterministic, no per-page VLM. Ideal
  tier-2.5: structured DOM driving before we escalate to pixel-vision.
- **Hardware/cost:** Free, no GPU, no vision model. `npx @playwright/mcp@latest`.
- **Maturity:** Very high — Microsoft-maintained, huge adoption, fast release cadence.
- **Integration note:** Run as a sidecar per worker; point it at Steel's CDP. Use it as the *default*
  agent tool surface; only fall to OmniParser+VLM when the accessibility tree is empty/obfuscated.

## 7. Notte — **pilot (cost-optimized hybrid agent)**

- **Repo:** https://github.com/nottelabs/notte — ~1.8k stars
- **License:** Server-side public licence — check terms (some components SSPL-style); treat as
  "evaluate before prod."
- **What it does:** Full-stack web-agent framework optimized for **speed/cost/reliability**. Lets you
  script deterministic parts and invoke AI only when needed (claims ~50% cost cut, ~47s/task, high
  reliability on its own benchmark). Playwright-compatible; single-API deploy of serverless web
  automations.
- **Fit:** Direct competitor to Browser-Use/Stagehand for the **orchestrator + extraction** slot, with
  an explicit cost-minimization design that mirrors our router philosophy. Pilot it head-to-head
  against Browser-Use on a stubborn source to see which wins on €/successful-extraction.
- **Hardware/cost:** Free framework; LLM cost minimized by design.
- **Maturity:** Medium — newer, smaller community, vendor-backed, active releases. Lower bus-factor.
- **Integration note:** Slot in behind the same task contract as Browser-Use so the router can A/B
  them. Verify licence before any redistribution; safe to run as an internal service.

## 8. LaVague — **watch (declining, useful patterns)**

- **Repo:** https://github.com/lavague-ai/LaVague — ~6.4k stars
- **License:** Apache-2.0
- **What it does:** "Large Action Model" framework: a **World Model** turns an objective + current page
  into instructions, an **Action Engine** compiles them to Selenium/Playwright code and runs them.
  Default GPT-4o, fully swappable.
- **Fit:** Conceptually maps onto our router (World Model = planner, Action Engine = code-gen → tier-2
  script). The *pattern* — generate reusable action code — is exactly what we want the router to do.
- **Hardware/cost:** Free; LLM cost only.
- **Maturity:** Low/declining — development has stalled relative to Browser-Use; community momentum has
  moved on. Don't build core on it.
- **Integration note:** Mine for design ideas (objective→code compilation) rather than adopt; if we
  want code-gen of reusable scripts, Stagehand's caching achieves it with more momentum.

## 9. Agent-E (Emergence AI) — **watch (architecture reference)**

- **Repo:** https://github.com/EmergenceAI/Agent-E — ~1.2k stars
- **License:** MIT
- **What it does:** Multi-agent web automation on the AG2 (AutoGen) framework. Decomposes tasks into
  atomic "skills" each returning a natural-language outcome; FastAPI wrapper for HTTP/streaming. Strong
  research pedigree (WebVoyager-topping results at release).
- **Fit:** Reference for a **hierarchical orchestrator** (planner + skill executors) if our router
  grows multi-agent. Its skill-returns-NL-outcome pattern is a clean worker contract.
- **Hardware/cost:** Free; LLM cost only.
- **Maturity:** Low/medium — small community, the vendor pushes its hosted Web Automation API over the
  OSS repo. Slower cadence.
- **Integration note:** Don't adopt wholesale; borrow the atomic-skill decomposition for our worker
  task contract. Emergence's hosted API is Tier-5-adjacent (third-party) — not for our core path.

## 10. WebVoyager — **adopt as eval, not runtime**

- **Repo:** https://github.com/MinorJerry/WebVoyager — research repo (paper ACL 2024, arXiv 2401.13919)
- **License:** check repo (research/permissive).
- **What it does:** Reference end-to-end multimodal web agent **and** a benchmark of 643 tasks over 15
  real sites, with a GPT-4V auto-evaluator (~85% human agreement). Reports ~55% success.
- **Fit:** **Benchmark/eval harness**, not a production brain. Use its task set + auto-evaluator to
  score Browser-Use vs Notte vs Skyvern on *our* hardware, and to regression-test the router after
  changes. The auto-eval pattern is reusable to grade our own runs.
- **Hardware/cost:** Free; eval LLM cost only.
- **Maturity:** Established as a benchmark; agent code is reference-grade, not maintained as a product.
- **Integration note:** Wire into CI as a quality gate for the agent layer. Do not run its tasks
  against live competitor/registry sites in prod — it is a measurement tool.

## 11. WebArena-style agents — **adopt as eval/sandbox, not runtime**

- **Repo:** https://github.com/web-arena-x/webarena (+ VisualWebArena
  https://github.com/web-arena-x/visualwebarena) — research repos
- **License:** check repo (research/permissive).
- **What it does:** Self-hosted, reproducible web environment (shopping, forum, GitLab, CMS, maps) with
  812 long-horizon tasks. Brutal difficulty — best GPT-4 agent ~10% success — so it's a stress test,
  not a soft benchmark. VisualWebArena adds multimodal tasks.
- **Fit:** **Offline sandbox + eval** for hardening our agents on long-horizon, multi-step flows
  (mirrors multi-page registry navigation) **without touching real sites** — perfect for compliance:
  we can hammer the router against self-hosted apps to tune retries/limiters before pointing at a real
  registry.
- **Hardware/cost:** Free; needs containers to self-host the apps. No GPU for the env itself.
- **Maturity:** Established research benchmark, widely cited.
- **Integration note:** Stand up the dockerized environment as a pre-prod gym for the worker pool;
  measure success/cost/robustness and tune the adaptive limiter against it.

---

## Adopt / pilot / watch summary

| Tool | Slot | Verdict |
|---|---|---|
| Browser-Use | orchestrator + UI-driver | **must-adopt** |
| Skyvern | vision UI-driver (fallback) | **must-adopt** (AGPL → isolate) |
| Stagehand | extraction + det/AI hybrid | **must-adopt** |
| Steel | browser infra / worker pool | **must-adopt** |
| OmniParser | local perception (cost control) | **must-adopt** |
| Playwright-MCP | uniform agent tool surface | **adopt** |
| Notte | cost-optimized agent | **pilot** (check licence) |
| LaVague | code-gen pattern | **watch** (declining) |
| Agent-E | multi-agent reference | **watch** |
| WebVoyager | eval harness | **adopt as eval** |
| WebArena | offline gym / eval | **adopt as eval** |

## Reference router/worker wiring

```
                        ┌─────────────── ADAPTIVE ROUTER ───────────────┐
  task + source ──▶     │ tier1 HTTP+parser → tier2 Playwright script    │
                        │ → tier2.5 Playwright-MCP (a11y tree)           │
                        │ → tier3 Browser-Use (DOM agent)                │
                        │ → tier3.5 Skyvern (pure vision)                │
                        │ extraction: Stagehand.extract(zod)             │
                        └───────────────────┬────────────────────────────┘
                                            │ all attach over CDP
                        ┌───────────────────▼───────────── WORKER POOL ──┐
                        │ Steel (sessions, proxy rotation, robots/rate)  │
                        │   └─ screenshots ─▶ OmniParser ─▶ local VLM    │  ← local cheap inference
                        └────────────────────────────────────────────────┘
   eval/CI: WebVoyager + WebArena gyms grade the whole stack offline.
```

On success at any AI tier, capture the action trace and regenerate a tier-2 script so the next run of
that source drops back to the cheapest deterministic path (Stagehand's cache does this natively).

---

_Sources: project GitHub repos (browser-use, Skyvern-AI/skyvern, browserbase/stagehand,
steel-dev/steel-browser, microsoft/OmniParser, microsoft/playwright-mcp, nottelabs/notte,
lavague-ai/LaVague, EmergenceAI/Agent-E, MinorJerry/WebVoyager, web-arena-x/webarena), confirmed via
web search June 2026. Star counts approximate and moving._
