# ARCHITECTURE v2 — Corrected, Policy-Gated, Bulk-First Acquisition Platform

**Version:** 2.0 — 2026-06-24 · Supersedes the mechanism described across `pillars/adaptive-engine.md`, `pillars/speed-parallelism.md`, `pillars/oss-combo-matrix.md`, `pillars/licensed-tools.md`, `pillars/fusion-confidence.md`.
**Status:** Executable. Every **P0** and **P1** finding in [`critic-gaps.md`](critic-gaps.md) is folded into a concrete, corrected design below. Authority order on any conflict: `country-data/_verified/*` > `docs/COMPLIANCE.md` > verifier > this document > the original pillars.
**Scope:** 20 European markets (Nordics + DACH + Benelux + France + Southern Europe + Isles + Central/Eastern Europe), five entity types (company, person/contact, LinkedIn profile, website, vehicle).

This file is the *corrected systems design*. It does three things the original pillars did not: (1) it makes the **Bulk Ingestion Plane** a real tier that runs before any fetch (P0-1); (2) it puts a **per-source Policy Gate** in front of method selection as a hard precondition (P0-4), wired to the same `policy.yaml` the reconcile phase emits from `sources.yaml` + `country-data/_verified/*`; (3) it defines a **durable-state model** so the learning, the rate budgets, and the seat economy survive a Redis flush (P0-3). LinkedIn (P0-2), the licensed-seat broker (P0-5), real async limiting and hedging (P1-1, P1-2), the vehicle split (P1-3), parse backpressure (P1-4), the contextual bandit prior (P1-5), and the language-routed NER dispatcher (P1-6) are all designed concretely, not asserted.

---

## 1. The revised tiered system diagram

The pipeline is a **cost-ascending cascade with two gates in front of it**. Nothing reaches a socket until the Bulk plane has been consulted and the Policy Gate has approved a lawful method. The ordering — *Bulk Plane → API confirm → HTTP → CF tier → browser → AI-agent → licensed/RPA → OCR/NER → ER → graph → fusion → API* — is strict: each tier is only entered when every cheaper tier has been tried (or excluded by policy/fusion) for that field.

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║ TIER -1 · BULK INGESTION PLANE            (runs on a cron, NOT in the per-entity hot path) ║
║   BulkSource registry (per country, from policy.yaml) → download whole register + deltas   ║
║   SE Bolagsverket bulkfil + iXBRL(weekly) · NO brreg /lastdown + /roller · DK CVR S2S ES    ║
║   FI PRH all-companies JSON · FR SIRENE Parquet + INPI SFTP · BE KBO daily + SFTP           ║
║   NL KVK fin-stmt + RDW · UK CH + PSC + Accounts · IE CRO · CZ ARES XML · PL KRS/REGON       ║
║   CH Zefix/LINDAS · AT/DE HVD+OffeneRegister · GLEIF golden copy (cross-border key)          ║
║      │  parse (arelle for XBRL, NOT OCR) → upsert registry_bulk_index + entity Bloom        ║
╚══════╪═══════════════════════════════════════════════════════════════════════════════════════╝
       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ INTAKE GATE   Bloom-dedup · bulk_index hit? · freshness TTL · DNC/erasure suppress (P2-7)  │
│               → 30–60% of company-level fields answered with ZERO fetch                      │
└──────┬───────────────────────────────────────────────────────────────────────────────────┘
       │ residual: contacts/email/phone + no-bulk markets (IS,HU,IT,ES,PT,LU) + stale fields
       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ POLICY GATE  (P0-4 — HARD precondition, before MethodRouter is even consulted)             │
│   resolve(source,country) → PolicyDecision{ allowed_methods, rate_cap_hard, forbidden,      │
│   reuse_restriction, reroute_to, lawful_basis, transport_floor }                            │
│   DE Handelsregister → cap 60/h, reroute OffeneRegister · ES CORPME → forbidden, reroute     │
│   BOE BORME · KBO/DE-dir contact → reuse=no_direct_marketing · gov registry → never Tor     │
└──────┬───────────────────────────────────────────────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ADAPTIVE ROUTER  (the brain; sees only methods the Policy Gate allowed)                    │
│  MethodRouter  Thompson bandit, lock-free Redis read, (WAF,TLD,page-type) cluster prior     │
│  FailureClassifier → deterministic remediation   AdaptiveLimiter  aiometer/aiolimiter AIMD  │
│  IdentityFactory  coherent UA+JA3/JA4+headers+viewport+locale+geo-proxy                      │
└──┬────────────────────┬─────────────────────┬─────────────────────┬───────────────────────┘
   │ HEDGE (staggered): cheap fired first; expensive launched only after deadline miss (P1-2) │
   ▼                    ▼                     ▼                     ▼
┌─────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐
│ TIER 0      │  │ TIER 1–2 HTTP    │  │ TIER 3 CF/BROWSER │  │ TIER 3.5 AI-AGENT (residual) │
│ API CONFIRM │  │ curl_cffi/wreq → │  │ cloudscraper →    │  │ LLM-planned nav for novel    │
│ registry/   │  │ Scrapling        │  │ cf_clearance-     │  │ portals (bounded, gated by   │
│ GLEIF/VIES  │  │                  │  │ harvest→replay →  │  │ cost counter; never paid in  │
│ Apollo*GATED│  │                  │  │ camoufox/nodriver/│  │ the first wave)              │
│ behind cost │  │                  │  │ botasaurus        │  │                              │
└─────────────┘  └──────────────────┘  │ FlareSolverr(opt) │  └──────────────────────────────┘
                                        └────────┬─────────┘
                                                 ▼ (only if OSS exhausted on this host)
                            ┌──────────────────────────────────────────────────┐
                            │ TIER 4–5 LICENSED / RPA  (one ScraperBackend IF)  │
                            │ ┌──────────────────────────────────────────────┐ │
                            │ │ LicensedSeatBroker (GLOBAL priority queue)    │ │ (P0-5)
                            │ │ SF(4) · Sequentum(2 desk + Cloud) · UiPath ·  │ │
                            │ │ Ranorex · value/urgency · cloud-overflow w/   │ │
                            │ │ daily $ ceiling · cross-backend seat view     │ │
                            │ └──────────────────────────────────────────────┘ │
                            └──────────────────────┬───────────────────────────┘
                                                   │ raw HTML / PDF / JSON
                                                   ▼  (broker hand-off, BACKPRESSURED — P1-4)
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 6 · CPU/GPU PARSE FARM  (separate pools; bounded queue, producer blocks at high-water)│
│   selectolax/lxml struct · XBRL/iXBRL FAST PATH (arelle) · PyMuPDF text → opencv →          │
│   PaddleOCR/RapidOCR/Tesseract → Claude Vision (cascade, OCR only for scanned PDFs)         │
│   NER LANGUAGE DISPATCHER (P1-6): doc.lang → best model (table §6) else xx_ent_wiki_sm       │
└──────┬───────────────────────────────────────────────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 7 · ENTITY RESOLUTION   blocking → RapidFuzz → Splink (DuckDB/Spark) → cluster        │
│ TIER 8 · RESOLUTION GRAPH    connected components w/ cohesion check; reg-id/LEI short-circ. │
│ TIER 9 · FUSION + CONFIDENCE log-odds agreement · freshness decay · isotonic calibration    │
│          └─► feeds back to router:  need_expensive_fetch()? → skip / cheap_only / full      │
└──────┬───────────────────────────────────────────────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 10 · CANONICAL STORE + OUTPUT API                                                     │
│   per-field {value, confidence, last_verified, sources[], lawful_basis, method_badge}       │
│   GDPR filter (provenance, reuse_restriction, DNC, erasure) · Fabric/Postgres + DuckDB graph│
└──────────────────────────────────────────────────────────────────────────────────────────┘

DURABLE STATE (§8):  Redis HA (AOF + replica + Sentinel) for hot state; Postgres/Fabric for the
  authoritative snapshots of bandit posteriors, method-memory, source-reliability, seat ledger,
  risk-budget counters. Degraded mode defined when Redis is unreachable.
```

The two structural changes from v1 are the **two gates before the router** and the **AI-agent tier between browser and licensed**. Tier-1 Bulk is *off the hot path entirely* — it is a scheduled producer that fills `registry_bulk_index`, so the per-entity request usually terminates at the Intake Gate with no network call at all. The AI-agent tier (Tier 3.5) is a bounded LLM-planned navigation lane for genuinely novel portals where no learned selector exists; it is gated by the same cost counter as paid sources and is never in the initial hedge wave.

---

## 2. P0-1 — Bulk Ingestion Plane as Tier -1

The single largest speed and coverage lever is making whole-country bulk a *first-class plane that runs before any fetch lane*, not a tier-0 confirmer that races a scrape. The original pillars asserted "registry bulk-dumps already answer 30–60%" but no component owned the download, the index, or the delta feed. Tier -1 owns all three.

**`BulkSource` registry.** Every country's bulk capability is a row seeded directly from `sources/sources.yaml` (which already carries `bulk: true|false`, `format`, `refresh`, `access`) plus the `country-data/_verified/*` legal/cadence facts. A `BulkSource` is `{country, name, url, format(json|csv|parquet|xbrl|xml), cadence, license, parser_id, delta_feed_url}`. The reconcile phase compiles `sources.yaml` into `policy.yaml`; the Bulk plane reads the `bulk: true` subset.

**Scheduling.** Each source runs on its *native cadence* via the scheduler, not a fixed nightly batch: brreg nightly, KBO/SIRENE daily, SE iXBRL weekly, CH Zefix daily, GLEIF daily, UK Companies House monthly bulk + PSC daily snapshot. The download is idempotent (content-hash short-circuit on unchanged files) and writes into `registry_bulk_index` (the columnar canonical store) plus the entity **Bloom filter** used by the Intake Gate.

**Delta subscribers.** Where a country publishes a change file (Bolagsverket, brreg, CVR, Companies House), a delta subscriber pulls only the diff and upserts — so the index stays fresh without re-pulling the whole register. Faust/Kafka carries the change firehose; a missed window triggers a full re-pull guarded by the content-hash so it is cheap when nothing changed.

**XBRL is structured, not OCR (P1-7).** Financial filings that arrive as iXBRL/XBRL (SE weekly bulk, UK Accounts Data Product, FR INPI, BE NBB, NL KVK financial-statements, FI subset) are parsed with `arelle` into tagged facts on the *fast* path — sub-50 ms, exact numbers, no OCR. OCR (Tier 6) is reserved for scanned/PDF-only filings (DE per-doc, IT/ES visure, LU/IS per-doc). For Sweden specifically the weekly iXBRL bulk is a *BulkSource*, never a per-company scrape.

**The Intake Gate is the payoff.** For each residual entity the gate checks, in order: (1) entity Bloom — have we seen this reg-id at all; (2) `registry_bulk_index` hit and is the needed field present; (3) field freshness vs its half-life; (4) DNC/erasure suppression. If the field is present and fresh, the request **terminates with zero fetch**. Only the genuine residual — contacts/email/phone the registries do not carry, plus the no-bulk markets (IS, HU, IT, ES, PT, LU) — descends to the Policy Gate and the cascade. This is what makes the free tier viable: it removes 30–60% of fetches before a socket opens.

---

## 3. P0-2 — LinkedIn: public-SERP lane + strict risk budget; authenticated crawl forbidden

The original `oss-combo-matrix` row 10 ("headless login once → export storage_state → replay reads with cookies, 1 login → 50 reads") is **deleted**. Automated authenticated LinkedIn reading is the exact conduct litigated in *hiQ v. LinkedIn* (post-remand) and a CFAA/ToS landmine that burns the operating identity. `docs/COMPLIANCE.md §2` already forbids it; the architecture now enforces it.

**The only LinkedIn lane is public-surface resolution.** A multi-engine SERP search (`site:linkedin.com/in "<name>" "<company>"`) over DuckDuckGo / Startpage / SearXNG (the approach the existing `contact-intel` and `company-contact-finder` skills already use) returns candidate public profile URLs; a fuzzy match on `name + company + title` selects the best and stores a `linkedin_urn` with a confidence score. We never authenticate, never solve LinkedIn's auth challenges, never read connections/messages. This bounds LinkedIn coverage to what the public SERP exposes — a deliberate, documented compliance/coverage trade.

**Strict global risk budget.** LinkedIn carries its own `RiskBudget` object, not just a per-host RPS. Three counters, all in durable state (§8): `linkedin.daily_serp_queries` (hard global cap, e.g. 5 000/day across the whole fleet), `linkedin.identity_burn_count` (resolver identities retired this window), and `linkedin.block_rate_ewma`. When the daily cap is hit, the lane closes for the window and queued LinkedIn work parks (not DLQ — it resumes next window). When `block_rate_ewma` crosses a ceiling, the limiter collapses LinkedIn to `cwnd=1` and slows the SERP engines, isolated by the Bulkhead so this never touches brreg. The SERP engines themselves are rotated and rate-limited as ordinary hosts; LinkedIn the *domain* is never fetched directly.

**Policy encoding.** The Policy Gate marks `linkedin.com` as `automated_authenticated_access=forbidden` and `public_serp_only=true`; the router cannot escalate a browser *into* a logged-in LinkedIn session because no such method is in the allowed set. Authenticated LinkedIn is documented as an explicit out-of-scope/forbidden method, consistent with the honesty moat.

---

## 4. P0-3 — Redis HA + durable learning + degraded mode

Redis is simultaneously broker, cache, Bloom store, rate-limit store, method-memory, identity-burn store, bandit-posterior store, and seat ledger. A flush forgets every learned method, resets the Bloom (re-scrapes everything), resets every token bucket (thundering-herd into per-host blocks → mass identity burn), and loses circuit-breaker state. v2 hardens this on three axes.

**(a) HA Redis.** Run Redis with **AOF persistence** (`appendfsync everysec`) + at least one **replica** + **Sentinel** for automatic failover (extend to Redis Cluster for sharding once the ~100k msg/s ceiling is hit). AOF means a process restart replays to the last second; the replica means a node loss promotes without data loss; Sentinel means the fleet re-points without manual intervention.

**(b) Durable learning — Redis is a cache, Postgres/Fabric is the source of truth.** Bandit posteriors, method-memory, source-reliability, seat ledger, and risk-budget counters are treated as *durable* state. A snapshotter flushes them to Postgres/Fabric on a short interval (§8 defines the schema and cadence); on cold start the router *reloads* from Postgres before serving traffic. Learning therefore survives a full Redis loss — we re-warm the cache from the durable store rather than re-paying the entire OSS-climb cost on every host.

**(c) Degraded mode (explicit).** If Redis is unreachable, the system does **not** fail open into aggressive defaults. It enters degraded mode: read the *last* Postgres snapshot of posteriors read-only; run a **conservative fixed concurrency** (e.g. `cwnd=2` per host, global rate floor) and **cheapest-method-first** (no Thompson exploration, just the lowest-cost allowed method) ; the Bloom is rebuilt lazily from `registry_bulk_index` so dedup is degraded-but-present; new writes buffer to a local WAL and replay when Redis returns. The bias is always toward *under*-fetching and *not* burning identities, because the cost of a flush should be slowness, never a wave of blocks.

---

## 5. P0-4 — The per-source Policy Gate (interface)

The Policy Gate is the hard precondition the router consults **before** method selection. It converts the prose in `country-data/_verified/*` and the structured rows in `sources/sources.yaml` into routing decisions. The reconcile phase compiles those into `policy.yaml`; the gate loads `policy.yaml` and answers one question per `(source, country)`: *which methods, at what rate, are lawful here, and where do I go if this door is closed?*

### 5.1 `policy.yaml` shape (compiled from `sources.yaml` + `country-data/_verified/*`)

```yaml
# policy.yaml — emitted by the reconcile phase; the router NEVER bypasses it.
defaults:
  transport_floor: https            # never downgrade below TLS
  government_registry_via_tor: false # HARD: gov registries never via Tor/aggressive escalation
sources:
  DE_handelsregister:
    country: DE
    allowed_methods: [api_confirm]          # browser escalation NOT permitted here
    rate_cap_hard: { count: 60, per: hour }  # §§303a/b StGB criminal exposure above this
    automated_access_forbidden: false
    reroute_to: DE_offeneregister            # prefer the bulk snapshot + bundesAPI deltas
    reuse_restriction: none
    lawful_basis: public_register
    legal_note: "§§303a/b StGB; 60 req/h hard cap; never bulk-scrape the portal"
  ES_corpme_sede:
    country: ES
    allowed_methods: []                      # automated access forbidden outright
    automated_access_forbidden: true
    reroute_to: ES_boe_borme_api             # the lawful spine
    reuse_restriction: none
    legal_note: "WAF rejects bots; automated access forbidden; use BOE BORME API + UiPath"
  BE_kbo_opendata:
    country: BE
    allowed_methods: [bulk_download, api_confirm]
    reuse_restriction: no_direct_marketing   # contact fields present but reuse forbidden
    lawful_basis: public_register
  NL_kvk_bulk:
    country: NL
    allowed_methods: [bulk_download]
    note_keying: anonymised                  # no name, no KVK nr → not a deterministic key
  linkedin_public:
    country: "*"
    allowed_methods: [serp_resolve]
    automated_authenticated_access: forbidden
    public_serp_only: true
    risk_budget: linkedin
```

### 5.2 Gate interface (the contract the router calls)

```python
@dataclass(frozen=True)
class PolicyDecision:
    allowed_methods: tuple[str, ...]      # subset the MethodRouter may sample from
    rate_cap_hard: RateCap | None         # enforced ABOVE the AIMD limiter (never exceeded)
    automated_access_forbidden: bool
    reroute_to: str | None                # alternate source_id if this door is closed
    reuse_restriction: str                # none | no_direct_marketing | b2b_only | ...
    lawful_basis: str | None              # public_register | legal_obligation | legit_interest
    transport_floor: str                  # https | http  (never downgrade below)
    via_tor_allowed: bool                 # False for every government registry
    risk_budget: str | None               # name of a global RiskBudget (e.g. "linkedin")

class PolicyGate:
    def resolve(self, source_id: str, country: str) -> PolicyDecision: ...
    def is_lawful_emit(self, field_provenance) -> bool:    # output-side reuse enforcement
        ...
```

**Where it sits.** `resolve()` is called in pre-flight, *before* `MethodRouter.choose()`. Its `allowed_methods` becomes the `allowed=` argument the bandit samples within — so the bandit physically cannot escalate a browser into ES CORPME or exceed DE's 60/h. If `automated_access_forbidden` or `reroute_to` is set, the request is redirected to the alternate source before any method runs. `rate_cap_hard` is enforced as an outer token bucket *above* the adaptive limiter: the AIMD sawtooth may ride below it, but a hard legal cap is never crossed even when the host *appears* friendly. `via_tor_allowed=false` and `transport_floor` make "never route a government registry through Tor or aggressive escalation" a structural impossibility, not advice. `is_lawful_emit()` is the second enforcement point: the output API drops any field whose `reuse_restriction` conflicts with the consumer's declared purpose (KBO/DE-directory contact fields withheld from direct-marketing exports). "A free bulk/API exists → never scrape" is implemented as: if a `bulk_download` method is allowed for a source, the cascade is skipped for any field that bulk carries.

---

## 6. P0-5 — Global LicensedSeatBroker (priority queue + cloud overflow + cost ceiling)

Seats are tiny (SF=4, Sequentum desktop=2, UiPath/Ranorex a handful) and at 50M scale the hard-target tail that *only* licensed tools can crack vastly exceeds seat throughput. v1 modelled per-backend semaphores with no global view, no overflow trigger, and no cost ceiling — so scarce seats throttled the whole pipeline silently. v2 replaces this with one broker.

**Single global priority queue across all four backends.** Every licensed-eligible target carries `value` and `urgency`. The broker holds one priority queue and a **cross-backend seat view** (SF, Sequentum, UiPath, Ranorex pools visible together), allocating the highest-`value` target to the best-fit *free* seat across *any* backend — so a scarce Sequentum seat can be traded against an idle Screaming Frog seat. Expected-utility routing: `EU(backend, target) = P_success(backend,domain)·value − (cost(backend)+latency_penalty)·urgency − seat_pressure(backend)`, where `P_success` is a Beta-Bernoulli per `(backend, domain)` — so the first CF challenge on a domain collapses every OSS tier's `P_success` and lifts Sequentum/UiPath automatically.

**Explicit cloud-overflow policy.** Spill to Sequentum Cloud / UiPath cloud robots **only when** desktop seats are full **AND** backlog age > threshold **AND** `value(target) > cost_of_cloud_call`. Cloud spend is governed by a **hard per-day ceiling** held in durable state (`seat:cloud_spend:{day}`); when the ceiling is hit, no more cloud calls fire that day. When even cloud is saturated, targets DLQ with an explicit `seat_starved` reason (never silent waiting).

**Seat saturation is a first-class metric.** It drives both KEDA-style autoscaling of the licensed worker VMs *and* the dynamic `value` threshold — when seats are scarce the broker raises the bar for "is this target worth a seat?", so low-value targets wait and high-value ones get the seat. A licensed job is dispatched exactly like an OSS rung (same queue, same method-memory, same per-domain circuit breaker), so the router learns "this domain always needs Sequentum" and routes straight there, skipping the wasted OSS climb.

### NER language dispatcher (P1-6) and XBRL lane (P1-7) — model table

The parse farm routes `document.lang → best model` (exact IDs from `country-data/_verified/*`), falling back to `xx_ent_wiki_sm` only where no dedicated model exists. XBRL/iXBRL bypasses NER/OCR entirely into the structured fast path.

| Market(s) | Language | NER model (verified ID) | spaCy fallback |
|---|---|---|---|
| SE | sv | `KBLab/bert-base-swedish-cased-ner` | `sv_core_news_lg` |
| FI | fi | `TurkuNLP/bert-base-finnish-cased-v1` (FinBERT) | — |
| DK | da | `DaCy large` (`da_dacy_large_trf`) | `da_core_news_lg` |
| NO | nb | `NbAiLab/nb-bert-base-ner` | `nb_core_news_lg` |
| IS | is | `mideind/IceBERT`-NER / `nbailab-base-ner-scandi` | `xx_ent_wiki_sm` |
| DE, AT | de | `flair/ner-german-large` | `de_core_news_lg` |
| FR | fr | `Jean-Baptiste/camembert-ner` | `fr_core_news_lg` |
| NL | nl | RobBERT | `nl_core_news_lg` |
| CH | de/fr/it | `wikineural-multilingual-ner` (xlm-roberta) | route per language |
| IT | it | `it_core_news_lg` (NER F≈0.884) | `it_core_news_trf` |
| ES | es | `PlanTL-GOB-ES/roberta-large-bne-capitel-ner` | `es_core_news_lg` |
| PT | pt | BERTimbau | `pt_core_news_lg` |
| UK, IE | en | `en_core_web_trf` | `en_core_web_lg` |
| PL | pl | HerBERT | `pl_core_news_lg` |
| CZ | cs | NameTag 3 (ÚFAL) | — |
| HU | hu | HuSpaCy `hu_core_news_lg` (F1≈0.869) | — |

`spaCy nlp.pipe(batch_size=256, n_process=N)` batches each language pool; the GPU OCR cascade (RapidOCR → PaddleOCR → Tesseract → Claude Vision) runs only on scanned PDFs, and the XBRL fast path (`arelle`) handles every machine-readable filing with no GPU at all.

---

## 7. P1 fixes folded into the router and the work fabric

**P1-1 — real async limiting, lock-free bandit reads.** The hand-rolled `self._sem._value` poking and the single `asyncio.Lock` around the token-bucket refill (which serialized *every* request on a host) are gone. Rate + concurrency are governed by **`florimondmanca/aiometer`** `run_all(..., max_at_once=N, max_per_second=R)` (GCRA-based) for the fan-out lanes and **`mjpieters/aiolimiter`** leaky-bucket for steady per-host pacing; AIMD now resizes by mutating `max_at_once`/`max_per_second` on a per-host limiter object, not a private counter. The bandit posterior is read as a **lock-free Redis sample** (or shared `fidelity/mabwiser` state), never a per-worker dict that silently goes stale; cache TTL + explicit invalidation make all fleet workers converge on a host's learned method.

**P1-2 — hedged (staggered) requests, paid sources never in the first wave.** The headline `resolve_company` no longer fires the scrape and confirmer in parallel and cancels the loser (`task.cancel()` does not free an in-flight socket/Chromium tab, so the bandwidth/RAM is already spent). The default is **staggered hedging**: fire free/cheap tier-0 first; launch the expensive tier only after a short deadline if cheap has not answered. **Apollo (paid) is never in the initial wave** — it is gated behind the same cost-aware counter as paid proxies and CAPTCHA solvers, fired only after a free/cheap miss, so we never burn a credit a free registry would have made unnecessary.

```python
async def hedged(entity):
    cheap = aiometer.run_all([lambda: bulk_index(entity),
                              lambda: registry_api(entity),
                              lambda: cached_lookup(entity)], max_at_once=3)
    done = await asyncio.wait_for(cheap, timeout=0.4)
    if (r := pick_best(done)) and is_acceptable(r):
        return r                                   # ~70–85% end here, ~80 ms, FREE
    return await resolve_with_scrape(entity)       # only the hard tail pays for a browser
    # Apollo enrich is reachable ONLY inside resolve_with_scrape, behind cost_counter.allow()
```

**P1-3 — vehicle split: technical/fleet (open bulk) vs owner (Nordic-only).** The canonical model no longer implies pan-European owner coverage. **(a) Technical/fleet** = broadly-available free bulk wired as BulkSources: RDW (NL, Socrata SODA, no key), Traficom (FI, open ZIP-CSV), ACI/MIT (IT LOD), DGT microdata (ES, anonymised), UK VES per-plate + MOT, ASTRA IVZ (CH), LU Parc Automobile (per-vehicle, CC0). **(b) Owner linkage** = Nordic-only (SE reseller scrapes via `merinfo`/`biluppgifter`/`blocket` skills; DK single public lookup), explicitly flagged as a coverage gap everywhere else. The Policy Gate marks owner-data sources in DE/IE/PL/CZ/HU/FR/PT/AT as `automated_access_forbidden`/`restricted` so the bandit never escalates into them.

**P1-4 — parse-pool backpressure (bounded queue, producer blocks at high-water).** Raw bytes are handed to the CPU/GPU parse pool over the broker so the fetch loop never stalls on a 200 ms parse — *and* the loop is closed the other way: the `parse` stream has a **high-water mark**; when depth exceeds it, the IO limiter's `acquire()` **blocks** (or the scheduler de-prioritizes new fetches) until the parse pool drains. Throughput is governed by the *slowest necessary* stage, so freshly-scraped HTML (the heaviest payload) can never grow the queue until Redis OOMs. KEDA still scales the parse pool on stream length, but backpressure covers the scaling latency and the GPU-pod ceiling.

**P1-5 — hierarchical/contextual bandit prior, per-traffic decay.** Most of 50M hosts are hit only a handful of times, so a flat `(1,1)` prior makes Thompson sampling effectively random and the cheapest-first intent is lost. v2 backs a host's sparse posterior off to a **cluster posterior keyed on `(WAF_vendor, TLD, page_type)`** — a brand-new `.se` site behind Cloudflare *starts* at the empirically-best method for "`.se` + Cloudflare", not the flat prior. Implemented as `mabwiser` LinUCB with context `[waf_vendor, tld, page_type, hour_of_day]`, or a two-level Beta where the cluster's `(α,β)` seeds the host prior. Decay is **per-traffic-volume**: slow decay for rarely-hit hosts (so their evidence is not forgotten between visits), fast decay for high-traffic hosts where a flapping WAF must demote a method quickly.

**P1-7 — XBRL/iXBRL structured lane** (also under §2/§6): `arelle`/iXBRL parse to tagged facts is the primary financials path; OCR is only for legacy scanned PDFs. This is faster (sub-50 ms vs OCR) and exact (tagged facts vs OCR'd numbers).

---

## 8. The durable-state model

State is split into a **hot tier (Redis HA)** and an **authoritative tier (Postgres/Fabric)**. Redis is a cache and a coordination bus; Postgres/Fabric is the source of truth for everything that must survive a flush. A snapshotter copies hot → durable on a cadence; the loader copies durable → hot on cold start and in degraded mode.

| State | Hot (Redis) | Durable (Postgres/Fabric) | Snapshot cadence | On Redis loss |
|---|---|---|---|---|
| **Bandit posteriors** `(host\|cluster, method) → α,β,ewma_latency,cost` | `router:{host}` hash | `bandit_posterior(scope, method, alpha, beta, ewma_latency_ms, cost_w, updated_at)` | every 60 s + on demote | reload last snapshot; degraded = cheapest-first |
| **Cluster prior** `(waf,tld,page_type) → α,β` | `cluster:{key}` hash | `cluster_prior(waf_vendor, tld, page_type, alpha, beta, updated_at)` | every 5 min | reload; seeds new-host priors |
| **Method-memory** `(domain,page_type) → last_good_method` | `mem:{domain}:{pt}` | `method_memory(domain, page_type, method, last_ok_at)` | every 60 s | reload |
| **Source-reliability** `r_s` per `(source, field, country)` | `rel:{src}:{field}:{cc}` | `source_reliability(source_id, field_type, country, r_s, n_obs, updated_at)` | every 5 min | reload |
| **Entity Bloom** | `bloom:entities` | rebuilt from `registry_bulk_index` | on bulk load | lazy rebuild from index |
| **Rate budgets / token buckets** | per-host bucket keys | `rate_cap(source_id, country, count, per)` (the *caps*, not live counters) | caps are static config | live counters reset → conservative restart, caps re-loaded |
| **Risk budgets** (LinkedIn, paid-source) | `risk:linkedin:{day}` counters | `risk_budget(name, window, limit, spent, updated_at)` | every 60 s | reload spent; if unknown, treat as exhausted (fail safe) |
| **Seat ledger** (per backend free/busy, cloud $) | `seat:{backend}` , `seat:cloud_spend:{day}` | `seat_ledger(backend, total, in_use, cloud_spend_day, updated_at)` | every 30 s | reload; cloud spend resumes from snapshot |
| **Circuit breakers** `(host) → state, open_until` | `cb:{host}` | `circuit_state(host, state, open_until, fail_count)` | every 60 s | reload open hosts (don't re-hammer) |
| **Identity burn** `(host) → burned proxies/UAs` | `identity:burned:{host}` set | `identity_burn(host, proxy, ua, burned_at)` | every 5 min | reload (don't reuse a burned identity) |
| **Task state** `pending→inflight→done\|dlq` | stream + `task:{id}` | `task_state(url, host, state, last_method, last_identity, updated_at)` | on transition | reload inflight → re-enqueue |
| **DLQ** | `tasks:dlq:{host}` | `dlq(url, host, reason, trace, parked_at)` | on enqueue | durable already |

**Snapshotter.** A single async task (idempotent, leader-elected via a Redis lock so only one fleet member runs it) batches each table's dirty keys and `UPSERT`s into Postgres/Fabric on the cadence above. Writes are append-or-upsert on `(scope, updated_at)` so a snapshot is never torn. The seat ledger and risk budgets snapshot most aggressively (30–60 s) because losing them costs money (cloud overspend) or legal exposure (LinkedIn over-cap).

**Loader / cold start.** On boot, the router *blocks serving* until it has reloaded `bandit_posterior`, `cluster_prior`, `source_reliability`, `circuit_state`, `identity_burn`, `seat_ledger`, and `risk_budget` from durable storage into Redis. This is the mechanism that makes learning survive a flush — we re-warm the cache rather than re-pay the OSS-climb on every host.

**Degraded mode (restated as a state contract).** Redis unreachable ⇒ (1) router serves read-only from the last in-process snapshot, cheapest-allowed-method, no exploration; (2) limiter pins `cwnd=2`, global rate floor; (3) Bloom rebuilt lazily from `registry_bulk_index`; (4) risk budgets with unknown `spent` are treated as **exhausted** (LinkedIn/paid lanes close) — fail safe, never fail open; (5) writes buffer to a local WAL, replayed on reconnect. The invariant: a state outage degrades *speed and coverage*, never *compliance* and never *identity safety*.

---

## 9. P2 items (folded, lower blast radius)

Carried for completeness; each is already designed in the pillars and unchanged in intent: SMTP-RCPT reserved for warmed dedicated IPs, never scraping proxies (P2-1); FlareSolverr optional/pooled/health-checked behind the `cf_clearance`-harvest path (P2-2); proxies scored per-`(domain,proxy)` against rotating self-hosted echo endpoints, not just `httpbin.org` (P2-3); calibration bootstrapped on the registry-confirmable subset with email/phone marked *uncalibrated* until feedback accrues (P2-4); a schematized metrics store `(backend|method, domain, country) → rolling success/latency/block/cost` in Postgres/Fabric (P2-5, now part of §8); deterministic browser+version → impersonate-token derivation with a UA-major == impersonate-version unit test (P2-6); DNC/erasure checked at **intake**, not just output (P2-7).

---

## 10. How v2 closes the critic

| Finding | v1 status | v2 resolution |
|---|---|---|
| P0-1 Bulk plane | name-dropped | Tier -1 plane, `BulkSource` registry from `sources.yaml`, delta subscribers, Intake Gate (§2) |
| P0-2 LinkedIn | ToS-reckless cookie replay | row 10 deleted; public-SERP lane + global risk budget; authenticated crawl forbidden (§3) |
| P0-3 Redis SPOF | no HA/durability | AOF+replica+Sentinel; durable snapshots; explicit fail-safe degraded mode (§4, §8) |
| P0-4 Policy gate | scrape-everything vs legal stops | `PolicyGate.resolve()` hard precondition before method selection; `policy.yaml` from reconcile (§5) |
| P0-5 Seat starvation | per-backend semaphores | global LicensedSeatBroker, priority queue, cloud overflow + $ ceiling, seat saturation metric (§6) |
| P1-1 Fake parallelism | `_sem._value` + global lock | aiometer/aiolimiter; lock-free bandit reads; explicit cache invalidation (§7) |
| P1-2 Race + double-charge | parallel race, Apollo in wave | staggered hedging; Apollo never in first wave, cost-gated (§7) |
| P1-3 Vehicle scope | implied pan-EU owner | technical/fleet bulk vs Nordic-only owner, flagged gap (§7) |
| P1-4 No backpressure | one-way handoff | bounded parse queue, producer blocks at high-water (§7) |
| P1-5 Bandit cold start | flat prior, thrash | `(WAF,TLD,page-type)` cluster prior, per-traffic decay (§7) |
| P1-6 NER / XBRL | hardcoded `en_core_web_md` | language dispatcher with verified model IDs; XBRL structured fast path (§6) |

The two halves of the platform — the scrape-everything cascade and the honesty/compliance moat — are now reconciled by a single enforced **Policy Gate** in front of the router and a **lawful-emit filter** at the output, so they can no longer contradict each other. Every paid action (Apollo credits, cloud seats, residential proxies, CAPTCHA solves) sits behind a cost counter; every legal limit sits behind the Policy Gate; every piece of learning sits behind a durable snapshot. The platform runs at the maximum speed each target *currently and lawfully* tolerates — and degrades into slowness, never into blocks or breaches, when its state store fails.
