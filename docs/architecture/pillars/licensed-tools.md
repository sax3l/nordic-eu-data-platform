# Architecture: Orchestrating the Licensed Tools Headlessly, In Parallel

**Part of:** Nordic + EU company / contact / LinkedIn / website / vehicle coverage platform
**Scope of this section:** Screaming Frog SEO Spider, Sequentum (Desktop + Cloud/Enterprise), UiPath Orchestrator, Ranorex — wrapped behind one `ScraperBackend` adapter interface so the adaptive router treats them as *just more methods* with measured cost, speed, and success metrics, and so their per-seat license limits are modeled as a constrained resource pool.

This builds on the OSS catalog (`OPEN_SOURCE_TOOLS_CATALOG.md`), the WAF-bypass repos, the headless-browser catalog, and `architecture_patterns_reference.md` (bulkhead, sticky sessions, adaptive backoff, circuit breakers). The OSS stack (curl_cffi, Botasaurus, Camoufox/Playwright, Scrapling, FlareSolverr) is **Tier 0–2**: cheap, infinitely parallel, free. The licensed tools are **Tier 3–5**: finite seats, higher cost-per-call, but they *win decisively* on three classes of target where OSS routinely fails. The whole point of this section is to make the conductor reach for a licensed seat *only when the marginal coverage/throughput gain justifies consuming that scarce seat* — and to do it automatically.

---

## 1. Why these four, and exactly when each beats the OSS path

| Tool | Headless mechanism | Wins over OSS when... | Loses to OSS when... |
|------|-------------------|----------------------|----------------------|
| **Screaming Frog SEO Spider** | `--headless` CLI, DB storage mode | You must discover + crawl an *entire company website* (hundreds–thousands of URLs) and bulk-extract emails/phones/people via CSS/XPath/Regex in one pass. SF's multi-threaded crawler + custom extraction is faster and more complete than hand-rolled BFS in Scrapy for full-site sweeps. | Single-page fetch, or JS-rendered SPA behind aggressive anti-bot. (SF *can* render with Chromium but it's slower than Camoufox there.) |
| **Sequentum (Desktop + Cloud)** | `RunAgent.exe` CLI / Cloud REST API | The target is a **JS-heavy, anti-bot, paginated table** (registries, directories, search portals) where the OSS stack hits CAPTCHA/CF walls. Sequentum has built-in CAPTCHA + Cloudflare handling, visual agent logic, and stateful pagination that survives session resets. | Static HTML or simple JSON APIs — using a Sequentum seat there is waste. |
| **UiPath Orchestrator** | Orchestrator OData REST API → unattended robots | The target needs **login + multi-step RPA workflow** or a **stateful government-registry UI** (Bolagsverket portal flows, Brønnøysund/PRH stateful sessions, bank-ID-gated portals). UiPath drives the real app deterministically with queues + retries + audit. | Anything stateless/scriptable. UiPath has the highest per-job overhead. |
| **Ranorex** | `Testsuite.exe` / Ranorex Studio CLI, object-recognition (RanoreXPath) | The target is a **stubborn web UI or a desktop application** where DOM selectors are unstable and you need image/UI-object recognition resilient to layout changes — or you must scrape a *native Windows app* (a thick-client registry viewer, a legacy fleet system). | Web pages with stable DOM — Playwright/Sequentum are cheaper. |

The escalation principle: **cheap-API-confirms-scrape** (goal #7). A free Apollo/registry/MX lookup that confirms a fact lets the router *skip* the expensive licensed crawl entirely. Licensed seats are spent only on the residual targets that no cheaper method resolved.

---

## 2. Screaming Frog SEO Spider — headless full-site discovery + bulk extraction

### 2.1 Verified CLI surface

The CLI binary is `ScreamingFrogSEOSpiderCli.exe` (Windows) / `screamingfrogseospider` (Linux/macOS). Headless flags (verified against Screaming Frog's user guide):

- `--headless` — run with no UI (required for unattended/parallel).
- `--crawl <url>` — spider-mode crawl from a seed.
- `--crawl-list <file>` — list mode: crawl exactly the URLs in a file (perfect for "crawl these 5,000 company homepages").
- `--config <file.seospiderconfig>` — apply a saved config (include/exclude rules, custom extraction, speed/threads, JS rendering on/off, user-agent, **custom search/extraction definitions**).
- `--output-folder <path>` — where exports land.
- `--export-tabs "<Tab:Filter>,..."` — export specific tabs, e.g. `"Custom Extraction:All"`, `"Page Titles:Missing"`.
- `--bulk-export "<Section:Export>,..."` — e.g. `"All Inlinks"`, `"Response Codes:Redirection (3xx)"`.
- `--export-format csv|xlsx` (also `gsheet`).
- `--save-crawl` — persist the crawl DB (**requires a paid license**; free edition cannot save).
- `--overwrite` and `--timestamped-output` — output-file hygiene for repeated runs.
- `--use-majestic`, `--google-analytics`, `--google-search-console` — enrichment integrations (we mostly ignore these for contact mining).
- `--create-sitemap` — emit XML sitemap of discovered URLs.
- Storage: `--config` selects DATABASE (default, scalable) vs MEMORY. **Always DATABASE mode** for big crawls — it lets a single instance crawl millions of URLs without OOM.

Exit code: `0` on success, non-zero on failure (license/EULA not accepted, bad config, crawl abort). First-ever run on a machine must accept EULA + enter license + pick storage mode interactively *once* (or seed `~/.ScreamingFrogSEOSpider/` config), after which `--headless` runs unattended.

### 2.2 The contact-mining config (the load-bearing part)

The value of SF here is **Custom Extraction**. We ship a `contacts.seospiderconfig` that defines, via the config's custom-extraction block, CSS/XPath/Regex extractors:

- Regex for emails: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` (excluding `*.png|jpg|svg`).
- Regex for Nordic phone numbers (E.164 + national formats for SE/NO/DK/FI).
- XPath for `mailto:` and `tel:` hrefs: `//a[starts-with(@href,'mailto:')]/@href`.
- XPath/CSS for team/about/contact-page person blocks (name + title).
- Config also restricts to `Include` paths matching `/(om-oss|about|team|kontakt|contact|medarbetare|staff|personal|ledning|management)/i` so we crawl the high-yield pages first and cap crawl depth/URL count for speed.

### 2.3 Example: bulk-crawl 5,000 company sites for contacts

```bash
# One company, full extraction, saved crawl, timestamped CSV output:
ScreamingFrogSEOSpiderCli.exe \
  --crawl https://www.example-bolag.se \
  --headless \
  --config "C:\platform\sf\contacts.seospiderconfig" \
  --output-folder "C:\platform\out\example-bolag" \
  --export-tabs "Custom Extraction:All" \
  --bulk-export "All Inlinks" \
  --save-crawl --overwrite --timestamped-output \
  --export-format csv
echo "exit=$?"
```

### 2.4 Parallelizing many crawls

A single SF instance is already multi-threaded *within* one crawl. To run *many sites at once* we shard the company list and launch **N headless processes**, one per shard, each with its own `--output-folder` (avoid output collisions). N is bounded by RAM (DATABASE mode ~ a few GB per heavy crawl) and license terms. The conductor spawns these as detached processes and reaps exit codes:

```bash
# Shard a 5,000-site list into 8 lanes, 1 SF process per lane:
split -n l/8 sites.txt lane_
for L in lane_*; do
  ScreamingFrogSEOSpiderCli.exe --crawl-list "$PWD/$L" --headless \
    --config contacts.seospiderconfig \
    --output-folder "C:\platform\out\$L" \
    --export-tabs "Custom Extraction:All" \
    --export-format csv --overwrite &
done
wait
```

Output ingestion: each lane drops `custom_extraction_all.csv`. A watcher tails the output folders, normalizes rows (orgnr ← domain map, email, phone, person, source-url), and upserts into the platform's contact table — then the dedup/fuzzy stage (`OPEN_SOURCE_TOOLS_CATALOG.md` §10) collapses duplicates. **Best role confirmed: fast full-site discovery + bulk custom extraction of emails/phones/people across thousands of company sites.**

Scheduling: SF has a built-in scheduler, but in this platform the conductor owns scheduling (cron/queue), invoking the CLI directly so retries, concurrency caps, and metrics flow through the same router as everything else.

---

## 3. Sequentum (Desktop + Cloud) — anti-bot, JS-heavy, paginated tables

### 3.1 Desktop runner: `RunAgent.exe`

```
RunAgent.exe <agentName|C:\path\agent.scg> [-inputParam "value"] [switch ...]
```

Input parameters take a dash prefix; switches do not. Verified switches:

- `no_ui` — suppress UI (headless).
- `view_browser` — show the browser (debug only).
- `log_level High` / `log_html` / `log_to_file ""` / `log_path "C:\Logs"`.
- `run_method Restart|Continue|ContinueRefreshAgent|ContinueAndRetryErrors|ContinueAndRetryErrorsRefreshAgent` — **self-healing built in**: `ContinueAndRetryErrors` resumes a partially-failed run and re-attempts only the error rows.
- `session_id`, `session_timeout <min>`, `env_ Prod|QA|Dev`.
- `agent_import_folder` / `agent_import_name` — import a packaged `.scg` agent onto a fresh runner (how we deploy agents to a runner pool).

**Exit codes are the gold here** (they drive the router's success/retry logic):

```
0  Success            5  Export Failed        8  Already Running     20 Paused/Stopped
1  Failed             6  License Restriction  9  Invalid Data        21 Agent Paused
2  Incomplete         7  Completed Unsucc.    12 Unknown Exception   22 ACC Error
3  Completed w/errors                         13 Invalid Parameter   23 Mismatching Run ID
4  Incomplete w/errors
```

Router mapping: `0` → success; `3/4` → partial (re-enqueue residual via `run_method ContinueAndRetryErrors`); `5` → export sink problem (retry export, don't re-crawl); `6/8/22` → **license/seat contention** (back off, re-queue to a free seat — do *not* count as a target failure); `9/13` → bad agent/params (alert, never retry blindly).

### 3.2 Headless desktop example, with parallel agents

```bash
# One paginated registry agent, headless, retry errors, custom output path:
RunAgent.exe "BrregOfficers" -seedFile "C:\in\no_orgs.csv" \
  no_ui log_level High run_method ContinueAndRetryErrors env_ Prod
echo "exit=$?"

# Parallel: launch independent agents in separate processes (Windows):
Start "lane1" RunAgent.exe AllabolagOfficers no_ui env_ Prod
Start "lane2" RunAgent.exe PrhFinland       no_ui env_ Prod
Start "lane3" RunAgent.exe BrregNorway       no_ui env_ Prod
```

Export: Sequentum agents own their output config (CSV/JSON/DB/S3 export commands inside the agent). The conductor points the agent's export at a known sink (a watched folder or a Postgres/Fabric writer) and reads results from there; exit code `5` specifically flags export-stage failure separate from crawl failure.

### 3.3 Sequentum Cloud API (managed, elastic parallelism)

For burst capacity beyond the desktop seats, Sequentum Cloud runs the *same agents* serverlessly. Base `https://dashboard.sequentum.com`, header `Authorization: ApiKey <KEY>`:

```http
GET  /api/v1/agent/all                                  # inventory
POST /api/v1/agent/{agentId}/start                      # body: {inputParameters, parallelism, timeout, isRunSynchronously}
GET  /api/v1/agent/{agentId}/runs                       # run history (newest first)
GET  /api/v1/agent/{agentId}/run/{runId}/files          # list output files
GET  /api/v1/agent/{agentId}/run/{runId}/file/{fileId}/download
POST /api/v1/agent/{agentId}/run/{runId}/stop
```

The `parallelism` field is the cloud-side concurrency knob; `isRunSynchronously` lets a quick agent block until done, while long crawls poll `/runs` for state. **Best role confirmed: complex JS-heavy/anti-bot sites + paginated tables the OSS stack struggles with** — desktop seats for steady volume, Cloud for spikes.

---

## 4. UiPath Orchestrator — login/RPA portals + stateful government registries

UiPath is driven entirely through the **Orchestrator OData REST API**; robots are unattended and idempotent via **queues**.

### 4.1 Auth + folder header

OAuth2 bearer token (External Application client-credentials for unattended automation). Every call carries `Authorization: Bearer <token>` and the folder scope header `X-UIPATH-OrganizationUnitId: <folderId>`.

### 4.2 Pattern: enqueue work, start robots, pull results

**(a) Add a queue item** (one company / one registry lookup = one item):

```http
POST {orchUrl}/odata/Queues/UiPathODataSvc.AddQueueItem
Authorization: Bearer {token}
X-UIPATH-OrganizationUnitId: {folderId}
Content-Type: application/json

{ "itemData": {
    "Name": "RegistryLookups",
    "Priority": "Normal",
    "Reference": "SE-5560000000",
    "SpecificContent": { "orgnr": "5560000000", "country": "SE", "portal": "bolagsverket" }
}}
```

**(b) Start unattended jobs** to drain the queue (verified `StartJobs` body):

```http
POST {orchUrl}/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs
Authorization: Bearer {token}
X-UIPATH-OrganizationUnitId: {folderId}

{ "startInfo": {
    "ReleaseKey": "795cbab2-8008-4a54-b1cb-f9ff1ece139e",
    "Strategy": "ModernJobsCount",
    "JobsCount": 6,
    "InputArguments": "{\"queue\":\"RegistryLookups\"}"
}}
```

`Strategy` options: `Specific` (named `RobotIds`), `JobsCount`/`ModernJobsCount` (Orchestrator allocates N robots from the pool), `All`. `JobsCount` is the **parallel-robot fan-out**. `InputArguments` is escaped JSON, max 10,000 chars.

**(c) Harvest results** — the robot writes to **Queue Item Output** (`Output` JSON on each transaction) or to a shared sink. The conductor polls completed queue items:

```http
GET {orchUrl}/odata/QueueItems?$filter=QueueDefinitionId eq {id} and Status eq 'Successful'&$expand=...
```

API triggers can also auto-start a process when items arrive, so the conductor just enqueues and reads back. **Best role confirmed: portals needing login/RPA workflows + government registries with stateful UI** (Bolagsverket interactive flows, BankID-gated portals, anything OSS can't drive deterministically). Robots are the scarcest, most expensive seats — used last.

---

## 5. Ranorex — resilient scraping of stubborn UIs and desktop apps

Ranorex compiles a test suite to a standalone `<Suite>.exe` (or runs via `Ranorex.exe`/Studio CLI). Object recognition (RanoreXPath) is resilient to DOM churn and works on **native Windows apps**, which is why it's the last-resort backend for UIs where even Sequentum's selectors break.

Verified arguments (compiled-suite exe):

- `/ts:<file.rxtst>` — test suite. `/tc:<name|GUID>` — single test container. `/rc:<config>` — run config.
- `/rf:<file.rxlog>` — report file; `/zr` — zip report; `/zrf:<file.rxzlog>` — zipped report path.
- `/rl:<None|Debug|Info|Warn|Error|Success|Failure|int>` — report level (Debug=10 … Failure=120).
- `/vr:<Off|KeepFailedTests|KeepAllTests>` — video on failure.
- `/pa:"Name=Value"` — set a (global) parameter; repeatable. This is how we pass the *target list / search term* into the scraping "test."
- Exit code: **`0` = success, `-1` (non-zero) = failure** — clean for the router.

```bash
# Drive a stubborn portal / thick-client, parameterized by org list, headless-ish:
ScrapeSuite.exe /ts:ScrapeSuite.rxtst /rc:Unattended \
  /pa:"InputCsv=C:\in\targets.csv" /pa:"OutDir=C:\out\ranorex" \
  /rl:Warn /zr /zrf:"C:\out\ranorex\run.rxzlog"
echo "exit=$?"
```

Parallelism is **per-machine/agent** (UI automation owns the desktop session). Scale-out = multiple Ranorex agent machines/VMs, each one seat; a "scraping test" loops over its assigned shard and writes a CSV the watcher ingests. **Best role confirmed: object-recognition scraping of desktop apps + stubborn web UIs** where selector-based tools fail.

---

## 6. The unified `ScraperBackend` adapter interface

Every backend — OSS *and* licensed — implements one interface. The adaptive router then sees a uniform list of methods, each carrying live cost/speed/success metrics, and a `acquire()`/`release()` contract against a constrained seat pool.

```python
from dataclasses import dataclass, field
from enum import IntEnum
import asyncio, time

class Tier(IntEnum):           # escalation order (cheap → expensive)
    HTTP_IMPERSONATE = 0       # curl_cffi / curl-impersonate
    STEALTH_BROWSER  = 1       # Botasaurus / Camoufox / Scrapling
    FLARE_SOLVER     = 2       # FlareSolverr / browser farm
    SCREAMING_FROG   = 3       # licensed: full-site bulk extraction
    SEQUENTUM        = 4       # licensed: anti-bot / paginated tables
    UIPATH           = 5       # licensed: login/RPA + gov registries
    RANOREX          = 5       # licensed: native app / stubborn UI

@dataclass
class FetchResult:
    ok: bool
    rows: list = field(default_factory=list)
    raw_path: str | None = None
    exit_code: int | None = None
    block_signal: str | None = None     # 'captcha' | 'cf' | '403' | 'login' | None
    cost_units: float = 0.0
    latency_s: float = 0.0

class SeatPool:
    """License seats modeled as a constrained, awaitable resource pool."""
    def __init__(self, seats: int):
        self._sem = asyncio.Semaphore(seats)
        self.total = seats
    async def acquire(self): await self._sem.acquire()
    def release(self):       self._sem.release()
    @property
    def free(self): return self._sem._value      # for the scheduler's bin-packing

class ScraperBackend:
    tier: Tier
    name: str
    seats: SeatPool | None = None                 # None => unlimited (OSS)

    # static priors; updated online from the metrics store per (backend, domain)
    base_cost: float = 1.0                         # $ / credits per task
    base_latency_s: float = 5.0
    base_success: float = 0.5

    def can_handle(self, target) -> bool: ...      # capability gate
    async def fetch(self, target) -> FetchResult: ...  # do the work
```

### 6.1 Two licensed adapters (illustrative)

```python
class ScreamingFrogBackend(ScraperBackend):
    tier, name = Tier.SCREAMING_FROG, "screaming_frog"
    base_cost, base_latency_s, base_success = 4.0, 90.0, 0.82
    def __init__(self): self.seats = SeatPool(seats=4)   # 4 concurrent crawls

    def can_handle(self, t):                              # full-site jobs only
        return t.kind == "company_site" and t.want in ("emails","phones","people")

    async def fetch(self, t) -> FetchResult:
        await self.seats.acquire()
        t0 = time.time()
        try:
            out = f"C:/platform/out/{t.id}"
            proc = await asyncio.create_subprocess_exec(
                "ScreamingFrogSEOSpiderCli.exe", "--crawl", t.url, "--headless",
                "--config", "contacts.seospiderconfig", "--output-folder", out,
                "--export-tabs", "Custom Extraction:All",
                "--export-format", "csv", "--overwrite")
            code = await proc.wait()
            rows = parse_sf_csv(out) if code == 0 else []
            return FetchResult(ok=(code == 0), rows=rows, raw_path=out,
                               exit_code=code, cost_units=self.base_cost,
                               latency_s=time.time()-t0)
        finally:
            self.seats.release()

class SequentumBackend(ScraperBackend):
    tier, name = Tier.SEQUENTUM, "sequentum"
    base_cost, base_latency_s, base_success = 6.0, 120.0, 0.88
    def __init__(self): self.seats = SeatPool(seats=2)   # 2 desktop seats; Cloud spills over

    def can_handle(self, t):
        return t.block_class in ("captcha","cf","paginated_table","js_heavy")

    async def fetch(self, t) -> FetchResult:
        await self.seats.acquire()
        t0 = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                "RunAgent.exe", t.agent, "-seedFile", t.seed,
                "no_ui", "run_method", "ContinueAndRetryErrors", "env_", "Prod")
            code = await proc.wait()
            ok = code in (0, 3)                            # 3 = completed-with-errors → partial
            sig = {6:"seat", 8:"seat", 22:"seat"}.get(code)  # contention, not target failure
            return FetchResult(ok=ok, rows=read_sink(t.sink), exit_code=code,
                               block_signal=sig, cost_units=self.base_cost,
                               latency_s=time.time()-t0)
        finally:
            self.seats.release()
```

UiPath and Ranorex adapters follow identically: UiPath's `fetch` does `AddQueueItem` → `StartJobs(JobsCount=k)` → poll `QueueItems`, with `seats=SeatPool(unattended_robot_count)`; Ranorex's `fetch` spawns `ScrapeSuite.exe /pa:...`, maps `0/-1`, with one seat per agent machine.

---

## 7. Adaptive routing, escalation, and the constrained seat pool

### 7.1 Per-target escalation ladder

```python
async def route(target, backends, metrics):
    # 1) Confirm-and-skip: a cheap source may already answer (goal #7)
    if (hit := await cheap_confirm(target)):          # Apollo/registry/MX/cache
        return hit                                     # never spend a licensed seat

    # 2) Order candidate backends by expected utility, cheap-first
    cands = [b for b in backends if b.can_handle(target)]
    cands.sort(key=lambda b: expected_utility(b, target, metrics))  # see 7.2

    for b in cands:
        if b.seats and b.seats.free == 0 and b.tier >= Tier.SCREAMING_FROG:
            continue                                   # seat-starved: try next method now
        r = await b.fetch(target)
        metrics.record(b.name, target.domain, r)       # online learning
        if r.ok and r.rows:
            return r
        if r.block_signal == "seat":
            await requeue(target, delay=backoff("seat"))  # not a failure; retry on free seat
        elif r.block_signal in ("captcha","cf","login"):
            target.block_class = r.block_signal         # escalate to the right Tier next loop
    return FetchResult(ok=False)                        # exhausted → honest gap, no fabrication
```

### 7.2 Sensing which method works per target (goal #5)

`expected_utility` is computed **per (backend, domain)** from a rolling metrics store, not from static guesses:

```
EU(b, target) = P_success(b, domain) * value(target)
              - (cost(b) + latency_penalty(b)) * urgency
              - seat_pressure(b)                      # discourage scarce-seat use when free seats are low
```

`P_success` starts at the static prior and converges to the observed rate (Beta-Bernoulli per domain). The first time a domain throws a CF challenge, every OSS tier's `P_success` for that domain collapses and Sequentum/UiPath rise — so the router *learns the target's defenses and adapts method + concurrency in real time*. Concurrency adapts too: when a domain's recent error rate climbs, the per-domain rate limiter (bulkhead, `architecture_patterns_reference.md` §1) tightens RPS and the router lowers fan-out; when it's clean, fan-out grows.

### 7.3 Seats as a global constrained resource (goal #6)

Licensed concurrency limits are first-class constraints. A **bin-packing scheduler** assigns ready targets to backends each tick, maximizing total expected yield subject to `Σ assigned(b) ≤ b.seats.total` for every licensed backend:

```python
def schedule_tick(ready, backends, metrics):
    plan = []
    budget = {b.name: b.seats.free for b in backends if b.seats}   # free seats now
    for t in sorted(ready, key=lambda x: x.value, reverse=True):
        b = best_affordable(t, backends, budget, metrics)          # highest-EU backend with a free seat
        if b is None:
            continue                                               # all suitable seats busy → wait
        plan.append((b, t))
        if b.seats:
            budget[b.name] -= 1
    return plan
```

This keeps **every OSS lane saturated in parallel** (unlimited seats) while **every licensed seat is kept busy on its single best-fit target**, and it lets Sequentum Cloud / UiPath `JobsCount` absorb spillover when desktop seats are full. The result satisfies the platform goals jointly: maximum speed (all lanes hot), maximum coverage (escalation reaches the hardest targets), self-correction (exit-code/block-signal feedback), and combined sources (confirm-and-skip removes redundant expensive work).

### 7.4 Escalation order, summarized

```
Tier 0  curl_cffi / curl-impersonate          (static HTML, JSON APIs)        ∞ seats
Tier 1  Botasaurus / Camoufox / Scrapling     (JS render, light stealth)      ∞ seats
Tier 2  FlareSolverr / browser farm           (CF JS challenge)               pool-bounded
Tier 3  Screaming Frog  --headless            (full-site bulk extraction)     N crawl seats
Tier 4  Sequentum RunAgent / Cloud            (anti-bot, paginated tables)    desktop seats + Cloud
Tier 5  UiPath StartJobs / Ranorex exe        (login-RPA, gov UI, native app) robot/agent seats
```

A target rides up the ladder only as far as it must, the router *learns* where it lands per domain, and the scarcest seats are spent last and only where they uniquely win.

---

## 8. Operational notes

- **First-run provisioning:** SF needs one interactive EULA/license/storage acceptance per machine (or a seeded config dir); Sequentum runners need agents imported via `agent_import_folder`; UiPath needs an External App (client-credentials) + folder ID + published process `ReleaseKey`; Ranorex needs the suite compiled and a logged-in interactive session (or RDP/auto-logon) for UI automation.
- **Determinism & idempotency:** UiPath queues give exactly-once semantics with retry; Sequentum `ContinueAndRetryErrors` and SF `--overwrite --timestamped-output` make re-runs safe; every adapter writes to an idempotent upsert sink keyed by (orgnr|domain|person).
- **Metrics:** every `FetchResult` (exit code, block signal, latency, rows, cost) feeds the per-(backend,domain) store that powers §7.2 — the licensed tools are governed by exactly the same feedback loop as the free stack, which is the whole design intent.
