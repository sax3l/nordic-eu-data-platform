# MASTER BLUEPRINT — Adaptive Multi-Method Company / Contact / LinkedIn / Website / Vehicle Data Platform

**Nordics + DACH + Benelux + France + Southern Europe + Isles + Central/Eastern Europe (20 markets)**
**Version:** 1.0 — 2026-06-24 · Chief-architect consolidation of `arch_*`, `country_*`, `verify_*`, `critic.md`
**Status:** Executable. Verifier corrections applied (verifier trusted over original on every conflict). Critic P0–P2 fixes folded into the design.

---

## 1. Executive Summary + Core Thesis

### 1.1 What we are building

A single platform that builds and continuously refreshes a **calibrated, provenance-stamped graph of every company, contact person, LinkedIn profile, website, and vehicle** across 20 European markets, by treating data acquisition as an **adaptive, multi-method optimisation problem** rather than a fixed scraper. The platform uses *every* free open-source repo, *every* licensed tool the user owns (Screaming Frog SEO Spider, Sequentum Desktop+Cloud, UiPath, Ranorex), and *every* free government bulk feed — each as an interchangeable "method" the system selects between in real time.

### 1.2 The core thesis (eight goals, one mechanism)

The user's eight goals collapse into one mechanism: **a per-target adaptive router that ranks every method cheapest-first, senses which one actually works, races the cheap confirmers against the slow scrapes, and self-heals when conditions change.** Concretely:

1. **Use every free repo maximally** — every OSS tool (curl_cffi, Botasaurus, Camoufox, nodriver, Scrapling, FlareSolverr, selectolax, RapidFuzz, Splink, PaddleOCR, spaCy, GLiNER) is a registered method/stage the router can select.
2. **Use every licensed tool maximally** — Screaming Frog / Sequentum / UiPath / Ranorex are **first-class bandit arms behind one `ScraperBackend` interface**, promoted automatically the moment they are the only method that cracks a host, governed by a global seat broker.
3. **Always maximum speed** — a **Bulk-Ingest-First plane** answers 30–60 % of company fields with *zero fetches*; the remainder runs on AIMD congestion control that rides just under each host's block threshold.
4. **Auto-detect + self-correct** — a precise `FailureClassifier` (CF/DataDome/PerimeterX/Akamai/Imperva/AWS-WAF/honeypot/poison) maps each block class to a deterministic remediation; circuit breakers + DLQ + online bandit learning recover without human edits.
5. **Sense + adapt method & concurrency per target** — per-host Thompson-sampling bandit (method) + per-host AIMD (concurrency), both online, both decaying for non-stationarity, **backed off to a `(WAF, TLD, page-type)` cluster prior so long-tail hosts start at their class's best method**.
6. **Every kind of parallelism** — per-source, per-host, per-country, per-worker, per-pool fan-out; distributed broker + worker fleet; source-racing/hedging.
7. **Combine all sources for speed AND coverage** — a cheap registry/API confirm that pushes a field over the confidence threshold **cancels (or never launches) the slow scrape**; cross-source agreement simultaneously raises confidence (coverage) and kills redundant work (speed).
8. **Cover every entity across all 20 markets** — a canonical entity model keyed on national reg-ids + LEI + VAT, fed by per-country bulk sources, with honest, explicitly-scoped coverage where the law closes a door (UBO, vehicle-owner).

### 1.3 The five corrections the critic forces into the thesis

The architecture mechanism was strong but had to be hardened on five points before it could be called executable:

- **Bulk-first, not scrape-first.** The single biggest speed+coverage lever — free whole-country bulk registers — is now a **Tier -1 Bulk Ingestion Plane** that runs *before* any fetch lane, not a footnote.
- **Policy-aware routing.** A **per-source policy table** (rate caps, forbidden-automated-access, reuse restrictions) is a hard precondition the router consults before choosing a method — so the platform never walks into DE Handelsregister's criminal-law cap or ES CORPME's WAF, and never re-markets data a source forbids.
- **Safe LinkedIn.** Authenticated LinkedIn scraping is **forbidden**; LinkedIn is resolved from the public SERP surface under a strict global risk budget.
- **Honest vehicle scope.** Vehicle data is split into **technical/fleet (broadly free)** and **owner-linkage (Nordic-only, gated)** — the canonical model no longer implies pan-European owner coverage that the law forbids.
- **Durable shared state + HA Redis.** Bandit posteriors, method-memory and source-reliability are snapshotted to Postgres/Fabric so learning survives a Redis flush; Redis runs HA with a defined degraded mode.

---

## 2. System Architecture Diagram

```
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │                         TIER -1 · BULK INGESTION PLANE  (runs first, cheapest)         │
 │   per-country BulkSource registry → download whole register + delta feeds              │
 │   SE Bolagsverket bulkfil+iXBRL · NO brreg lastned+roller · DK CVR S2S · FI PRH JSON   │
 │   FR SIRENE/INPI Parquet+SFTP · BE KBO daily+SFTP · NL KVK+RDW · UK CH+PSC+accounts    │
 │   IE CRO · CZ ARES XML · PL KRS/REGON · CH Zefix/LINDAS · AT/DE HVD/OffeneRegister      │
 │   GLEIF golden copy (cross-border key)                                                  │
 │            │ loads → registry_bulk_index + entity Bloom + canonical store               │
 └────────────┼───────────────────────────────────────────────────────────────────────────┘
              ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │  INTAKE GATE:  Bloom-dedup · bulk-index hit? · freshness TTL · DNC/erasure suppress    │
 │                (answers 30–60% of company fields with ZERO fetch)                       │
 └────────────┬───────────────────────────────────────────────────────────────────────────┘
              │ only residual (contacts/email/phone, no-bulk markets, stale fields)
              ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │  PER-SOURCE POLICY GATE  (HARD precondition before any method is chosen)               │
 │  (source,country) → {rate_cap_hard, automated_access_forbidden, reuse_restriction}     │
 │  e.g. DE Handelsregister ≤60/hr→route to OffeneRegister · ES CORPME=forbidden→BOE BORME │
 └────────────┬───────────────────────────────────────────────────────────────────────────┘
              ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │             ADAPTIVE ROUTER  (the brain — §3)                                          │
 │  • MethodRouter: per-host Thompson bandit + (WAF,TLD,page-type) cluster prior          │
 │  • FailureClassifier → deterministic remediation map                                   │
 │  • AdaptiveLimiter: per-host AIMD concurrency + token bucket (bulkhead isolated)       │
 │  • IdentityFactory: coherent UA+JA3/JA4+headers+viewport+locale+geo-proxy profiles     │
 └───┬──────────────────────────┬───────────────────────────┬───────────────────────────┘
     │  SOURCE-RACE / HEDGE (cheap confirmer fired first; expensive launched only on miss)│
     ▼                          ▼                           ▼
 ┌─────────────┐        ┌──────────────────┐      ┌────────────────────────────────────┐
 │ TIER 0      │        │ TIER 1–3 OSS     │      │ TIER 3–5 LICENSED BACKENDS         │
 │ API CONFIRM │        │ FETCH FABRIC     │      │ (one ScraperBackend interface)     │
 │ registries/ │        │ curl_cffi/wreq → │      │ ┌────────────────────────────────┐ │
 │ GLEIF/VIES/ │        │ cloudscraper/    │      │ │ LicensedSeatBroker (global Q)  │ │
 │ Apollo(gated│        │ Scrapling →      │      │ │ SF(4) · Sequentum(2+Cloud) ·   │ │
 │ behind cost)│        │ Botasaurus/      │      │ │ UiPath robots · Ranorex agents │ │
 └─────────────┘        │ Camoufox/        │      │ │ value/urgency priority + Cloud │ │
                        │ nodriver →       │      │ │ overflow w/ daily $ ceiling    │ │
                        │ FlareSolverr(opt)│      │ └────────────────────────────────┘ │
                        └────────┬─────────┘      └──────────────────┬─────────────────┘
                                 │ raw HTML/PDF/JSON over broker (backpressured)         │
                                 └──────────────────────┬───────────────────────────────┘
                                                        ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │   CPU/GPU PARSE FARM  (separate pools; bounded queue w/ producer backpressure)        │
 │   selectolax/lxml struct · XBRL/iXBRL parse (arelle) FAST PATH · PyMuPDF text →        │
 │   opencv → PaddleOCR/RapidOCR/Tesseract → Claude Vision (cascade)                      │
 │   NER LANGUAGE DISPATCHER: doc.lang → best model (KB/bert SE, FinBERT FI, DaCy DK,     │
 │   camembert FR, flair-german DE/AT, RobBERT NL, HuSpaCy HU, …) fallback xx_ent_wiki_sm │
 └────────────┬───────────────────────────────────────────────────────────────────────────┘
              ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │   FUSION + CONFIDENCE  (§7)  blocking → RapidFuzz → Splink → cluster → log-odds        │
 │   agreement fuse · freshness/decay half-lives · calibration · skip-the-scrape feedback │
 │   ─────► feeds back to router: need_expensive_fetch()? cheap_only / full / skip        │
 └────────────┬───────────────────────────────────────────────────────────────────────────┘
              ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │   CANONICAL STORE + OUTPUT API   per-field {value, confidence, last_verified,          │
 │   sources[], lawful_basis, method_badge}  ·  GDPR filter (provenance, DNC, erasure)    │
 │   Fabric/Postgres columnar + DuckDB/Spark resolution graph                             │
 └──────────────────────────────────────────────────────────────────────────────────────┘

 SHARED STATE (HA):  Redis (broker+cache+Bloom+rate+bandit) WITH AOF+replica+Sentinel;
 durable snapshots of bandit posteriors / method-memory / source-reliability → Postgres/Fabric.
 SCALE: docker-compose → k8s + KEDA on broker backlog; IO/browser/parse/GPU pools scale
 independently; stateless workers on spot/preemptible.
```

---

## 3. The Adaptive Self-Healing Engine

The engine is ~1500 lines of `asyncio` Python + Redis shared state, so a worker fleet shares one brain. Four cooperating subsystems: **MethodRouter** (which method), **FailureClassifier** (what broke), **AdaptiveLimiter** (how fast), **IdentityFactory** (who we look like) — plus durability glue.

### 3.1 Method tier ladder (cost-weighted; licensed tools are arms, not exceptions)

| Tier | Method | Repo / Tool | Cost wt | Solves | Throughput |
|------|--------|-------------|---------|--------|-----------|
| **-1** | **Bulk register ingest** | per-country bulk files (§8) + GLEIF | 0 | whole-country, no fetch | millions/load |
| 0 | **Cross-source API confirm** | Bolagsverket/brreg/PRH/CVR/Zefix/CH-API; GLEIF; VIES; Apollo (gated) | 1 | skips scrape | 1000s/s |
| 1 | **curl_cffi (impersonate)** | [lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) 5.9k | 2 | TLS/JA3/JA4, HTTP2 | 50–200 rps |
| 1 | **wreq-python** | [0x676e67/wreq-python](https://github.com/0x676e67/wreq-python) 1.4k | 2 | TLS + HTTP/3 | 50–200 rps |
| 2 | **cloudscraper** | [VeNoMouS/cloudscraper](https://github.com/VeNoMouS/cloudscraper) 6.6k | 4 | CF IUAM/JS-lite | 10–40 rps |
| 2 | **Scrapling** | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) 65.9k | 4 | rotation + fingerprints | 10–40 rps |
| 3 | **Botasaurus** | [omkarcloud/botasaurus](https://github.com/omkarcloud/botasaurus) 4.8k | 8 | CF JS, full browser | 2–8 rps |
| 3 | **Playwright + rebrowser** | [microsoft/playwright](https://github.com/microsoft/playwright) 65k + [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches) 1.4k | 8 | JS render, SPA | 2–8 rps |
| 3 | **Camoufox / nodriver** | [daijro/camoufox](https://github.com/daijro/camoufox) 9.5k, [ultrafunkamsterdam/nodriver](https://github.com/ultrafunkamsterdam/nodriver) 4.4k | 9 | DataDome/PX/Turnstile | 1–5 rps |
| 3.5 | **FlareSolverr pool** (optional, health-checked) | [FlareSolverr/FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) 14.4k | 10 | CF challenge as service | 0.5–2 rps |
| 4 | **Screaming Frog SEO Spider** | licensed (`--headless` CLI) | 12 | full-site crawl + bulk extract | site-batch |
| 4 | **Sequentum (Desktop+Cloud)** | licensed (`RunAgent.exe` / Cloud API) | 12 | anti-bot, paginated tables | agent-batch |
| 5 | **UiPath** | licensed (Orchestrator OData) | 16 | login/RPA + stateful gov UI | RPA-batch |
| 5 | **Ranorex** | licensed (`Suite.exe` / RanoreXPath) | 16 | desktop/Win32/Citrix, stubborn UI | RPA-batch |
| 6 | **2captcha / capsolver** | [2captcha-python](https://github.com/2captcha/2captcha-python) | 20 | hard CAPTCHA (pay last) | manual |

Promotion/demotion is **emergent**: once a licensed arm accumulates wins on a host where OSS only accumulates blocks, its Thompson-sampled reward overtakes them and the router returns it; hourly decay demotes a method that *stops* working.

### 3.2 MethodRouter — per-host bandit with cluster prior

**Algorithm:** Thompson Sampling with a Beta posterior per `(host, method)`, blended with a cost+latency penalty, decayed by γ=0.98/hr for non-stationarity. Library: [`fidelity/mabwiser`](https://github.com/fidelity/mabwiser) (`LearningPolicy.ThompsonSampling()`, swappable to `UCB1`/`EpsilonGreedy`/contextual `LinUCB`); thin in-Redis Beta sampler on the hot path.

```python
def sample_score(stat):                       # Thompson sample / cost-time
    p = random.betavariate(stat.alpha, stat.beta)
    cost_time = stat.cost_weight * (stat.ewma_latency_ms / 100.0)
    return p / max(cost_time, 0.1)
```

**Critic fix P1-5 — cluster prior + per-traffic decay (the long-tail unlock).** Most of 50M hosts are hit only a handful of times, so a flat (1,1) prior makes Thompson sampling effectively random and the cheapest-first intent is lost. We add a **hierarchical prior**: a host's sparse posterior backs off to a **cluster posterior keyed on `(WAF_vendor, TLD, page_type)`**. A brand-new `.se` site behind Cloudflare therefore *starts* at the empirically-best method for "`.se` + Cloudflare," not from scratch. Decay rate is tuned per traffic volume (slow decay for rarely-hit hosts so their evidence isn't forgotten between visits). This is implemented as `mabwiser` LinUCB with context features `[waf_vendor, tld, page_type, hour_of_day]`, or a two-level Beta where the cluster's (α,β) seeds the host prior.

**Critic fix P1-1 — real parallelism.** No `self._sem._value` private-poking and no single `asyncio.Lock` serialising every request on a host. Use [`aiolimiter`](https://github.com/mjpieters/aiolimiter) / `aiometer` leaky-bucket for rate; the bandit posterior is read as a **lock-free Redis sample** (or shared `mabwiser` state), not a per-worker dict that silently goes stale; cache TTL + invalidation are explicit so all fleet workers converge on a host's learned method.

### 3.3 FailureClassifier — precise block detection → deterministic remediation

Detection must be specific because each class has a different optimal remedy. Signals inspected: HTTP status (403/429/503/401/5xx); WAF fingerprints (`cf-mitigated`, `__cf_chl`, `Just a moment`, Turnstile; `x-datadome`/`captcha-delivery`; `_px`/`px-captcha`; Akamai `_abck`/`bm_sz`; Imperva `incap_ses`/`___utmvc`; `awswaf`); empty/shell render (200 but required selector absent, body < N bytes); honeypot (hidden links followed); poisoned/soft-ban (200 with wrong content, caught by cross-source disagreement + per-field plausibility — orgnr checksum, MX-valid email).

Remediation map (the auto-correct core):

```
RATE_LIMIT  → slow_down, keep identity            FORBIDDEN   → rotate identity, retry
CF_CHALLENGE→ cf_clearance-harvest→curl_cffi replay; camoufox; (FlareSolverr optional)
DATADOME    → camoufox + residential + slow        PERIMETERX → camoufox → nodriver
AKAMAI      → match JA3/JA4 → playwright_stealth    IMPERVA/AWS_WAF → botasaurus + rotate
EMPTY_RENDER→ escalate tier (browser)              HONEYPOT   → burn proxy + blacklist + rotate
CAPTCHA     → detect-first/avoid → OSS token harvest → licensed (Sequentum/UiPath) → pay last
SERVER_ERR  → jittered backoff + retry             POISONED   → rotate identity + cross-check
```

`"or_licensed"`: when a host repeatedly reaches CAPTCHA and even the OSS browser tier fails, remediation **promotes UiPath/Sequentum** for that host — the licensed tools become the survival path.

**Critic fix P2-2 — FlareSolverr is optional.** It is single-browser-per-request, slow, and frequently stale against current Cloudflare. Prefer the `cf_clearance`-harvest-then-curl_cffi-replay path (reuse exact IP+UA) and camoufox; FlareSolverr is a pooled, health-checked, *optional* rung, never a required one.

### 3.4 AdaptiveLimiter — AIMD congestion control per host

TCP-style **Additive-Increase / Multiplicative-Decrease** on per-host concurrency + per-host rate, with the *block signal* (not just latency) as controller input. On success while latency < target: `cwnd += 1`. On soft block (429): `cwnd *= 0.5`. On hard block (CF/DataDome): `cwnd *= 0.25`. Token bucket via `aiometer`/`pyrate-limiter`/`aiolimiter`. **Bulkhead isolation** (per-host limiter + circuit breaker) means LinkedIn collapsing to cwnd=1 never slows brreg. The sawtooth keeps us riding just under each host's block threshold — maximum tolerated speed, discovered live, no hand-tuning. Secondary governor: Scrapy-AutoThrottle latency-EWMA ceiling.

### 3.5 IdentityFactory — coherent fingerprint profiles, rotated whole

Detection works by **incoherence** (Chrome UA + Firefox JA3 + mismatched Accept-Language). We bind UA + full header set + TLS/JA3/JA4 + HTTP2 fingerprint + viewport + timezone/locale + geo-proxy into one `IdentityProfile` and rotate the *whole* profile. [`browserforge`](https://github.com/daijro/browserforge) Markov generator is the source of truth (it feeds Playwright/Camoufox too, so escalation reuses the same identity); curl_cffi `impersonate=` token is mapped from the profile's browser+version so the TLS layer matches the UA; [`intoli/user-agents`](https://github.com/intoli/user-agents) as UA pool; geo-proxy pinned per host (Swedish target → Nordic exit IP, sticky ≤1 h). `rotate_identity` mints a fresh profile + blacklists the burned one; `keep_identity` (429) reuses it and just waits.

**Critic fix P2-6:** browser+version are taken deterministically from the browserforge fingerprint and mapped to the impersonate token; a unit test asserts `UA-major-version == impersonate-version` for every generated identity (kills the `if False else 131` placeholder desync).

### 3.6 Self-healing, durability & degraded mode

- **Circuit breakers per host** ([`pybreaker`](https://github.com/danielfm/pybreaker)): after N consecutive hard-blocks the breaker opens, host parked on the adaptive-backoff table `[300,600,1800,3600]s`, effort spent elsewhere.
- **Retries** ([`tenacity`](https://github.com/jd/tenacity)): `wait_random_exponential(max=60), stop_after_attempt(5)` — jitter kills thundering-herd.
- **Dead-letter queue**: URLs that exhaust all tiers (incl. licensed) land in `tasks:dlq:{host}` with full trace, replayed when the host's posture relaxes.
- **Checkpoint/resume**: every URL state (`pending→inflight→done|dlq`) + last good method/identity persisted, so a crash/restart resumes exactly.
- **Critic fix P0-3 — Redis HA + durable learning + degraded mode.** Redis runs with AOF persistence + replica + Sentinel/Cluster. Bandit posteriors, method-memory and source-reliability are **snapshotted to Postgres/Fabric** periodically and reloaded on cold start, so learning survives a flush. Degraded mode: if Redis is unavailable, fall back to **conservative fixed concurrency + cheapest-method-first**, never fail open into aggressive defaults.
- **Critic fix P2-7 + P2-1 — suppress at intake.** National DNC (SE NIX, DE Robinsonliste, FR Bloctel, …) and erasure tombstones are checked at **intake**, so suppressed/erased contacts are never fetched, stored, or enriched. SMTP-RCPT probing is reserved for premium/low-volume from dedicated warmed IPs (never scraping proxies) to avoid Spamhaus/greylisting blacklisting.

---

## 4. Maximum-Speed / Parallelism Spec

### 4.1 The throughput identity

> **throughput = min(IO ceiling, CPU ceiling, politeness ceiling)** — and the first rule is: *the cheapest request is the one you never make.*

`asyncio for the wait, processes for the work, machines for the scale.` Pools never mix: IO-bound fetches on `asyncio` (one loop = 5k–20k sockets), CPU-bound parse/NER/OCR on `ProcessPool` (1/core), politeness on per-shard token buckets.

### 4.2 Bulk-Ingest-First (the largest lever — critic P0-1)

Before any socket opens, the **Bulk Ingestion Plane** downloads whole-country registers (§8) into `registry_bulk_index` + entity Bloom + canonical store, on each source's native cadence (brreg nightly, KBO/SIRENE daily, SE iXBRL weekly, CH Zefix daily, GLEIF daily; subscribe to Bolagsverket/brreg/CVR/Companies House **delta feeds** to stay fresh without re-pulling). The intake gate then answers **30–60 % of company-level fields with zero fetches**. Only the residual — contacts/email/phone registries don't carry, plus the no-bulk markets (IS, HU, IT, ES, PT, LU) — reaches the cascade.

### 4.3 Distributed work fabric (right tool per pool)

| Pool | Framework | Why |
|------|-----------|-----|
| IO fetch fleet | **Arq** (asyncio+Redis) | coroutine-native, 1 worker = thousands in-flight |
| CPU parse/NER/OCR | **Dramatiq** (proc actors, prefetch=1) | GPU affinity, rate-limit + backoff middleware |
| Stateful enrichment saga | **Temporal** | 6-step "company→officers→emails→verify" resumes at the failed step (don't re-spend an Apollo credit) |
| Change firehose | **Faust/Kafka** | replayable partitioned registry delta + vehicle-listing streams |

**Broker:** Redis default (broker+cache+Bloom+rate, HA per §3.6); RabbitMQ where true message-priority + acks matter (LinkedIn risk-budgeted work); Kafka only for the streaming change-feed lane.

**Sharding + fair scheduling:** shard key = `(country, registrable_domain)`, each shard its own stream + token bucket; global dispatcher pulls **round-robin across active shards** (fair share) so a 2M-row `.se` domain can't starve a 5k-row `.fi` registry. Priority lanes urgent/normal/batch drained 8:3:1.

### 4.4 Source-racing / hedged requests (critic P1-2 corrected)

The headline differentiator — but **staggered hedging is the default, not parallel-everything**:

```python
async def hedged(entity):
    cheap = asyncio.gather(registry_api(entity), cached_lookup(entity), bulk_index(entity))
    done, _ = await asyncio.wait({cheap}, timeout=0.4)
    if done and (r := pick_best(done)) and is_acceptable(r):
        return r                              # 70–85% end here, ~80 ms, FREE
    return await resolve_with_scrape(entity)  # only the hard tail pays for a browser
```

- **Never put a PAID source (Apollo) in the initial wave.** It is gated behind the same cost-aware counter as paid proxies/CAPTCHA, fired only after free/cheap miss — racing a paid credit against a free registry would burn credits we didn't need.
- **`is_acceptable()` = the confidence gate.** Two cheap sources agreeing → cancel/skip the expensive one (speed). Two cheap sources disagreeing → escalate a browser to break the tie (coverage). One control flow, both goals.
- **Cancellation caveat:** `task.cancel()` doesn't free an in-flight socket/Chromium tab instantly, so hedging (don't launch the expensive arm until the cheap deadline passes) is what actually saves bandwidth/RAM — not racing-then-cancelling.

### 4.5 Caching + dedup-before-fetch

HTTP cache (`hishel`, ETag/Last-Modified, 20–50 % on re-runs); negative cache (known-404/blocked); content-hash dedup (`xxhash`/`blake3`, 10–25 %); **entity Bloom filter** (`datasketch`/Redis, 18–30 %); near-dup MinHash-LSH; DNS cache (`aiodns`). `304 Not Modified` and Wayback-CDX/sitemap-`lastmod` diffs make most re-checks free.

### 4.6 Backpressure both ways (critic P1-4)

Raw bytes are handed to the CPU/GPU pool over the broker so the fetch loop never stalls on a 200 ms parse — **and** a **bounded parse queue with producer backpressure** closes the loop the other way: when the `parse` stream depth exceeds a high-water mark, the IO limiter's `acquire()` blocks (or the scheduler de-prioritises new fetches) until it drains, so throughput is governed by the *slowest necessary* stage and Redis never OOMs on freshly-scraped HTML.

### 4.7 GPU/CPU batching

NER: `spaCy nlp.pipe(batch_size=256, n_process=N)` — 5–20× a Python loop. OCR tiering: **RapidOCR** (ONNX, 1000+ img/s) for volume → **PaddleOCR** (96.3 %) for accuracy → **Tesseract** CPU fallback → Claude Vision last. GPU pod = Dramatiq actor, `prefetch=1`, micro-batch up to 512 images or 50 ms.

### 4.8 Horizontal scale

docker-compose (dev/≤2M/day) → k8s with **KEDA scaling on broker backlog** (queue depth, not CPU — IO workers sit at 30 % CPU while 5k sockets wait). IO/browser/parse/GPU pools scale on independent triggers. Stateless idempotent workers on **spot/preemptible** (60–90 % discount; killed worker drops its lease, broker redelivers); KEDA scales to zero in quiet windows.

### 4.9 Throughput math to 50M

Per-worker rates: Arq IO cheap-API/registry (H2 reuse) **40–120 ent/s**; curl_cffi WAF site **8–25 ent/s**; Playwright (6 ctx, assets blocked) **0.6–1.5 ent/s**; spaCy parse+NER **150–500 docs/s**; PaddleOCR GPU batch **300–1000 img/s**.

Realistic blended mix *after Bulk-Ingest + dedup remove ~50 %*: of the remaining fetches ~70 % cheap API/registry, ~25 % HTTP/TLS, ~5 % browser → **≈18 resolved entities/s/worker** sustained = **1.55M entities/day/worker**.

| Target | Window | IO workers @18/s | Companion pools |
|--------|--------|------------------|-----------------|
| 1M | 1 day | **1** (finishes ~15 h; run 2–3 for SLA) | — |
| 10M | 1 day | **7** (run 10 for retries/skew) | — |
| 50M | 1 day | **33** | + 6 browser pods (6 ctx) + 2 CPU pods + 1 GPU pod |
| 50M | 7 days | **5** | low-cost steady backfill |

**50M companies/contacts in one day ≈ 33 IO workers + 6 browser pods + 2 CPU pods + 1 GPU pod**, all stateless on spot, KEDA-scaled on backlog. Scaling is **linear in IO workers** until a *shared* ceiling (Redis ~100k msg/s, proxy egress bandwidth, a registry's global quota) — then shard the broker (Redis Cluster / Kafka partitions) and add proxy vendors. Compute is never the wall; politeness budget + proxy bandwidth are.

---

## 5. OSS Combination Matrix (situation → ordered chain → fallback)

Governing principle: climb the cost ladder, stop at the first rung that returns a valid payload, remember the winning rung per `(domain, page-type)`, start next time at known-good-minus-one (probe one cheaper rung occasionally to detect a defence downgrade), and fire the cheap confirmer in parallel so the slow scrape can be cancelled.

| # | Situation (signal) | Ordered tool chain (stop at first success) | Speed/page | Conc. | Fallback |
|---|---|---|---|---|---|
| 1 | Static HTML, content in body | `curl_cffi(impersonate)` → `selectolax` CSS | 20–80 ms | 50–200 | row 5 |
| 2 | XPath/namespaces/sitemaps | `curl_cffi` → `lxml.html`/`etree` + `cssselect` | 60–120 ms | 50–150 | selectolax |
| 3 | `__NEXT_DATA__`/`__NUXT__`/inline state | `curl_cffi` → pull `<script>` → `orjson.loads` | 25–90 ms | 100–200 | row 4 |
| 4 | GraphQL/REST XHR behind SPA | harvest route once (mitmproxy) → replay `curl_cffi` + captured headers/persistedQuery | 30–120 ms | 80–150 | row 8 |
| 5 | Soft block (403/429/503, `cf-mitigated`) | `cloudscraper` → (FlareSolverr opt) → `curl_cffi` + fresh proxy/UA | 1–5 s | 10–40 | row 6 |
| 6 | CF Turnstile / managed challenge | `cf_clearance`-harvest → `curl_cffi` replay (same IP+UA) → `camoufox` → `nodriver` → `botasaurus` | 2–8 s | 4–12 | **Sequentum** (row 19) |
| 7 | DataDome / PerimeterX / Akamai | `camoufox` (best TLS+JS coherence) → `nodriver`+rebrowser → `botasaurus` → residential ISP proxy | 3–10 s | 3–8 | Sequentum Cloud |
| 8 | JS-rendered SPA (empty body) | `nodriver` → `undetected-playwright` → `camoufox` → puppeteer-extra+stealth | 2–6 s | 6–16 | block resources → row 19 |
| 9 | Infinite scroll / lazy | headless + scroll → **intercept XHR** → switch to row 4 | 3–8 s | 6–12 | paginate via API params |
| 10 | Login / cookie-walled (registries) | headless login once → export storage_state → replay reads with `curl_cffi`+cookies | 2 s + 50 ms/read | 1→50 | rotate identity, re-login |
| 11 | PDF / annual report | `PyMuPDF` fast text → `pdfplumber` tables → OCR (row 13) | 50–300 ms | 20–50 | OCR |
| 11b | **XBRL/iXBRL filing** (critic P1-7) | **`arelle`/iXBRL parse → structured facts (NO OCR)** | <50 ms | 50+ | treat as bulk if whole-country |
| 12 | Image/scan needing text | `PaddleOCR` → `docTR`/`RapidOCR` (ONNX) → `Tesseract 5` → Claude Vision | 100–800 ms | 4–8 GPU | Claude Vision |
| 13 | Low-quality scan | `opencv` deskew/denoise/binarize/upscale → row 12 | +30–80 ms | 4–8 | noteshrink → retry |
| 14 | Entity extraction from messy text | **language-routed NER** (§4.7 dispatcher) → `GLiNER`/transformers → Claude API hard cases | 20 ms/doc | 8–32 | Claude API |
| 15 | Structured fields from a page | CSS/XPath rules → `selectolax` → NER only on residual free-text | <5 ms | 100+ | NER |
| 16 | Email discovery + verify | pattern infer → MX (`dnspython`) → catch-all detect → cross-source confirm; SMTP-RCPT premium-only | 5 ms / 150 ms MX | 20–50 | accept syntactic+MX |
| 17 | Dedup / entity resolution | `RapidFuzz` blocking → `datasketch` MinHash/LSH → `Splink`/`dedupe` | 10k pairs/s | CPU | RapidFuzz token_set |
| 18 | CAPTCHA presented | **avoid first** (back off, rotate) → OSS Turnstile (cf-clearance-scraper, Boterdrop) → 2captcha/capsolver | varies | low | paid solver |
| 19 | OSS exhausted (JS+TLS+behavioral) | **Sequentum Desktop** → **Sequentum Cloud** → **UiPath** (portal flows) → **Ranorex** (Win32/Citrix) | 5–30 s | seat pool | manual queue |
| 20 | Bulk site crawl / sitemap | **Screaming Frog** (list+spider, custom extraction) → feed URL frontier to rows 1–8 | 100–500 URL/s | n/a | sitemap + curl_cffi |

**Anti-bot decision order (sense before you spend):** `Server: cloudflare`+`cf-mitigated`→cloudscraper→(FlareSolverr opt); Turnstile `cf-turnstile`→token-harvest→camoufox→botasaurus; `x-datadome`→camoufox→nodriver+rebrowser→ISP; `_px`→camoufox→nodriver→Sequentum; Akamai `_abck`→curl_cffi correct JA3→camoufox→Sequentum; Incapsula→cloudscraper→camoufox.

**Three load-bearing chains** (full code in `arch_oss-combo-matrix.md`): **Chain A** curl_cffi+selectolax with `__NEXT_DATA__` shortcut (selectolax ~2–5 ms vs BS4 ~40–150 ms = 10–30×, what lets row 1 run at 100–200 workers); **Chain B** adaptive escalation with method-memory + speculative confirmer (cancel-on-confirm); **Chain C** fitz→opencv→Paddle/docTR/Tesseract→spaCy.pipe→Claude (PDF text first, OCR only no-text pages, single batched NER pass).

**Free proxy fabric:** union of `TheSpeedX/PROXY-List`, `monosans/proxy-list`, `proxifly/free-proxy-list`, `clarketm/proxy-list` + `ProxyBroker2` + Tor via `stem`; self-healing health-check; sticky per-domain ≤1 h; cost-aware paid ISP/residential escalation only after N free-tier failures on that domain. **Critic P2-3:** score proxies on **per-`(domain,proxy)`** success (a proxy good for brreg may be burned on allabolag), feeding the same metrics store; health-check against rotating self-hosted echo endpoints, not just `httpbin.org`.

---

## 6. Licensed-Tool Orchestration Spec

All four licensed tools implement **one `ScraperBackend` interface** so the router sees a uniform method list with live cost/speed/success metrics and an `acquire()`/`release()` contract against a constrained seat pool. They are **last by cost, promoted by win-rate** — spent only on the residual targets no cheaper method resolved.

### 6.1 When each wins

| Tool | Headless mechanism | Wins over OSS when… |
|------|-------------------|---------------------|
| **Screaming Frog SEO Spider** | `ScreamingFrogSEOSpiderCli.exe --headless`, DATABASE storage | discover + crawl an entire company website (100s–1000s URLs) and bulk-extract emails/phones/people via CSS/XPath/Regex custom extraction in one pass; the URL-frontier front-end for every large site |
| **Sequentum (Desktop+Cloud)** | `RunAgent.exe` CLI / Cloud REST | JS-heavy, anti-bot, paginated tables (registries, directories, search portals) where OSS hits CAPTCHA/CF; built-in CAPTCHA + CF handling, stateful pagination, `ContinueAndRetryErrors` self-healing |
| **UiPath Orchestrator** | OData REST → unattended robots + queues | login + multi-step RPA, stateful gov-registry UI (Bolagsverket interactive flows, BankID-gated portals, ES sede checkout, PT publicacoes VIEWSTATE postbacks) — deterministic, audited, exactly-once |
| **Ranorex** | `Suite.exe` / RanoreXPath object recognition | stubborn web UI where DOM selectors break, or native Windows/Citrix thick-client apps (legacy registry viewers) with no web surface |

### 6.2 Verified CLI / API surfaces

- **Screaming Frog:** `--headless --crawl <url>` | `--crawl-list <file>` | `--config <.seospiderconfig>` | `--output-folder` | `--export-tabs "Custom Extraction:All"` | `--bulk-export` | `--export-format csv|xlsx` | `--save-crawl` (paid) | `--overwrite --timestamped-output`. Always DATABASE storage for big crawls. One interactive EULA/license/storage acceptance per machine, then `--headless` unattended. Shard a list into N lanes, 1 process per lane, distinct `--output-folder`. The contact-mining `contacts.seospiderconfig` defines email regex, Nordic phone regex, `mailto:`/`tel:` XPath, and restricts includes to `/(om-oss|about|team|kontakt|contact|medarbetare|staff|ledning|management)/i`.
- **Sequentum Desktop:** `RunAgent.exe <agent> [-param val] no_ui run_method ContinueAndRetryErrors env_ Prod`. **Exit codes drive routing:** `0`=success, `3/4`=partial (re-enqueue residual via `ContinueAndRetryErrors`), `5`=export-sink problem (retry export only), `6/8/22`=**seat contention** (back off, requeue to free seat — *not* a target failure), `9/13`=bad agent/params (alert, never blind-retry). **Sequentum Cloud:** `POST /api/v1/agent/{id}/start` with `parallelism` + `isRunSynchronously`; poll `/runs`, download via `/run/{runId}/file/{fileId}/download`.
- **UiPath:** OAuth2 bearer + `X-UIPATH-OrganizationUnitId`. Pattern: `AddQueueItem` (one company/lookup = one item) → `StartJobs` with `Strategy: ModernJobsCount, JobsCount: k` (the parallel fan-out) → poll `QueueItems?$filter=Status eq 'Successful'`. Queues give exactly-once + retry.
- **Ranorex:** `Suite.exe /ts:<.rxtst> /tc:<name> /rc:<config> /pa:"InputCsv=..." /pa:"OutDir=..." /rl:Warn /zr`. Exit `0`=success, `-1`=failure. Parallelism is per-machine; scale = multiple agent VMs, one seat each.

### 6.3 Seat-limited resource pools + escalation order (critic P0-5)

Seats are scarce (SF=4, Sequentum desktop=2, UiPath/Ranorex a handful) and at 50M scale the hard-target tail vastly exceeds seat throughput. The fix:

- **Single `LicensedSeatBroker`** with a **global priority queue across all four tools**: targets carry `value`/`urgency`; the broker allocates the highest-value target to the best-fit *free* seat across all backends (a cross-backend global seat view, so one scarce seat class can be traded against another).
- **Explicit Cloud-overflow policy:** when desktop seats are full **AND** backlog age > threshold **AND** target value > cost-of-cloud-call → spill to Sequentum Cloud / UiPath cloud robots, under a **per-day spend ceiling**. When even Cloud is saturated, targets DLQ with a clear "seat-starved" reason (not silent waiting).
- **Seat saturation is a first-class metric** that both KEDA-style autoscaling and the `value` threshold react to — raise the "is this target worth a seat?" bar when seats are scarce.
- **Expected-utility routing:** `EU(b,target) = P_success(b,domain)·value(target) − (cost(b)+latency_penalty(b))·urgency − seat_pressure(b)`. `P_success` is Beta-Bernoulli per `(backend,domain)`, converging from a static prior to observed rate — so the first CF challenge on a domain collapses every OSS tier's `P_success` and lifts Sequentum/UiPath automatically.

```
Tier 0  curl_cffi / wreq                 (static HTML, JSON)            ∞ seats
Tier 1  Botasaurus / Camoufox / Scrapling(JS render, light stealth)    ∞ seats
Tier 2  FlareSolverr / browser farm      (CF JS, optional)             pool-bounded
Tier 3  Screaming Frog --headless        (full-site bulk extraction)   N crawl seats
Tier 4  Sequentum RunAgent / Cloud       (anti-bot, paginated tables)  desktop + Cloud
Tier 5  UiPath StartJobs / Ranorex exe   (login-RPA, gov UI, native)   robot/agent seats
```

A licensed job is dispatched exactly like an OSS rung — same work queue, same method-memory, same per-domain circuit breaker — so the router can learn "this domain always needs Sequentum" and route straight there, skipping the wasted OSS climb. Every `FetchResult` (exit code, block signal, latency, rows, cost) feeds the same per-`(backend,domain)` store as the free stack.

---

## 7. Cross-Border Data-Fusion + Confidence + GDPR Spec

The trust engine turns noisy, contradictory, multi-language claims into **one canonical record per real-world entity, with a defensible calibrated confidence and full provenance on every field**. The competitive wedge is **calibrated honesty**: a field that says `confidence: 0.83` must be correct ~83 % of the time (measured, re-fit quarterly) — the claim Apollo (claims 97 %, delivers 65–70 %) and Cognism (98 % on 2.3 % of its DB) cannot make.

### 7.1 Canonical entity model (6 types)

Six entity types, each with an immutable UUIDv7 surrogate + natural keys. **Company** carries `lei`, `reg_ids[]` (polymorphic `RegId`), `primary_country`, `legal_name(_normalized)`, `legal_form`, `status`, `vat_id`, `domains[]`, `registered_address`, `sni_nace`, `size_band`, `parent_company_uid`, `_provenance`. Plus **person**, **role** (time-bounded person↔company edge with `valid_from/to`), **contact_point** (email/phone, `value_e164`/`value_email`, `validation`), **website** (`url_canonical`, `etld_plus_one`, `liveness`, `cms/tech`), **vehicle**.

### 7.2 Cross-border keying

- **Within a country:** the checksum-validated national reg-id is the deterministic merge key (two claims with the same Luhn-valid `SE_ORGNR` are the same company, period).
- **Across borders:** **GLEIF LEI** is the bridge (`LEI ↔ national reg-id` for ~2.5M entities, free daily). Where LEI is absent (most SMEs), fall back to probabilistic resolution over `legal_name_normalized + registered_address + domain + VAT`. **VIES VAT** is a second cross-border anchor + cheap active-status confirm.
- **Critic fix P0-4 / NL caveat:** `NL_KVK` is **not** a free deterministic key — the free KVK bulk is anonymised (no KVK number, no name). For NL, deterministic keying needs the paid KVK API or falls to LEI/probabilistic. The keying spec flags NL accordingly.
- **Vehicle:** VIN is the global natural key (17-char, position-9 check digit); national plate is country-scoped + mutable (reassigned), a weak key only within `(plate, country, observed_window)`.

### 7.3 Entity resolution at scale

**Blocking** (avoid O(N²)): multiple union keys — `reg:{scheme}:{value_norm}`, `lei:{lei}`, `dom:{etld+1}`, phonetic `nm:{country}:metaphone(sorted_tokens)`, `geo:{country}:{postcode[:3]}:{name[:5]}` — block size 2–50. **Diacritics:** language-aware expansions (DE `ä→ae`, SV `ä→a`, NO/DA `ø→o`) *plus* NFKD fold, match on whichever scores higher; `unidecode` for non-Latin; jellyfish Metaphone/NYSIIS safety net. **Legal-form normalisation** per jurisdiction (strip for comparison, keep for storage). **Pairwise:** Stage A `RapidFuzz token_sort_ratio` (µs/comparison) filters; Stage B `Splink` (Fellegi-Sunter, EM-learned m/u probabilities, pushed into DuckDB/Spark) for the ambiguous 0.55–0.92 band; deterministic short-circuit `reg-id or LEI match → 1.0`. **Clustering:** connected components with a Splink cohesion check to prevent merge-everything chains.

### 7.4 Multi-source agreement scoring (the differentiator)

Each source has a **measured reliability `r_s`** per field-type per country (Bolagsverket/legal_name/SE→0.99; website_scrape/email/SE→0.74; email_pattern_inference→0.55; merinfo/vehicle.owner/SE→0.85). Fusion is **log-odds**: each agreeing source contributes `freshness · log(r_s/(1−r_s))`, disagreeing sources contribute half-weight negative evidence, prior = `log(0.05/0.95)`. Two independent r=0.75 sources agreeing → ~0.90 (agreement compounds); a registry r=0.99 single-handedly anchors; a guessed r=0.55 email stays low. **Validation as a pseudo-source:** MX/SMTP, libphonenumber, website-liveness injected with their own reliability — a scraped email that also passes MX gets a second agreeing signal; one that fails MX gets a strong contradiction. Catch-all MX (`r≈0.6`) is weighted below SMTP-RCPT confirm (`r≈0.9`), and the badge surfaces *which* check passed.

### 7.5 Freshness + decay

Time is a first-class confidence input. Field-specific half-lives: `reg_id` 3650 d, `legal_name` 1825 d, `registered_address` 730 d, `email` 400 d (~22 %/yr), `phone_mobile` 500 d, `role.title` 270 d, `website.liveness` 30 d, `vehicle.owner` 365 d. `freshness = 0.5^(age/half_life)`. Re-verification queue triggers when `freshness < 0.6` AND the field matters; cheap re-checks first (registry diff, MX re-ping, Wayback-CDX/sitemap-`lastmod` diff, ETag `304`) before expensive re-scrape.

### 7.6 Calibration (the honesty guarantee) — critic P2-4

`calibrate()` maps raw fused probabilities to empirically-observed correctness via **isotonic regression** against ground truth, re-fit quarterly, with published reliability diagrams. Cold-start honesty: **bootstrap calibration only from the registry-confirmable subset; explicitly mark email/phone confidence as *uncalibrated* until bounce/answer feedback accrues, and do not publish a calibrated number for fields with no ground truth yet.**

### 7.7 Skip-the-scrape arbitration (speed via fusion)

Before dispatching any expensive method the router asks the fusion layer `need_expensive_fetch(entity, field, target_conf=0.85)`: if current confidence ≥ target and fresh → **skip**; if a cheap confirm would push it over → **cheap_only**; else **full**. The fusion layer is thus also the cost/throughput governor.

### 7.8 GDPR / compliance by design (the EU moat) — critic P0-4 enforced

- **Field-level provenance, non-optional:** every value carries `{source_id, source_url, collected_at, method, lawful_basis, lia_ref, jurisdiction}`. A field with no lawful basis cannot be emitted — the output API filters it.
- **Lawful-basis tagging:** public registries → `public_register`/`legal_obligation`; B2B contact (work email/direct dial/role) → `legitimate_interest` backed by a documented LIA referenced in `lia_ref`; **DE/FR stricter** (UWG+GDPR / CNIL) → shorter re-consent/suppression windows, excluded from certain bulk exports unless the consumer attests B2B purpose; SE personnummer & equivalents **never** stored for marketing.
- **Per-source reuse restriction (new, critic P0-4):** a `(source,country)` policy table tags e.g. BE KBO contact fields and DE directory data with `reuse=no_direct_marketing`; the output `lawful_basis` filter enforces it. Distinct from per-country DNC.
- **DNC/suppression** (DE Robinsonliste, FR Bloctel, SE NIX, …) loaded as hard filters, checked at **intake** (critic P2-7) and again at output; matched `cp_uid` flagged `suppressed=true`, withheld from contactable exports, retained in the graph for resolution only.
- **Art. 14 notification** plumbing per `person_uid` on first ingest; **right-to-erasure** tombstoning purges values, keeps a hash to block re-ingestion, propagates to exports.

### 7.9 Output contract

Every field is `{value, confidence, last_verified, sources[], lawful_basis, method_badge}` — no bare values; `method_badge` spells out which validation passed (vs Apollo's opaque "verified"); suppressed fields auto-withheld from `?contactable=true`; `needs_reverify[]` exposed; bulk/stream endpoints (`POST /v1/resolve`, `GET /v1/changes?since=`) mirror the envelope. Canonical store columnar in Fabric/Postgres + JSONB provenance sidecar; resolution graph in DuckDB/Spark.

---

## 8. The 20-Country Source Table (verifier-corrected)

Confidence flag is the **verifier's** verdict (✅ verified / ⚠️ likely-or-caveated). Corrections from the `verify_*.md` files are applied inline.

### 8.1 Company registry / access / cost / financials

| # | Country | Company registry | Access method | Free? | Board/UBO | Financials | Conf. |
|---|---------|------------------|---------------|-------|-----------|-----------|-------|
| 1 | **Sweden** | Bolagsverket | bulkfil.zip + API v4.4 (free, "valuable datasets" since 3 Feb 2025) | ✅ free core | directors API; UBO "verklig huvudman" gated (CJEU) | **iXBRL weekly bulk free**, 2020→, mandatory all AB FY>31 Dec 2025 | ✅ |
| 2 | **Norway** | Brønnøysund Enhetsreg. | `/api/enheter/lastned` JSON/CSV/xlsx, nightly (NLOD) | ✅ free | `/api/roller/totalbestand` free; PID via Maskinporten | Regnskapsregisteret **open key-figures API (free)** | ✅ |
| 3 | **Denmark** | CVR / Erhvervsstyrelsen | S2S Elasticsearch `distribution.virk.dk/cvr-permanent` (free, register via `cvrselvbetjening@erst.dk`, ~2 wk) | ✅ free | participants + reelle ejere in bulk | XBRL/PDF free; `cvrapi.dk` lighter free alt | ✅ |
| 4 | **Finland** | PRH Trade Register / YTJ | all-companies JSON bulk + API v3 (free, CC-BY, daily, ~300 q/min) | ✅ free | board via register; edunsaajat restricted | iXBRL `xbrl` v3 service (subset) free | ✅ |
| 5 | **Iceland** | Fyrirtækjaskrá (Skatturinn) | **scrape-only** (no open API/bulk) | ⚠️ free-ish | UBO via per-company web lookup | Ársreikningaskrá per-doc free download | ⚠️ likely |
| 6 | **Germany** | Handelsregister | **portal scrape-only, ≤60 req/hr, §§303a/b StGB criminal**; use **OffeneRegister bulk = ~2019 SNAPSHOT** + bundesAPI deltas | ⚠️ free (stale) | officers in OffeneRegister; Transparenzregister UBO gated (legit-interest) | Unternehmensregister XBRL, search free, **~€1/doc**; no free bulk | ✅ |
| 7 | **Austria** | Firmenbuch (JustizOnline) | **HVD bulk = identity fields only** (data.gv.at, CC-BY); full extracts paid via billing agents | ⚠️ free core only | Funktionäre paid extract; **WiEReG UBO ~€3/extract**, legit-interest | Jahresabschluss paid per-doc; no free bulk | ✅ |
| 8 | **Switzerland** | Zefix (FCRO, 26 cantons) | **free REST API + opendata.swiss daily + LINDAS SPARQL**; heavy programmatic use account-gated (free, email `zefix@bj.admin.ch`) | ✅ free | directors/auditors free via API/LINDAS; **no public UBO register** (LETA non-public, in force H2 2026) | **no public SME accounts** (structural gap); SOGC/SHAB statutory only | ✅ |
| 9 | **Netherlands** | KVK Handelsregister | **free open dataset is ANONYMISED** (no name, no KVK nr, 2-digit postcode, BV/NV only); **names require paid KVK API** | ⚠️ paid for names | directors paid API; UBO restricted (15 Jul 2025), UBO API ~Q2 2026 | KVK Financial Statements open dataset (SBR/XBRL) free | ✅ |
| 10 | **Belgium** | KBO/BCE (FPS Economy) | **full open data DAILY since 3 Nov 2025** + delta, CSV via portal/SFTP (free, register) | ✅ free | directors via KBO public-search scrape; UBO gated | **NBB CBSO** API XBRL/JSON/CSV (JSON since 4 Apr 2022) free per-doc | ✅ |
| 11 | **Luxembourg** | RCS (LBR) | free basic search + free PDF docs; **no confirmed free bulk/open API** (keep uncertain) | ⚠️ free per-doc | directors on free extract; RBE UBO gated | annual accounts free download (eCDF/PCN); no bulk API | ⚠️ likely |
| 12 | **France** | INSEE SIRENE + INPI RNE | **SIRENE free bulk on data.gouv.fr (Parquet since Jun 2025, CSV ends 1 Jan 2027)** + daily delta; INPI RNE free API+SFTP; **API Recherche d'Entreprises** no-auth (7 req/s/IP) | ✅ free | dirigeants bulk-free (INPI); UBO gated | **INPI "Actes et bilans" free via data.inpi.fr** (not the gated entreprise.api.gouv.fr); SME comptes confidentiels excluded | ✅ |
| 13 | **Italy** | Registro Imprese (InfoCamere) | **free fields = name/office/PEC/activity/status; rest paid** (Visura ≈€6–12 via Telemaco/ABDO); no free bulk | ⚠️ free core only | directors/shareholders in paid Visura; **UBO public access SUSPENDED** (D.Lgs 210/2025, in force 9 Jan 2026) | Bilanci XBRL ≈€6–12/doc; no free bulk | ✅ |
| 14 | **Spain** | Registro Mercantil (CORPME, 52 prov.) | **BOE BORME open-data API** `boe.es/datosabiertos/api/borme/sumario/{YYYYMMDD}` (XML/JSON, free) = spine; **opendata.registradores.org is ALSO a free incorporations/closures microdata feed** (WAF-protected); sede notes <€5 | ⚠️ free events; rest paid | directors in BORME acts (free); Titularidades Reales UBO paid | Cuentas anuales per-doc small fee; new models 26 May 2025; no free bulk | ✅ |
| 15 | **Portugal** | Registo Comercial (IRN) | **free MJ publicacoes.mj.pt search** (events; ASP.NET VIEWSTATE) + DRE gazette feed; no public API/bulk | ⚠️ free events only | **MJ free layer surfaces shareholders+directors more than expected**; RCBE UBO gated | IES legally public but **no free bulk** (Racius/Informa paid); BPLIM for accredited researchers | ⚠️ likely |
| 16 | **UK** | Companies House | **free API (key) + free monthly bulk CSV** (`en_output.html`, within 5 working days, carries "will not be supported" notice) | ✅ free | officers via API; **PSC free daily bulk JSON** | **Accounts Data Product free** (iXBRL, daily 60-day + historic to 2008) | ✅ |
| 17 | **Ireland** | CRO Open Data Portal | **daily bulk CSV + API**, CC-BY-4.0 (current + dissolved) | ✅ free | officers via CRO; **RBO UBO restricted** (no legit-interest approvals reported) | Financial Statements dataset free; fuller docs CORE pay-per-call | ✅ |
| 18 | **Poland** | KRS + CEIDG + REGON | KRS open REST API (per-entity, throttled); **REGON BIR1 = SOAP, key-by-email**; CEIDG warehouse API needs identity verification | ✅ free (gated access) | directors in KRS excerpt; **CRBR UBO public access ENDS 1 Jul 2026** (→restricted) | RDF repository free per-company (XML+PDF) | ✅ |
| 19 | **Czech Rep.** | ARES (MoF) | **free REST API + open-data XML bulk** (`dataor.justice.cz`), daily | ✅ free | directors in Commercial Register; **ESM UBO public access ENDED 17 Dec 2025** | Sbírka listin free PDFs per company | ✅ |
| 20 | **Hungary** | e-Cégjegyzék (MoJ) | free basic per-company lookup; **no free bulk/API → paid feed required** (OPTEN, companyapi.hu) | ⚠️ paid for bulk | directors paid; UBO gated | **e-Beszámoló free** (all companies' annual statements, PDF/XML) | ⚠️ likely |

### 8.2 Vehicle registry / language-NER / bypass (verifier-corrected)

| # | Country | Vehicle registry | Owner data? | Technical/fleet open? | NER model | Bypass note |
|---|---------|------------------|-------------|----------------------|-----------|-------------|
| 1 | SE | Transportstyrelsen Vägtrafikreg. | paid FTP (live); reseller biluppgifter/merinfo | **open feed is HISTORICAL annual snapshot** (tsopendata, not live) | `KB/bert-base-swedish-cased-ner` / `sv_core_news_lg` | API/file endpoints open; **landing HTML is CAPTCHA-gated** |
| 2 | NO | Statens vegvesen Autosys | **no owner** | tech API, key, 50k calls/day | `NbAiLab/nb-bert-base-ner` / `nb_core_news_lg` | clean API |
| 3 | DK | Motorregister (DMR) | **public single lookup shows owner/user; no bulk** | per-vehicle + B2B SOAP (cert) | **DaCy large** / `da_core_news_lg` | clean |
| 4 | FI | Traficom | anonymised (no owner) | **fully open ZIP-CSV** (~31.3.2026, ~5.15M rows, CC-BY 4.0) | `TurkuNLP/bert-base-finnish-cased-v1` (FinBERT) | clean |
| 5 | IS | Samgöngustofa Ökutækjaskrá | gated (uncertain) | no confirmed open bulk | `mideind/IceBERT`-NER / `nbailab-base-ner-scandi` | scrape island.is |
| 6 | DE | KBA ZFZR | **restricted by law (§§35–39 StVG)** | aggregate stats + type-approval only | `flair/ner-german-large` / `de_core_news_lg` | **never bulk-scrape Handelsregister** |
| 7 | AT | VVO/Statistik Austria | no public per-owner | aggregate (Kfz-Bestand/Zulassungen, CC-BY) | `flair/ner-german-large` / `de_core_news_lg` | HVD static CKAN → high parallelism |
| 8 | CH | ASTRA IVZ | **no owner** | **open** `opendata.astra.admin.ch/ivzod` | xlm-roberta / `wikineural-multilingual-ner` (de+fr+it) | Zefix/LINDAS official; search.ch tel 1000/mo |
| 9 | NL | **RDW (best in EU)** | excluded (privacy) | **fully open, no key, Socrata SODA, `Gekentekende_voertuigen` m9d7-ebf2** | `nl_core_news_lg` / RobBERT | open portals no WAF |
| 10 | BE | DIV (FPS Mobility) | **not public** | Statbel/FPS aggregate only | `nl_core_news_lg` + `fr_core_news_lg` route | KBO public-search scrape rate-limited |
| 11 | LU | SNCA | no owner | **"Parc Automobile" data.public.lu, CC0, monthly = PER-VEHICLE** (latest 4 Jun 2026, 224 files) | `fr_core_news_lg` + `de_core_news_lg` | RCS scrape; per-doc |
| 12 | FR | SIV (Min. Interior) | **not public**; HistoVec free to current owner only | fleet/immatriculation stats on data.gouv.fr | `Jean-Baptiste/camembert-ner` / `fr_core_news_lg` | open portals/SFTP no WAF |
| 13 | IT | PRA (ACI) | paid (Visurenet) | **open** ACI LOD (CC-BY) + MIT "Parco Circolante" | `it_core_news_lg` (**NER F≈0.884**, not 0.91) / `it_core_news_trf` | free search light WAF; Telemaco paid |
| 14 | ES | DGT | **legit-interest gated** (MATRABA tightened 1 Feb 2025) | **open monthly microdata (anonymised)** | `PlanTL-GOB-ES/roberta-large-bne-capitel-ner` / `es_core_news_lg` (~0.90) | **CORPME sede/opendata = WAF, do NOT naive-scrape**; use BOE BORME API + UiPath |
| 15 | PT | IMT | **not open** | no IMT open dataset (ACAP/INE aggregates) | `pt_core_news_lg` (BR-trained, watch drift) / BERTimbau | publicacoes.mj.pt = VIEWSTATE → Sequentum/UiPath; DRE feed clean |
| 16 | UK | DVLA VES + DVSA MOT | **not public** (reasonable cause) | **VES free per-plate; MOT History free + full-DB extract** (app approval) | `en_core_web_trf` / `en_core_web_lg` | gov APIs clean, no WAF |
| 17 | IE | NVDF (Dept Transport) | **restricted** (S.I. 287/2015) | aggregate TDM01/TDA01 on data.gov.ie | `en_core_web_trf` | open-data ZIP+API, no WAF |
| 18 | PL | CEPiK | restricted (authorities) | open API + stats (dane.gov.pl 1558, CC-BY) | `pl_core_news_lg` / HerBERT | official APIs clean; CRBR via stealth scrape |
| 19 | CZ | Registr silničních vozidel | **on request, CZK 100/req** | not open/bulk | **NameTag 3** (ÚFAL) / Czech spaCy | ARES API + XML dump clean |
| 20 | HU | Nyilvántartó (JSZP) | **no owner** (data-protection) | public vehicle query, no owner | **HuSpaCy** `hu_core_news_lg` (F1≈0.869) | e-Beszámoló + e-Cégjegyzék server-rendered scrapeable |

**Cross-border spine (all 20):** GLEIF LEI golden copy (free daily, the cross-key); BRIS/e-Justice "Find a company" (free per-company, not bulk; UK left after Brexit); VIES VAT validation (free per-VAT confirm); OpenCorporates (aggregator, bulk by licence). UBO reality: **post-CJEU C-37/20 (22 Nov 2022), public/bulk UBO is closed in essentially every market**; only UK PSC remains fully free + bulk. PL CRBR is the last open EU one and **sunsets 1 Jul 2026**.

---

## 9. Coverage & Cost Model

### 9.1 Estimated records per market

Company counts from registries; contacts ≈ 1.5–2.5 decision-makers per active company that we can lawfully resolve (registry officers + public-surface LinkedIn + website imprint); vehicle = technical/fleet rows where open (owner-linkage Nordic-only).

| Market group | Companies (active, approx) | Resolvable contacts (approx) | Vehicle (technical rows, open) |
|--------------|---------------------------|------------------------------|-------------------------------|
| Nordics (SE/NO/DK/FI/IS) | ~3.5M | ~6–8M | FI ~5.1M open; SE historical; DK lookup; NO/IS none |
| DACH (DE/AT/CH) | ~5.5M | ~9–12M | aggregate only (no per-vehicle owner) |
| Benelux+FR (NL/BE/LU/FR) | ~7M (FR ~5M dominant) | ~12–16M | **NL RDW full open**; LU per-vehicle; BE/FR closed |
| Southern (IT/ES/PT) | ~9M (IT ~6M) | ~10–14M | IT ACI/MIT open; ES DGT microdata; PT closed |
| Isles+East (UK/IE/PL/CZ/HU) | ~10M (UK ~5M, PL ~2–3M) | ~14–18M | UK VES/MOT per-plate; PL/CZ stats; HU none |
| **Total (20 markets)** | **~35M companies** | **~50–65M contacts** | **~12–15M open vehicle rows** (NL+FI+IT+ES+LU+UK dominate) |

The 50M-records throughput target (§4.9) maps to a full company+contact build cycle; vehicle technical data is overwhelmingly **bulk** (RDW/Traficom/ACI/DGT) so it adds load to the parse farm, not the fetch fleet.

### 9.2 Monthly run-cost (three tiers)

| Tier | What it uses | Companies/contacts coverage | Vehicle | Est. monthly cost |
|------|--------------|----------------------------|---------|-------------------|
| **Free-tier** | Bulk registries + free APIs + OSS scrapers + free proxies + GLEIF/VIES; no licensed tools, no paid proxies/APIs | ~85–90 % of company fields (registry-carried); ~40–55 % of contacts (registry officers + public LinkedIn SERP + imprint); **0 paid UBO/financials in no-bulk markets** | technical only, open feeds | **~$300–900** (compute on spot + Redis/Postgres/Fabric; egress) |
| **Budget-tier (with licensed tools)** | Free-tier **+ Screaming Frog/Sequentum/UiPath/Ranorex seats + residential proxy pool + per-doc financials (DE ~€1, IT/ES visure) + gated Apollo confirms** | ~92–95 % company; ~60–70 % contacts (licensed crack hard portals; SF mines imprints at scale); financials in no-bulk markets via targeted per-doc | technical + Nordic owner-linkage (merinfo/biluppgifter/Blocket) | **~$2k–6k** (seats amortised + ~$1–3k proxy/credits + per-doc fees on targeted set) |
| **Enterprise** | Budget-tier **+ Sequentum Cloud overflow + UiPath cloud robots + full residential/ISP proxy + SMTP-RCPT warmed IPs + paid KVK names + OpenCorporates licence + legit-interest UBO access where lawful** | ~95–98 % company; ~75–85 % contacts; UBO where legally purchasable | broadest lawful | **~$15k–40k+** (Cloud seat-hours + proxy bandwidth dominates ≈$0.15/profile at 50M scale; legal/LIA + OpenCorporates licence) |

Cost is dominated by **proxy egress bandwidth, not compute** (compute is never the wall). The Bulk-Ingest plane is what keeps the free tier viable — it removes 30–60 % of fetches before a socket opens.

---

## 10. Phased Implementation Roadmap

### Phase 0 — Nordic MVP (SE/NO/DK/FI/IS) + the spine

**Goal:** prove bulk-first + adaptive router + fusion on the easiest, richest open markets; ship a calibrated API.

**Build:**
1. **Bulk Ingestion Plane + `BulkSource` registry** (the highest-leverage component, critic P0-1): SE Bolagsverket bulkfil + **iXBRL weekly** (parse with `arelle`, not OCR); NO brreg `/api/enheter/lastned` + `/api/roller/totalbestand`; DK CVR S2S Elasticsearch (`gronlund/cvrdata`); FI PRH all-companies JSON; GLEIF golden copy. Delta-feed subscribers. Load → `registry_bulk_index` + Bloom + canonical store.
2. **Per-source policy table** seeded from the country files (even Nordics: SE landing-HTML CAPTCHA scoping; reuse restrictions).
3. **Adaptive router core**: MethodRouter (mabwiser Thompson + cluster prior), FailureClassifier, AdaptiveLimiter (aiolimiter AIMD), IdentityFactory (browserforge); Redis HA + Postgres snapshot of posteriors.
4. **OSS fetch fabric** rows 1–8 (curl_cffi/wreq, cloudscraper, Scrapling, Botasaurus, Camoufox, nodriver) + selectolax/lxml parse; free proxy fabric.
5. **Contact lane**: website imprint via curl_cffi + **public-surface LinkedIn SERP resolution** (DDG/Startpage/SearXNG `site:linkedin.com/in`) under a strict risk budget — reuse the existing `contact-intel`/`company-contact-finder` skills; email pattern+MX (no SMTP at volume).
6. **NER language dispatcher**: KB/bert (SE), FinBERT (FI), DaCy (DK), nb-bert (NO), IceBERT/scandi fallback (IS).
7. **Fusion + confidence + GDPR**: blocking→RapidFuzz→Splink→log-odds fuse; freshness half-lives; calibration bootstrapped on registry-confirmable fields (email/phone marked uncalibrated); provenance + DNC(NIX)+erasure at intake; output API envelope.
8. **One licensed backend wired**: **Screaming Frog** behind `ScraperBackend` for full-site imprint mining (lowest-friction licensed integration, proves the seat-pool contract).
9. **Vehicle (honest scope)**: FI Traficom open bulk + SE historical + Nordic owner-linkage via merinfo/biluppgifter/Blocket skills, flagged as the only owner-coverage tier.

**Repos/tools:** curl_cffi, wreq-python, cloudscraper, Scrapling, Botasaurus, Camoufox, nodriver, browserforge, intoli/user-agents, mabwiser, aiolimiter/aiometer, tenacity, pybreaker, selectolax, lxml, RapidFuzz, datasketch, Splink, spaCy + KB/bert/FinBERT/DaCy, dnspython, arelle, Arq, Redis, DuckDB, Fabric/Postgres. Licensed: Screaming Frog.

### Phase 1 — DACH + Benelux + France (DE/AT/CH/NL/BE/LU/FR)

**Goal:** add the policy-hard and mixed-openness markets; bring up the full licensed-tool stack and the seat broker.

**Build:**
1. **Bulk sources**: FR SIRENE Parquet + INPI RNE SFTP (free, **data.inpi.fr** route); BE KBO daily + SFTP; NL KVK financial-statements open + **RDW vehicles**; CH Zefix/LINDAS SPARQL; AT HVD; DE OffeneRegister snapshot + bundesAPI deltas; NBB CBSO (BE financials).
2. **Hard policy enforcement**: DE Handelsregister capped ≤60/hr and *routed away* to OffeneRegister; mark forbidden-automated sources; NL keying flagged (anonymised bulk → LEI/paid-API for names); reuse=no_direct_marketing on KBO/DE-directory contact fields.
3. **LicensedSeatBroker** (critic P0-5): global priority queue across SF/Sequentum/UiPath/Ranorex; Cloud-overflow policy + daily spend ceiling; seat-saturation metric. Wire **Sequentum** (anti-bot tables), **UiPath** (portal/gov logins), **Ranorex** (stubborn UI / thick-client).
4. **NER**: flair-german (DE/AT), multilingual xlm-roberta/wikineural (CH), RobBERT (NL), camembert (FR), language routing for BE/LU.
5. **Per-doc financials lane**: DE ~€1, gated and budgeted; XBRL fast path everywhere it exists.
6. **Vehicle**: RDW (NL, gold), LU Parc Automobile, CH ASTRA IVZ, FR/AT/BE aggregate — technical only.

**Repos/tools:** + FlareSolverr (optional pool), PaddleOCR/RapidOCR/Tesseract + opencv (no-bulk-financials OCR tail), GLiNER, Splink at scale on Spark, Temporal (enrichment saga), Faust/Kafka (delta firehose), Dramatiq (parse fleet), KEDA. Licensed: Screaming Frog + Sequentum (Desktop+Cloud) + UiPath + Ranorex.

### Phase 2 — Full EU (Southern + Isles/East: IT/ES/PT/UK/IE/PL/CZ/HU)

**Goal:** complete 20-market coverage, including the pay-per-document and WAF-hostile registries; scale to 50M.

**Build:**
1. **Bulk/open sources**: UK Companies House + PSC + Accounts; IE CRO; CZ ARES XML; PL KRS/REGON(SOAP)/CEIDG + RDF; ES BOE BORME API + opendata.registradores microdata; IT Movimprese + INI-PEC (PEC-first) + ACI/MIT vehicle; PT publicacoes.mj.pt + DRE feed; HU e-Beszámoló.
2. **WAF-hostile / VIEWSTATE handling**: ES CORPME marked `automated_access_forbidden` → BOE BORME API; PT VIEWSTATE postbacks → Sequentum/UiPath; IT Telemaco visure automated via UiPath/Ranorex for targeted org IDs only.
3. **Time-bomb handling**: PL CRBR public-UBO sunset **1 Jul 2026** flagged in policy table (auto-downgrade to restricted); CZ ESM already closed; IT UBO suspended.
4. **Scale-out to 50M**: 33 IO workers + 6 browser pods + 2 CPU pods + 1 GPU pod; KEDA on backlog; broker sharding (Redis Cluster / Kafka) once shared ceiling hit; full proxy-vendor diversity.
5. **NER**: it_core_news_lg, roberta-bne (ES), BERTimbau (PT), en_core_web_trf (UK/IE), pl_core_news_lg/HerBERT, NameTag 3 (CZ), HuSpaCy (HU).
6. **Calibration maturity**: bounce/answer feedback now accrued → re-fit isotonic on email/phone, publish reliability diagrams, lift "uncalibrated" flags where ground truth exists.

**Repos/tools:** full stack + 2captcha/capsolver (gated last resort), OpenCorporates licence (enterprise), all per-language NER models. Licensed: all four, at full seat utilisation under the global broker.

---

## 11. Open Questions / Risks + Decisions Needed

### 11.1 Risks carried from the critic (status in this blueprint)

- **Bulk-first now architected** (P0-1 fixed) — but each `BulkSource` parser is bespoke; freshness depends on delta-feed reliability per country.
- **LinkedIn scoped to public surface** (P0-2 fixed) — authenticated crawl forbidden; coverage of LinkedIn is therefore *bounded by what the public SERP exposes*, lower than an authenticated crawl would yield. This is a deliberate compliance/coverage trade.
- **Redis HA + durable learning** (P0-3 fixed) — adds Sentinel/Cluster ops weight and a snapshot/restore path that must be tested under failure.
- **Policy gate enforced** (P0-4 fixed) — depends on keeping the per-source policy table current as laws change (CJEU follow-ons, AMLR, PL CRBR sunset).
- **Seat broker defined** (P0-5 fixed) — but real licensed throughput at 50M is genuinely seat-bounded; Cloud overflow has a hard $ ceiling that will leave a hard-target tail in DLQ.
- **Vehicle owner-linkage is irreducibly Nordic-only** (P1-3) — pan-European owner coverage is impossible under the platform's own legal rules; the canonical model is honest about it.

### 11.2 Top 5 decisions needed from the user

1. **LinkedIn policy confirmation.** Confirm authenticated LinkedIn scraping stays **forbidden** (public-SERP resolution only), accepting lower LinkedIn coverage for legal safety — or do you have a licensed LinkedIn data source (Sales Navigator export, a data partner) we should wire as a sanctioned backend instead?
2. **Budget tier + monthly ceiling.** Which cost tier do we target — free (~$300–900/mo, registry-rich but thin contacts), budget-with-licensed (~$2–6k/mo), or enterprise (~$15–40k+/mo)? And what is the hard monthly ceiling for paid proxies + per-doc financials + Sequentum Cloud / UiPath cloud overflow?
3. **UBO & paid-financials scope.** Post-CJEU, UBO is closed almost everywhere. Do we (a) ship directors-from-register + GLEIF parent-relationships only, or (b) fund legitimate-interest UBO access + per-doc financials in the no-bulk markets (DE/AT/IT/ES/PT/LU/HU)? This decides whether Phase-1/2 carry a per-document financials line.
4. **NL named-company data.** The free KVK bulk is anonymised. Do we purchase the **paid KVK Handelsregister API** for Dutch company names + KVK numbers (the only legal route to names at scale), or live with LEI/probabilistic NL keying and reduced NL coverage?
5. **Licensed seat counts + host topology.** Confirm exact seat counts and where they run: SF crawl seats, Sequentum desktop seats + Cloud key, UiPath unattended robot count + Orchestrator folder, Ranorex agent VMs. These are the real throughput wall for the hard-target tail (§6.3) and size the seat broker's queue.

### 11.3 Cross-cutting

- The country research is excellent and now **machine-readable as a source registry + per-source policy table** — the single highest-leverage conversion of prose into routing decisions. Keep it versioned; laws move (PL CRBR 1 Jul 2026 is days away).
- Three of five entity types (LinkedIn, vehicle-owner, person/contact) are where both the differentiation **and** the risk live; the company layer is well-served by registries. Phase budgets weight the people/LinkedIn/vehicle layers accordingly.
- The honesty/compliance moat (calibrated confidence, provenance, no number we can't defend) is now enforced by a **shared policy gate** so the scrape-everything half and the compliance half of the platform no longer contradict each other.
```

