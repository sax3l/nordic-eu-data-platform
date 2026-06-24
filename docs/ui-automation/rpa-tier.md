# UI‑Automation / RPA Tier

> **Scope (read with [`../COMPLIANCE.md`](../COMPLIANCE.md)).** This tier exists for **T1 primary official registries that have no API and force a stateful, click‑through UI** — e.g. DE Handelsregister (`de-handelsregister`), IT Registro Imprese (`it-registroimprese`), AT Firmenbuch (`at-firmenbuch`), HU e‑cégjegyzék (`hu-ceginformacio`). These are public, official, lawful sources we are *entitled* to read; the only obstacle is that they're built for a human with a mouse, not a machine with an API.
>
> **It is explicitly NOT for competitor ICP tools.** Apollo / ZoomInfo / Cognism / Lusha / Seamless are **T5 — benchmark only**. Pointing a robot at a competitor's logged‑in database to OCR‑exfiltrate their contacts is a ToS breach, an access‑control circumvention, and it launders *their* errors and consent problems into our "honest" product. The RPA tier's source allowlist is hard‑coded to `tier: T1_primary_official` (+ a small set of T3 official directories) and **rejects any T5 host at config‑load time** (see [§9](#9-compliance-guardrails-enforced-in-code)).

---

## 1. Where this sits in the platform

The RPA tier is **one backend behind the adaptive router** (architecture pillar 1) and is modelled exactly like the other licensed/seat‑limited tools (pillar 4, `licensed-tools.md`): a **resource pool with a hard concurrency ceiling = number of robot seats you own**. The router does not "know" how to click Handelsregister; it knows there is a backend `rpa` that can service `source.access == ui_automation`, that it has `N` seats, a measured success‑rate and latency per host, and a cost per run. It schedules against that like any other arm.

```
                       ┌──────────────────────────────────────────────┐
                       │              ADAPTIVE ROUTER                  │
                       │  (multi‑armed bandit per host: success,       │
                       │   latency, cost, block‑rate → pick backend)   │
                       └──────────────────────────────────────────────┘
        chooses cheapest viable backend per (source, target) ↓↓↓
   ┌──────────┬──────────────┬───────────────┬──────────────────────────────┐
   │ http     │ curl_cffi /  │ headless      │ RPA TIER (this doc)           │
   │ (api,    │ botasaurus   │ browser       │ seat‑limited pool, access==   │
   │  bulk)   │ (WAF bypass) │ (playwright)  │ ui_automation                 │
   └──────────┴──────────────┴───────────────┴──────────────────────────────┘
                                                   │ adapter interface (§5)
                          ┌────────────────────────┼─────────────────────────┐
                          │            │           │            │             │
                       UiPath      Ranorex     Playwright   Browser‑Use   Skyvern
                     (Orchestr.   (object    (code‑first,   (OSS LLM    (OSS vision
                      + unattended  recog.,    self‑healing   browser     agent, self‑
                      robots +      CLI runs)  via §6)        agent)      healing)
                      queues)
```

**Escalation order the router walks** (cheapest → most expensive), per pillar‑3 combination matrix:

| Rank | Backend | Marginal cost | When the router picks it |
|---|---|---|---|
| 0 | `http` (api/bulk/open_data) | ~free | Source has an API or bulk file. **Always preferred** — RPA is last resort. |
| 1 | `curl_cffi` / Botasaurus | cents | Static HTML behind a JA3/Cloudflare wall, no JS state machine. |
| 2 | `playwright` (headless, scripted) | low | SPA / JS rendering, **stateless** flow, selectors stable. |
| 3 | **RPA — Playwright‑in‑pool** | low‑med | Stateful multi‑step flow (login → search → paginate → open doc) but DOM is automatable. *Default RPA engine.* |
| 4 | **RPA — Browser‑Use / Skyvern** | med (LLM tokens) | Layout changed / selectors broke / never‑seen form → AI agent figures out the next action from vision+DOM. *Self‑healing engine.* |
| 5 | **RPA — UiPath / Ranorex (seat)** | high (per‑seat licence) | Enterprise registry needs Citrix/desktop‑app/Java‑applet handling, signed audit trail, or an attended fallback. *Scarce seats — only when 0–4 can't.* |

The router demotes a backend automatically when its measured `block_rate`/`error_rate` for a host rises (failure classifier → auto‑remediation), and promotes the AI‑agent engine when scripted selectors start failing — that's the self‑healing loop in [§6](#6-ai-driven-self-healing-selectors).

---

## 2. When UI‑automation beats HTTP (and when it doesn't)

UI‑automation is **slow and expensive** (a full browser, a stateful session, sometimes a paid seat). Use it only when HTTP genuinely can't get the datum. Decision rule:

**Use RPA when ANY of these hold:**

- **No API and no bulk file**, and the data is gated behind a *sequence* of stateful pages (search form → result list → entity page → document tab), where each step depends on server‑side session/CSRF/`__VIEWSTATE` you'd have to reverse‑engineer per release.
- The flow needs a **real login/session** (gov credential or paid account) whose token lives in cookies + hidden form fields + anti‑CSRF nonces that rotate per page.
- The page is a **server‑rendered postback app** (classic ASP.NET WebForms `__doPostBack`, JSF/PrimeFaces, Java applet, Citrix/published app) where there is no clean JSON endpoint to call.
- A **CAPTCHA / interaction challenge** only fires inside a genuine browser session and the source's ToS *permits* manual solving (official registries usually do for legitimate per‑document access).
- The artefact is a **rendered PDF/print view** reachable only by clicking through (then OCR/NER downstream).

**Prefer HTTP (don't use RPA) when:**

- An API, bulk export, or open‑data file exists (Handelsregister now offers an **XML/SI bulk export** for annual filings — use that for backfill; reserve RPA for *targeted, fresh, single‑entity* lookups the bulk doesn't cover).
- The "stateful" page actually fronts a discoverable JSON/XHR endpoint — capture it once and replay with `curl_cffi`. Always run the **XHR‑sniff probe before committing to RPA**.
- You only need a field already covered by a T2 aggregator we're licensed for (North Data/Atoka often cheaper at scale than per‑document registry fees).

**Cost economics (order‑of‑magnitude, per successful record):**

| Path | Throughput / worker | Marginal $/record | Notes |
|---|---|---|---|
| HTTP api/bulk | 100s–1000s/s | ~$0.000 | Always win if available. |
| curl_cffi / Botasaurus | 5–20/s | ~$0.001 | + proxy GB. |
| Playwright headless | 0.3–1/s | ~$0.01 | Browser RAM/CPU dominated. |
| **RPA Playwright‑pool** | 0.1–0.5/s/seat | $0.02–0.10 | + registry per‑doc fee where charged. |
| **RPA AI‑agent (Browser‑Use/Skyvern)** | 0.05–0.2/s/seat | $0.05–0.30 | + LLM tokens (vision). Cheaper than a broken scraper you re‑write weekly. |
| **RPA UiPath/Ranorex seat** | 0.05–0.2/s/seat | $0.10–0.40 amortised | Seat licence ($/yr) ÷ runs. Only where it's the *only* thing that works. |

The economic argument for the AI‑agent engine is **maintenance amortisation**: a brittle CSS‑selector scraper for a registry that re‑skins twice a year costs an engineer a day each break; a self‑healing vision agent absorbs the re‑skin for the price of a few thousand vision tokens. Below ~50k records/yr from a churny registry, the AI agent is *cheaper total‑cost‑of‑ownership* than hand‑maintained selectors even though its per‑record cost is higher.

---

## 3. Engine roles — what each tool actually does for us

| Engine | Role in the tier | Strengths | We use it for |
|---|---|---|---|
| **Playwright** | The **default RPA driver** and the substrate the AI agents drive. | Free, fast(ish), cross‑browser, great state/cookie/network control, `tracing` + `codegen`, video on failure. | 80% of flows: scripted, stateful, stable‑DOM registries. Also the executor Skyvern/Browser‑Use emit actions into. |
| **Browser‑Use** (OSS) | **Self‑healing agent**, code‑first. An LLM reads the **accessibility tree + screenshot**, decides the next action, and drives Playwright. | Cheap to run on local DOM, pinnable, scriptable in Python, deterministic‑ish with a task plan. | Recovering a flow when selectors break; one‑off "find the filing PDF on this page" steps. |
| **Skyvern** (OSS) | **Vision‑first self‑healing agent.** Computer‑vision + LLM over a screenshot to locate and act on elements without selectors. | Survives heavy re‑skins, handles canvas/odd widgets, form‑filling from a schema. | The hardest, most layout‑volatile registries; CAPTCHA‑adjacent flows where DOM is obfuscated. |
| **UiPath** | **Enterprise orchestration backbone** when we need it: **Orchestrator** (central control), **unattended robots** (run headless on VMs, no human), **Queues** (transactional work items with retry/SLA/dead‑letter). | Audit trail, scheduling, Citrix/Java/desktop‑app recorders, mature retries, on‑prem gov‑credential vaulting. | Registries needing a published‑app/Citrix surface, or a customer who demands an auditable, supported RPA stack. Modelled as a **seat pool** (§4). |
| **Ranorex** | **Object‑recognition driver + CLI runs.** RanoreXPath + a UI object repository; runs headless via `Ranorex.exe`/`*.runconfig` from CI. | Strong on desktop/hybrid apps and flaky web objects; stable object IDs survive minor DOM shuffles; clean CLI for our orchestrator to shell out to. | Hybrid desktop+web registry clients; where its object repository out‑survives raw selectors. Also a **seat pool**. |

> UiPath and Ranorex are *commercial, seat‑metered*. They are **rank‑5** — the platform reaches for free Playwright/AI‑agents first and only spends a seat when nothing cheaper clears the flow.

---

## 4. Seat‑limited resource pools (the licence is the bottleneck)

Every RPA engine is exposed to the router as a **pool with a hard concurrency cap = seats owned**. This is the same abstraction as Screaming Frog / Sequentum in `licensed-tools.md`. The router can request a *lease*; if no seat is free it either queues or falls back to the next cheapest backend.

```python
# src/ui_automation/pools.py
from dataclasses import dataclass, field
import asyncio, time

@dataclass
class SeatPool:
    name: str                       # "uipath" | "ranorex" | "playwright" | "skyvern" | "browser_use"
    seats: int                      # licensed concurrency (Playwright/OSS: effectively cores/RAM bound)
    licence_cost_year: float = 0.0  # 0 for OSS — feeds $/record amortisation
    _sem: asyncio.Semaphore = field(init=False)
    _in_use: int = field(default=0, init=False)
    _runs: int = field(default=0, init=False)   # lifetime runs → amortise licence

    def __post_init__(self):
        self._sem = asyncio.Semaphore(self.seats)

    async def acquire(self, timeout_s: float = 0.0):
        """Return a lease or None (router then falls back to a cheaper backend)."""
        try:
            if timeout_s:
                await asyncio.wait_for(self._sem.acquire(), timeout_s)
            else:
                if self._sem.locked() and self._in_use >= self.seats:
                    return None
                await self._sem.acquire()
        except asyncio.TimeoutError:
            return None
        self._in_use += 1; self._runs += 1
        return _Lease(self)

    def amortised_seat_cost(self) -> float:
        return 0.0 if not self._runs else self.licence_cost_year / self._runs

class _Lease:
    def __init__(self, pool): self.pool = pool; self.t0 = time.time()
    async def __aenter__(self): return self
    async def __aexit__(self, *exc):
        self.pool._in_use -= 1; self.pool._sem.release()

# Registered with the router at boot:
POOLS = {
    "playwright":  SeatPool("playwright",  seats=24, licence_cost_year=0),       # RAM/CPU bound
    "browser_use": SeatPool("browser_use", seats=12, licence_cost_year=0),       # + LLM tokens
    "skyvern":     SeatPool("skyvern",     seats=8,  licence_cost_year=0),
    "ranorex":     SeatPool("ranorex",     seats=2,  licence_cost_year=3_600),   # 2 runtime seats
    "uipath":      SeatPool("uipath",      seats=4,  licence_cost_year=8_400),   # 4 unattended robots
}
```

**Parallelism within seat limits.** Throughput inside the tier = `Σ seats` across pools, *not* unlimited. Two levers keep us inside the licence while maximising flow:

1. **Per‑host AIMD concurrency** (pillar 1) caps how many seats may hit *one* registry at once — registries rate‑limit and lock accounts, so e.g. Handelsregister might be capped at 2 concurrent sessions even if 24 Playwright seats are free. The router's per‑host limiter owns this; seats free up for *other* hosts.
2. **UiPath Queues / our Redis work‑queue** decouple *enqueue* from *execute*. We can enqueue 50k Handelsregister lookups; robots drain them at `min(seats_free, host_concurrency_cap)`. Transactional queue items give retry, SLA, and dead‑letter for free (UiPath natively; we mirror it in Redis for the OSS engines).

---

## 5. The adapter interface

Every engine implements one interface so the router treats them identically. A flow is declared **once** as a JSON/YAML *flow spec* (steps + selectors + a recovery hint); the adapter executes it on its engine, and on selector failure hands off to the self‑healing layer ([§6](#6-ai-driven-self-healing-selectors)).

```python
# src/ui_automation/adapter.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

class Outcome(str, Enum):
    OK = "ok"
    BLOCKED = "blocked"          # WAF/CAPTCHA/lockout → router demotes host
    AUTH_FAILED = "auth_failed"  # session/credential problem
    SELECTOR_MISS = "selector_miss"   # DOM changed → trigger self‑heal
    RATE_LIMITED = "rate_limited"
    EMPTY = "empty"              # flow ran, target not found
    ERROR = "error"

@dataclass
class RpaRequest:
    source_id: str               # MUST resolve to a tier-T1 source (compliance gate)
    flow: str                    # flow-spec id under flows/<source_id>/<flow>.yaml
    inputs: dict[str, Any]       # e.g. {"orgnr": "HRB 12345", "court": "Berlin"}
    tier: str                    # carried from sources.yaml; gate rejects T5
    deadline_s: float = 120.0

@dataclass
class FieldVal:
    value: Any
    # GDPR-by-design provenance, stamped on EVERY field (COMPLIANCE §4):
    source_id: str
    source_url: str
    lawful_basis: str            # e.g. "official_register_public_record"
    captured_at: str             # ISO-8601 UTC
    engine: str                  # which adapter produced it
    confidence: float            # selector match / agent certainty

@dataclass
class RpaResult:
    outcome: Outcome
    fields: dict[str, FieldVal]
    artifacts: list[str]         # paths to downloaded PDFs/screenshots for OCR/NER
    latency_s: float
    engine: str
    cost: float                  # tokens + amortised seat + per-doc fee
    trace: str | None            # Playwright trace / video for debugging
    healed: bool = False         # True if self-heal rewrote a selector this run

class RpaAdapter(Protocol):
    name: str                                  # "playwright" | "uipath" | ...
    def supports(self, req: RpaRequest) -> bool: ...
    async def run(self, req: RpaRequest, lease) -> RpaResult: ...
    # introspection for the router's bandit:
    def health(self) -> dict[str, float]: ...  # {success_rate, p50_latency, seats_free}
```

Concrete adapters: `PlaywrightAdapter`, `BrowserUseAdapter`, `SkyvernAdapter`, `UiPathAdapter` (calls Orchestrator REST: add queue item → poll → fetch output), `RanorexAdapter` (shells `Ranorex.exe <test>.exe /rc:<run.runconfig> /param:...` and parses the JUnit/XML report). The router calls `acquire()` on the engine's pool, then `adapter.run(req, lease)`, records the `RpaResult` into the per‑host bandit, and emits fields to the fusion layer with their provenance intact.

**Flow spec** (declarative, engine‑agnostic, version‑controlled — this is what self‑healing repairs):

```yaml
# flows/de-handelsregister/normal_search.yaml
id: normal_search
source_id: de-handelsregister
tier: T1_primary_official
steps:
  - goto:   "https://www.handelsregister.de/rp_web/welcome.xhtml"
  - click:  { role: link, name: "Advanced search", css: "#naviForm\\:erweiterteSuche" }
  - fill:   { label: "Company or keywords", css: "#form\\:schlagwoerter", value: "{{ company }}" }
  - select: { label: "Register type", css: "#form\\:registerArt", value: "HRB" }
  - fill:   { label: "Register number", css: "#form\\:registerNummer", value: "{{ reg_no }}" }
  - click:  { role: button, name: "Find", css: "#form\\:btnSuche" }
  - expect: { css: ".ergebnisListe tr", min: 1, on_miss: self_heal }   # ← recovery hint
  - click:  { role: link, name: "{{ company }}", in: ".ergebnisListe" }
  - extract:
      company_name: { css: ".firmaName",  lawful_basis: official_register_public_record }
      court:        { css: ".registergericht" }
      reg_number:   { css: ".registerNummer" }
      status:       { css: ".status" }
  - download: { role: link, name: "AD (current printout)", as: artifact }  # → OCR/NER
```

The same spec runs unchanged on Playwright (selector path) or on Skyvern/Browser‑Use (which read the `role`/`name`/`label` semantic hints and the screenshot instead of the CSS, so an AI agent can complete it even when `css` rots — see [the a11y‑friendly design skill]).

---

## 6. AI‑driven self‑healing selectors (vision + DOM)

Layout changes are the #1 cause of RPA breakage. The tier never breaks hard on a missing selector — it **escalates within the same run**:

1. **Try the declared selector** (`css` then `role`/`name`/`label` — semantic locators are far more durable than CSS).
2. **On `SELECTOR_MISS`**, the orchestrator switches engine *for that step only* to the self‑healing layer with a tight task: *"On this page, the step `click Find button` failed. Here is the screenshot + accessibility tree. Locate the element that submits the company search and return a stable locator + perform the click."*
   - **Browser‑Use** answers from the **DOM/a11y tree** (cheap, token‑light) first.
   - **Skyvern** answers from the **screenshot (vision)** when the DOM is obfuscated/canvas.
3. **Persist the heal.** The agent's resolved locator is written back into the flow spec as a *candidate* (`healed_css`, `healed_at`, `confidence`), the run sets `healed=True`, and a low‑priority review task is opened. Next run tries the healed locator first → the flow "learns" the new layout without an engineer.
4. **Telemetry → router.** A spike in `healed` rate for a host signals a re‑skin; the router temporarily *promotes the AI‑agent engine to rank‑3* for that host (skip the dead selectors) until the healed spec stabilises, then demotes back to cheap scripted Playwright.

This is the failure‑classifier → auto‑remediation loop from pillar 1, specialised to UI breakage. Vision is the **fallback**, not the default: DOM/a11y healing is ~10× cheaper, so we only pay for pixels when the DOM lies.

---

## 7. Login / session / form handling

- **Credential vault.** Gov credentials and paid‑account logins live in a secrets vault (UiPath Orchestrator Assets / Azure Key Vault), **never in the flow spec**. The adapter receives a credential *handle*, resolves it at runtime, and scrubs it from traces/logs.
- **Session reuse (sticky).** A successful login produces a `storage_state` (cookies + localStorage). The adapter persists it per `(source_id, account)` and **reuses it across runs** until it 401s — re‑login is expensive and lock‑out‑risky, so we amortise one login over many lookups. This mirrors the platform's sticky‑session/identity‑rotation pattern: one coherent identity (UA+viewport+proxy+session) per registry account, rotated as a unit.
- **CSRF / `__VIEWSTATE` / nonces.** Because we drive a *real browser*, hidden anti‑CSRF fields and ASP.NET `__VIEWSTATE`/`__EVENTVALIDATION` are filled and posted by the page itself — we never reconstruct them. This is the core reason RPA beats HTTP for postback registries.
- **Forms.** Declarative `fill`/`select`/`upload` steps; the self‑heal layer maps a *form schema* → fields by label when positions move. Multi‑step wizards are just sequential steps with `expect` gates between them.
- **CAPTCHA / challenges.** Only where the source's ToS permits manual solving for legitimate access: route to an **attended** UiPath robot or a human‑in‑the‑loop queue. We never bulk‑solve, never defeat an auth challenge the ToS forbids, and **never** do any of this against a T5 host (it's blocked upstream anyway).
- **Lock‑out safety.** Per‑host AIMD caps concurrent sessions per account; on `AUTH_FAILED`/`RATE_LIMITED` the circuit breaker opens for that host (backoff 5min→1h, per the adaptive‑backoff table) so we never hammer a paid account into suspension.

---

## 8. Parallelism & throughput within the licence

```
effective_tier_throughput =
    Σ_engines  min( seats_free(engine),
                    Σ_hosts host_concurrency_cap(host) )      # work-queue drained
    with each host gated by its own AIMD limiter + circuit breaker
```

- **Enqueue ≫ execute.** 50k targets enter a Redis (or UiPath) queue; robots drain at the per‑host safe rate. Burst is absorbed by the queue, not by the registry.
- **Hedging within the tier is disabled by default** for paid/login flows (firing two sessions doubles lock‑out risk and per‑doc cost). Source‑racing happens *one level up*: the router races the cheap T2‑aggregator HTTP path against the RPA path and cancels the slow one — so RPA only actually runs when the cheap path lost.
- **Batch windows.** Low‑priority backfill RPA runs in off‑peak windows where registries are faster and per‑seat contention is lowest.

---

## 9. Compliance guardrails (enforced in code)

These are not advisory — they are checked at config‑load and per‑request:

1. **Allowlist by tier.** The RPA backend registers handlers **only** for sources whose `sources.yaml` entry has `access: ui_automation` **and** `tier: T1_primary_official` (plus an explicit short list of official T3 directories). Any request whose `source_id` resolves to `tier: T5_benchmark` raises `ForbiddenTierError` before a browser ever launches. **Competitor ICP tools can never be targeted by this tier.**
2. **No competitor exfiltration.** There is no flow spec, and the loader refuses to create one, for Apollo/ZoomInfo/Cognism/Lusha/Seamless or any T5 host — by name‑denylist *and* by the tier gate above.
3. **Respect technical signals.** robots.txt, `429`/`Retry‑After`, and account‑lockout signals feed the same AIMD limiter + circuit breaker as every other backend. The tier slows down on these; it never brute‑forces.
4. **GDPR provenance on every field.** Each `FieldVal` carries `source_id`, `source_url`, `lawful_basis`, `captured_at`, `engine` → straight into the fusion layer's per‑field provenance and the right‑to‑erasure index.
5. **Auditable runs.** Every run keeps a Playwright trace / UiPath job log so we can prove *what* we accessed, *when*, and *under what credential* — the EU‑moat audit trail.

---

## 10. Worked example — DE Handelsregister (`de-handelsregister`)

**Goal:** for a company we already track, fetch the *current* register entry (court, HRB number, status, legal form, registered seat) and the **AD current printout** PDF, for fields the bulk SI export doesn't refresh between filings. Official, public, T1 — exactly what this tier is for.

**Why RPA here:** handelsregister.de is a JSF/PrimeFaces postback app behind a search wizard; the result and document tabs depend on server‑side session + `javax.faces.ViewState`. There's a bulk SI export for backfill (use it!), but *targeted fresh single‑entity* lookups have no API → RPA.

**Flow (router's eye view):**

1. Router gets a fetch task for `de-handelsregister`, field `register_status` for `{company: "Beispiel GmbH", reg_no: "HRB 12345", court: "Berlin"}`.
2. It first **races** the cheap path: is this covered by our licensed North Data (T2) pull? If North Data returns fresh + agrees, cancel RPA — done for ~$0.01.
3. North Data is stale → router escalates to **rank‑3 RPA Playwright**. Compliance gate: `tier == T1_primary_official` ✔. It `acquire()`s a seat from `POOLS["playwright"]`; per‑host AIMD says Handelsregister cap = 2, one free → lease granted.
4. `PlaywrightAdapter.run` loads `flows/de-handelsregister/normal_search.yaml`, reuses `storage_state` (no login needed for normal search), executes steps, fills the JSF form, lets the page carry `ViewState`, opens the result, **extracts** the four fields and **downloads** the AD printout to `artifacts/`.
5. **Self‑heal branch:** if Handelsregister re‑skinned and `#form\:btnSuche` is gone (`SELECTOR_MISS` on the `Find` step), the orchestrator hands that step to **Browser‑Use** with the screenshot + a11y tree: *"locate and click the search‑submit control."* It finds the renamed button, completes the step, writes `healed_css` back into the spec, sets `healed=True`. The run still succeeds; an engineer reviews the heal later.
6. Adapter returns `RpaResult(OK, fields={...with provenance...}, artifacts=[AD.pdf], engine="playwright", healed=?)`.
7. The PDF goes to the **OCR/NER pipeline**; structured fields go to **fusion** with `lawful_basis="official_register_public_record"`, `captured_at`, `source_url`. Multi‑source agreement scoring reconciles them against North Data.
8. Router records success + latency + cost into the per‑host bandit; the seat is released back to the pool.

**Cost for this record:** ~$0.04 (browser seat amortised + storage), or ~$0.12 if the self‑heal vision step fired — versus an engineer‑day every time the wizard changes, which is the whole point.

---

## 11. Build order

1. `RpaAdapter` + `SeatPool` + `PlaywrightAdapter` (the 80% engine) + flow‑spec loader **with the tier/denylist gate**.
2. Wire the pool into the adaptive router as a rank‑3/4 backend; per‑host AIMD + circuit breaker.
3. Self‑heal layer: `BrowserUseAdapter` (DOM) then `SkyvernAdapter` (vision); heal‑write‑back + review queue.
4. `de-handelsregister`, `it-registroimprese`, `at-firmenbuch`, `hu-ceginformacio` flow specs.
5. `UiPathAdapter` (Orchestrator queues) + `RanorexAdapter` (CLI) for the seat‑metered enterprise cases.
6. Provenance/erasure plumbing + audit‑trace retention.

> See also: [`../COMPLIANCE.md`](../COMPLIANCE.md) (the hard lines), `docs/architecture/adaptive-engine.md` (the router/bandit/AIMD this plugs into), `docs/architecture/licensed-tools.md` (seat‑pool model shared with Screaming Frog/Sequentum), and the `ai-friendly-web-design` notes on semantic/`role`/`label` locators that make flows self‑heal.
