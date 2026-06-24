# Architecture: Maximum-Throughput / Parallelism Layer

**Part of:** Nordic + EU Company / Contact / LinkedIn / Website / Vehicle data platform
**Scope of this document:** the concurrency, distribution, racing, batching, caching and horizontal-scale design that makes every other layer (free OSS scrapers + licensed Screaming Frog / Sequentum / UiPath / Ranorex) run at the physical limit of the hardware and the network — never the limit of the code.
**Companion docs:** `OPEN_SOURCE_TOOLS_CATALOG.md` (tool inventory), `architecture_patterns_reference.md` (bulkhead / sticky-session / backoff / cost), `docker_scraping_infrastructure_guide.md`, `WEB_EXTRACTION_NER_PIPELINE.md`, `COMPETITIVE_ANALYSIS_APOLLO_COGNISM_LINKEDIN_2026.md`.

---

## 0. The core thesis: throughput = min(IO ceiling, CPU ceiling, politeness ceiling)

A crawl of 50M entities is **never** CPU-bound on the fetch and **never** IO-bound on the parse. The job is to keep each resource saturated *independently*:

- **IO-bound fetches** (HTTP GET, registry API, DNS) → one event loop can hold **5,000–20,000 in-flight sockets**. You do not fork processes for this; you fork only to escape the GIL on the *parse*.
- **CPU-bound work** (HTML→struct parse, NER, OCR, fuzzy-dedup, embedding) → one process per physical core, fed by a queue. asyncio here buys nothing.
- **Politeness ceiling** (per-host RPS, per-registry quota, LinkedIn risk budget) → a token bucket *per shard key*, decoupled from global concurrency.

The architecture below puts each of these in its own pool so one never starves the other, and adds a **racing layer** so the *cheapest source that can answer wins* and the expensive scrape is cancelled mid-flight.

```
                       ┌───────────────────────────────────────────────┐
   targets (50M) ──▶   │  DEDUP-BEFORE-FETCH  (Bloom + registry diff)   │
                       └───────────────────┬───────────────────────────┘
                                           │ only unseen / stale
                       ┌───────────────────▼───────────────────────────┐
   broker (Redis/  ◀──▶│  PRIORITY + FAIR-SHARE SCHEDULER (per-country, │
   RabbitMQ/Kafka)     │  per-domain shards, token buckets)            │
                       └───────────────────┬───────────────────────────┘
            ┌──────────────────────────────┼──────────────────────────────┐
            ▼                              ▼                              ▼
  ┌──────────────────┐         ┌──────────────────────┐       ┌──────────────────┐
  │ IO POOL (asyncio │         │ BROWSER POOL (fork:   │       │ TOOL POOL (licensed│
  │ httpx/aiohttp/   │         │ Playwright/Camoufox/  │       │ Frog/Sequentum/    │
  │ curl_cffi H2)    │         │ Botasaurus contexts)  │       │ UiPath/Ranorex)    │
  └─────────┬────────┘         └──────────┬───────────┘       └─────────┬────────┘
            │   RACE: asyncio.wait FIRST_COMPLETED across all three      │
            └──────────────────────────────┬──────────────────────────────┘
                                            ▼
                       ┌───────────────────────────────────────────────┐
   CPU POOL (procs)    │  PARSE / NER / OCR / DEDUP  (spaCy.pipe,       │
                       │  PaddleOCR batch, datasketch LSH, GPU batch)   │
                       └───────────────────┬───────────────────────────┘
                                           ▼  content-hash + canonical-id
                                     SINK (Fabric / Postgres / lake)
```

---

## 1. Async vs multiprocess vs distributed — the decision matrix

| Workload | Nature | Right model | Concrete tool | Concurrency unit | Why not the others |
|---|---|---|---|---|---|
| HTTP GET against APIs/registries | IO-bound | **asyncio + httpx[http2] / aiohttp** | `httpx.AsyncClient(http2=True)` | 1 loop, 5–20k sockets | Threads waste 8 MB/stack; procs waste fork cost |
| TLS-fingerprinted fetch of WAF sites | IO-bound + native | **curl_cffi async** | `AsyncSession(impersonate="chrome131")` | 1 loop, 2–5k sockets | Pure-Python httpx leaks JA3; gets 403 |
| JS-rendered / Cloudflare-challenge pages | IO + heavy RAM | **forked browser pool** | Playwright / Camoufox / Botasaurus, N contexts | 1 proc per ~6–10 contexts | One loop can't hold 500 Chromium tabs (RAM) |
| HTML→struct, regex, selector parse | CPU-bound | **ProcessPool (1/core)** | `concurrent.futures.ProcessPoolExecutor` | 1 proc/core | GIL serialises it inside asyncio |
| NER / OCR / embeddings | CPU/GPU-bound | **batched GPU + proc pool** | spaCy `nlp.pipe`, PaddleOCR batch, transformers batched | batch of 64–512 | Per-item calls waste 90% of GPU |
| Cross-machine 50M scale | distributed | **broker + worker fleet** | Dramatiq/Arq/Celery + Redis/RabbitMQ/Kafka | N pods × M coros | Single box caps ~2–4M/day |

**Rule of thumb that drives the whole platform:**

> **asyncio for the wait, processes for the work, machines for the scale.**

### 1a. When to use asyncio + httpx / aiohttp (the 90% case)

This is the default fetch path for **every API, every official registry (Bolagsverket / Brønnøysund / PRH / VIES / GLEIF), every JSON endpoint, and every non-JS HTML page**. It exploits four free wins:

```python
import httpx, asyncio
from aiodns import DNSResolver

# One client reused for the whole worker lifetime → HTTP/2 multiplexing,
# connection-pool reuse, keep-alive, and DNS cache all "for free".
limits = httpx.Limits(
    max_connections=2000,            # global socket ceiling for this loop
    max_keepalive_connections=2000,  # never tear down warm sockets
    keepalive_expiry=120,
)
client = httpx.AsyncClient(
    http2=True,                      # multiplex 100s of reqs over 1 TCP/TLS conn
    limits=limits,
    timeout=httpx.Timeout(10.0, connect=4.0),
    follow_redirects=True,
)

sem = asyncio.Semaphore(1500)        # bound in-flight work, not the pool

async def fetch(url):
    async with sem:
        r = await client.get(url)
        return r

async def run(urls):
    return await asyncio.gather(*(fetch(u) for u in urls), return_exceptions=True)
```

Why this is the throughput floor and not a guess:

- **HTTP/2 multiplexing** — against a registry that supports H2, one TCP+TLS handshake carries hundreds of concurrent streams. You pay TLS once per host instead of once per request. On `vies.ec.europa.eu` / `data.brreg.no` this alone is a 3–8× win versus HTTP/1.1 + new sockets.
- **Connection pooling / keep-alive** — `max_keepalive_connections=2000` keeps warm sockets so the median request skips the 1–2 RTT handshake entirely.
- **DNS cache** — wrap with `aiodns` / a 60 s TTL dict so 1M URLs across 50k hosts do 50k lookups, not 1M. Cuts ~20–40 ms off every cold request.
- **One client, reused** — creating a client per request is the #1 silent throughput killer; it throws away the pool every time.

A single tuned event loop on one 8-vCPU box sustains **3,000–8,000 req/s** against fast JSON APIs (registry bulk, VIES, Apollo MCP, internal Fabric). That is ~250M–700M requests/day from *one* loop for the IO-cheap fraction.

### 1b. When to fork browser pools

The moment a target needs a real JS engine (Cloudflare Turnstile, SPA, lazy-loaded LinkedIn-style DOM), asyncio stops helping — Chromium is **RAM-bound, not socket-bound** (~150–250 MB/context). You fork:

```python
# One process owns one browser; it runs K contexts concurrently on its own loop.
# Fleet = P processes × K contexts. RAM, not the loop, sets K.
#   8 GB free RAM / 0.2 GB per ctx ≈ 40 ctx → run 6–8 procs × 6 ctx safely.
from playwright.async_api import async_playwright

async def browser_worker(jobs, k=6):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox","--disable-gpu"])
        sem = asyncio.Semaphore(k)
        async def one(job):
            async with sem:
                ctx = await browser.new_context()          # cheap-ish, isolated
                page = await ctx.new_page()
                await page.route("**/*.{png,jpg,css,woff2}", lambda r: r.abort())  # block heavy assets → 2-4× faster
                await page.goto(job.url, wait_until="domcontentloaded")
                html = await page.content()
                await ctx.close()
                return html
        return await asyncio.gather(*(one(j) for j in jobs))
```

Forking is via the **process/broker layer** (`multiprocessing` locally, separate pods at scale) — never threads, because each browser leaks file descriptors and one crash must not take the loop down (bulkhead, see `architecture_patterns_reference.md` Pattern 1). Botasaurus and Camoufox slot in here unchanged; the `botasaurus-scraper` skill's "100% CF settings" become the per-context profile.

### 1c. When to go distributed

Single-box ceiling: ~**2–4M cheap fetches/day** or ~**150k–400k browser renders/day** before RAM/CPU caps. Cross that, or need fault isolation per country, and you move to a **broker + worker fleet** (§2). Trigger conditions:

- backlog > what one box drains in its SLA window,
- need country-sharded politeness across machines,
- need spot-instance elasticity (kill/restart workers without losing jobs),
- mixed licensed tools (Sequentum Cloud, UiPath robots) that live on their own VMs.

---

## 2. Distributed work fabric

### 2a. Task framework: Celery vs RQ vs Dramatiq vs Arq vs Temporal vs Faust

| Framework | Model | Native async | Throughput (msg/s/box) | Ops weight | Use it for |
|---|---|---|---|---|---|
| **Arq** | asyncio-first | ✅ built on asyncio+Redis | 10–30k | tiny | **The IO scraping fleet** — coroutine tasks, perfect fit for httpx workers |
| **Dramatiq** | thread/proc actors | partial | 10–20k | low | **CPU parse/NER/OCR fleet** — simple, fast, great retries/rate-limit middleware |
| **RQ** | proc, Redis | ❌ | 1–5k | minimal | Low-volume side jobs, registry bulk-diff cron |
| **Celery** | proc/thread/eventlet | ⚠️ clunky | 5–15k | high | Only if you already run it / need its huge ecosystem (beat, canvas) |
| **Temporal** | durable workflow | ✅ SDKs | n/a (orchestration) | high | **Long multi-step enrichment sagas** — "find company → officers → emails → verify" with retries/state that survive restarts |
| **Faust / Kafka-streams** | stream processor | ✅ | 100k+ | high | **Firehose**: continuous diff of registry change-feeds, vehicle-listing streams |

**Recommended split (not one tool — the right tool per pool):**

- **IO fetch fleet → Arq.** Coroutine-native, so 1 worker = 1 loop = thousands of in-flight fetches. Lowest overhead per task.
- **CPU/NER/OCR fleet → Dramatiq.** Process actors, prefetch=1, GPU affinity, built-in rate-limiters and exponential backoff.
- **Enrichment orchestration → Temporal** for the *stateful* per-entity saga (so a 6-step pipeline resumes exactly where it failed, not from scratch — critical when step 4 is a paid Apollo credit you don't want to re-spend).
- **Change firehose → Faust on Kafka** for registry delta streams and Blocket/vehicle live polling, where you want replayable, partitioned, exactly-once-ish ingestion.

### 2b. Broker: Redis vs RabbitMQ vs Kafka

| Broker | Throughput | Durability | Priority queues | Fan-out / replay | Pick when |
|---|---|---|---|---|---|
| **Redis** (streams/lists) | ~100k msg/s | RDB/AOF | ✅ (multi-list) | weak | **Default** — fast, simple, doubles as cache + Bloom + rate-limit store |
| **RabbitMQ** | ~50k msg/s | durable queues, acks | ✅ native x-max-priority | per-queue | When you need true per-message priority + reliable acks + per-domain queues |
| **Kafka** | 1M+ msg/s | log, infinite replay | ❌ (partition only) | ✅ replay/consumer groups | Firehose / change-feeds / when you must replay history |

**Concrete choice:** Redis as the **default broker + cache + rate-limit + Bloom store** (one dependency does four jobs), RabbitMQ when a workload truly needs message-level priority and guaranteed acks (LinkedIn risk-budgeted work), Kafka only for the streaming change-feed lane. This matches the cost table in `architecture_patterns_reference.md` (Redis $200 vs RabbitMQ $300 vs SQS pay-per-use per 1M).

### 2c. Priority queues, fair scheduling, country/domain sharding

The hard requirement: **saturate global throughput while never exceeding any single host's politeness limit.** Solve it by sharding the queue space and metering each shard with its own token bucket.

```python
# Shard key = (country, registrable_domain). Each shard = its own Redis stream
# + its own token bucket. Global pool pulls round-robin across shards (fair share),
# so a 2M-row .se domain can't starve a 5k-row .fi registry.

SHARD = lambda t: f"q:{t.country}:{t.domain}"        # e.g. q:SE:allabolag.se

RPS = {                                              # politeness ceiling per host
  "allabolag.se": 1.0, "linkedin.com": 0.2,
  "data.brreg.no": 20.0, "vies.ec.europa.eu": 8.0,
  "_default": 4.0,
}

async def token(host):                               # leaky-bucket in Redis (atomic Lua)
    bucket = f"rl:{host}"
    allowed = await redis.eval(LEAKY_LUA, 1, bucket, RPS.get(host, RPS["_default"]))
    return allowed == 1
```

- **Priority** — 3 logical levels (urgent / normal / batch). Urgent = a user-triggered single-company lookup; batch = the overnight 50M backfill. RabbitMQ `x-max-priority` or three Redis lists drained 8:3:1.
- **Fair scheduling across domains** — the global dispatcher pulls **round-robin across active shard streams**, not FIFO across one queue. This is what keeps one giant domain from monopolising workers while a small registry's quota sits idle.
- **Sharding by country** — also maps cleanly to data-residency, proxy geo (use a `.se` exit IP for Swedish sites), and licensed-tool routing (a Sequentum Cloud agent pinned per market).
- **Bulkhead per domain** — a circuit breaker per shard (Pattern 1) flips a hot domain to its own slow retry queue without touching the other 49,999 hosts.

---

## 3. Combine sources to maximize SPEED, not just coverage (the racing core)

This is the user's headline requirement and the platform's biggest differentiator. **For any one entity, fire the cheap/fast sources and the slow scrape *simultaneously*, take the first acceptable answer, and cancel the rest.** Two techniques:

1. **Dedup-before-fetch** — never fetch what a bulk registry dump already contains.
2. **Speculative / hedged execution** — `asyncio.wait(..., FIRST_COMPLETED)` with cancellation.

### 3a. Dedup-before-fetch (the cheapest request is the one you skip)

```python
# Before queuing ANY scrape, diff the target set against:
#   (1) bulk registry dumps already on disk (Bolagsverket iXBRL, brreg CSV, PRH),
#   (2) a Bloom filter of every entity we've already resolved,
#   (3) a freshness TTL (don't re-scrape a profile < N days old).
from datasketch import LeanMinHash          # near-dup of company names/sites
# + a scalable Bloom filter in Redis for seen canonical IDs

def needs_fetch(entity) -> bool:
    cid = canonical_id(entity)              # orgnr | normalized domain | li-slug
    if bloom_seen(cid):                     # O(1), ~0.1% false-positive
        if fresh_enough(cid):  return False # already have it, still fresh
    if cid in registry_bulk_index:          # answer is in a free bulk dump
        ingest_from_bulk(cid);  return False
    return True
```

Effect on a 50M run: registry bulk-dumps already answer **30–60%** of company-level fields (name, orgnr, SNI, officers, address) for free; Bloom skips re-work on re-runs (18–30% per `architecture_patterns_reference.md`). **You can routinely cut the actual fetch volume in half before a single socket opens.** That is the single largest speed win in the system.

### 3b. Speculative execution / hedged requests / first-good-wins

```python
import asyncio

async def resolve_company(entity):
    """Race every source that could answer. First acceptable answer cancels the rest."""
    sources = [
        asyncio.create_task(registry_api(entity)),   # ~80 ms, authoritative, FREE
        asyncio.create_task(apollo_enrich(entity)),   # ~300 ms, costs a credit
        asyncio.create_task(cached_lookup(entity)),   # ~2 ms, may miss
        asyncio.create_task(http_scrape(entity)),     # ~1.5 s, JS-free site
        asyncio.create_task(browser_scrape(entity)),  # ~6 s, last resort, expensive
    ]
    answer = None
    try:
        while sources:
            done, pending = await asyncio.wait(
                sources, return_when=asyncio.FIRST_COMPLETED, timeout=8.0
            )
            for t in done:
                sources.remove(t)
                res = t.exception() and None or t.result()
                if res and is_acceptable(res):        # has the fields we need, confident
                    answer = res
                    break
            if answer:
                break
    finally:
        for t in sources:                             # CANCEL the slow scrape mid-flight
            t.cancel()
        await asyncio.gather(*sources, return_exceptions=True)
    return answer or {}
```

Design notes that make this real, not a toy:

- **Staggered hedging, not pure parallel.** Don't always pay for the browser. Launch the cheap tier; only spawn the expensive tier if no acceptable answer arrives within a deadline (e.g. 400 ms). This is the "hedged request" pattern — bounded tail latency without N× the cost:

```python
async def hedged(entity):
    cheap = asyncio.gather(registry_api(entity), cached_lookup(entity))
    done, _ = await asyncio.wait({cheap}, timeout=0.4)
    if done and (r := pick_best(done)) and is_acceptable(r):
        return r                                    # 70-85% of cases end here, ~80 ms
    return await resolve_company(entity)            # only the hard tail pays for browser
```

- **`is_acceptable()` is the confidence gate.** A cheap API "confirms" the scrape: if VIES + Bolagsverket already agree on the legal name and orgnr, the slow allabolag scrape is *cancelled* — exactly the user's example of "a cheap API confirms a scrape so the slow scrape can be skipped." Confidence = source authority × field completeness × cross-source agreement.
- **Cross-source agreement raises BOTH speed and coverage.** Two cheap sources agreeing → skip the expensive one (speed). Two cheap sources disagreeing → escalate to the browser to break the tie (coverage). One control flow, both goals.
- **Cancellation is mandatory.** Without `task.cancel()` you keep paying proxy bandwidth and a Chromium tab for an answer you already have. The `finally` block is what turns "parallel" into "fast *and* cheap."

This is the same primitive used for adaptive method-sensing: each source's win-rate per domain is tracked, and `resolve_*` re-orders/short-circuits the race so the historically-winning method for *that* host fires first next time (see §6 ADAPT loop).

---

## 4. GPU/CPU batching for OCR & NER

Per-item inference wastes 80–95% of a GPU and most of a CPU's SIMD width. The parse fleet must **batch**, and IO-bound vs CPU-bound work must live in **separate pools** so a slow OCR never blocks a fast fetch.

### 4a. NER with spaCy `nlp.pipe` (batched, multiprocess)

```python
import spacy
nlp = spacy.load("xx_ent_wiki_sm")          # multilingual: SE/NO/DK/FI/DE/FR/...
# pipe() batches internally AND forks processes; never loop nlp(text) per doc.
for doc in nlp.pipe(texts, batch_size=256, n_process=8):
    persons = [e.text for e in doc.ents if e.label_ == "PER"]
    orgs    = [e.text for e in doc.ents if e.label_ == "ORG"]
```

`nlp.pipe(batch_size=256, n_process=N)` is **5–20× faster** than a Python loop: it vectorises the model forward pass and forks N workers. For transformer-grade accuracy, `transformers` pipeline with `batch_size=64` on GPU; for pure throughput keep the small CNN pipelines on CPU cores.

### 4b. OCR batching (PaddleOCR / RapidOCR / Tesseract)

```python
# GPU OCR: feed a LIST of images so the GPU runs one big batch, not 64 small ones.
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_gpu=True, det_db_score_mode="fast")
results = ocr.ocr(image_batch)              # batch det+rec; 5-15× vs per-image
# Throughput-tier alternative: RapidOCR (ONNX, quantized) → 1000+ img/s on CPU,
# use for high-volume low-stakes pages (vehicle plate crops, logo text).
# Tesseract: CPU-cheap fallback, parallelise across cores with a proc pool.
```

Tiering: **RapidOCR** for volume (1000+ img/s), **PaddleOCR** for accuracy (96.3%), **Tesseract** as the zero-dep CPU fallback (per `OPEN_SOURCE_TOOLS_CATALOG.md` §4). A dedicated GPU pod runs as a Dramatiq actor with `prefetch=1` and a micro-batching collector that gathers up to 512 images or 50 ms, whichever first.

### 4c. Separate IO-bound and CPU-bound pools (never mix)

```
Arq IO workers (asyncio)  ──push raw HTML/img──▶  Redis stream "parse"
Dramatiq CPU workers (1/core) ──pull batches──▶  spaCy.pipe / PaddleOCR batch
Dramatiq GPU worker (1/GPU, prefetch=1) ──micro-batch──▶ transformers / Paddle GPU
```

If you parse inside the fetch coroutine, a 200 ms CPU parse blocks the loop and your 5,000 sockets go idle. Hand raw bytes to the CPU fleet over the broker and the fetch loop never stalls. This is the single most common throughput regression in naive scrapers.

---

## 5. Caching layers (skip work at every level)

| Layer | Tool | Skips | Hit-rate / effect |
|---|---|---|---|
| **HTTP response cache** | `hishel` (httpx) / Redis, honor ETag/Last-Modified | re-downloading unchanged pages | 20–50% on re-runs |
| **Negative cache** | Redis key w/ short TTL | re-hitting known-404 / known-blocked URLs | kills wasted retries on dead hosts |
| **Content-hash dedup** | `xxhash`/`blake3` of normalized body | re-parsing identical content served at N URLs | 10–25% (mirror/param dupes) |
| **Entity Bloom filter** | `datasketch` / scalable Bloom in Redis | re-resolving an entity already in the DB | 18–30% (per benchmarks) |
| **Near-dup index** | `datasketch` MinHash-LSH / SimHash | merging "Acme AB" vs "Acme Aktiebolag" | O(1) lookup, 95%+ acc |
| **DNS cache** | `aiodns` + TTL dict | repeat resolution across 1M URLs / 50k hosts | ~20–40 ms saved/cold req |
| **Negative entity cache** | Redis TTL | re-attempting an entity that has no findable email | avoids re-running the whole 6-step saga |

```python
# Bloom-gate every entity at intake — the highest-leverage cache in the system.
from datasketch import LeanMinHash
import redis, xxhash

def already_have(canonical_id: str) -> bool:
    return bool(r.getbit("bloom:entities", _bloom_index(canonical_id)))

def content_changed(url: str, body: bytes) -> bool:
    h = xxhash.xxh3_64_hexdigest(normalize(body))
    prev = r.hget("chash", url)
    if prev == h:  return False                 # byte-identical → skip parse entirely
    r.hset("chash", url, h);  return True
```

The Bloom filter + registry bulk-index together are what let the racing layer (§3) be cheap: most entities are answered from cache/bulk and never enter the fetch fleet at all.

---

## 6. Self-sensing, self-correcting ADAPT loop (SENSE → ADAPT → ACT)

Real-time per-target method selection and concurrency tuning — requirements (4), (5), (6). Each `(country, domain)` shard keeps a rolling scoreboard in Redis:

```python
# Per-shard EWMA stats updated on every result.
#   success_rate, p50_latency, block_rate(403/429/captcha), best_method
async def adapt(shard, result):
    s = stats[shard]
    s.update(result)                            # EWMA of success, latency, blocks
    # SENSE which method works for THIS host, ACT on it next time:
    if s.block_rate > 0.15:                     # being detected
        s.concurrency = max(1, s.concurrency // 2)   # back off (Pattern 3)
        s.method = escalate(s.method)           # api → http → curl_cffi → browser → licensed tool
    elif s.success_rate > 0.95 and s.p50 < 0.5:
        s.concurrency = min(s.cap, s.concurrency + 2)  # ramp up while it's working
    # rank sources by observed win-rate so the RACE (§3) fires the winner first
    s.source_order = rank_by_winrate(shard)
```

- **SENSE** — every fetch reports `{method, status, latency, blocked?}`. EWMA per shard tells you which method currently works for that exact host.
- **ADAPT method** — climb the cost ladder *only as needed*: registry API → plain httpx → curl_cffi (TLS) → Botasaurus/Camoufox browser → **licensed Screaming Frog / Sequentum / UiPath / Ranorex** for the hardest authenticated/JS targets. The race in §3 reorders so the proven-best method runs first.
- **ADAPT concurrency** — AIMD (additive-increase / multiplicative-decrease, like TCP): +2 while green, ÷2 on block. This *automatically* finds each host's max safe RPS without a human tuning it.
- **ACT in parallel** — the dispatcher keeps every green shard saturated and every red shard throttled *simultaneously*; global throughput stays maxed even as individual hosts throttle (requirement 6, "every kind of parallel combination").

Licensed tools plug into this as just more "methods" the SENSE loop can pick: Screaming Frog SEO Spider for full-site URL/asset/structured-data harvest, Sequentum (Desktop+Cloud) for resilient agent-based extraction on hard JS sites, UiPath/Ranorex for authenticated portals that need true UI driving — each pinned to its own VM/pod pool and metered by the same token buckets.

---

## 7. Horizontal scale: Compose → k8s HPA/KEDA on queue depth

### 7a. Local → cluster

- **Dev / ≤2M/day:** `docker-compose` — 1 Redis, 1 Postgres, N Arq IO workers, M Dramatiq CPU workers, 1 GPU OCR worker, FlareSolverr sidecar (per `docker_scraping_infrastructure_guide.md`).
- **Prod:** Kubernetes with **KEDA scaling on broker backlog**, not CPU. Queue depth is the true demand signal for IO-bound scrapers (CPU sits at 30% while 5k sockets wait):

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: io-fetch-workers }
spec:
  scaleTargetRef: { name: arq-io-worker }
  minReplicaCount: 2
  maxReplicaCount: 300
  cooldownPeriod: 120
  triggers:
    - type: redis
      metadata:
        address: redis:6379
        listName: q:pending          # scale on backlog, the real demand signal
        listLength: "500"            # >500 queued per replica → add pods
```

CPU/GPU parse fleet scales on a *different* trigger (the `parse` stream length) so the two pools grow independently. Browser pods get a conservative `maxReplicaCount` because they're RAM-bound.

### 7b. Spot instances + autoscaling by backlog

- IO and browser workers are **stateless and idempotent** (job re-queued on SIGTERM) → run on **spot/preemptible** at 60–90% discount. A killed worker just drops its lease; the broker redelivers.
- Use a **node-group taint** so only interruption-tolerant pools land on spot; the broker, DB and Temporal control plane stay on on-demand.
- KEDA scales to **zero** in quiet windows (no nightly backfill = no idle cost), then back to 300 when the morning batch lands.

---

## 8. Throughput math — profiles/sec/worker → profiles/day at N workers

**Base unit (one tuned worker):**

| Worker type | Per-worker rate | Bottleneck |
|---|---|---|
| Arq IO fetch (cheap API/registry, H2 reuse) | **40–120 entities/s** | network RTT / per-host RPS |
| Arq IO fetch (TLS-spoofed WAF site, curl_cffi) | **8–25 entities/s** | per-host politeness |
| Browser render (Playwright, 6 ctx, assets blocked) | **0.6–1.5 entities/s** | Chromium CPU/RAM |
| CPU parse + NER (spaCy.pipe, 1 proc/core) | **150–500 docs/s** | model forward pass |
| GPU OCR batch (PaddleOCR, batch 512) | **300–1000 img/s** | GPU |

**Mix assumption** (realistic Nordic+EU company/contact run after dedup-before-fetch removes ~50%): of the *remaining* fetches ~70% answered by cheap API/registry, ~25% by HTTP/TLS scrape, ~5% need a browser. Blended ≈ **18 resolved entities/s/worker** sustained (accounts for blocks, retries, the 5% browser tax).

| Target | Entities | Window | Entities/day needed | Workers @ 18/s sustained | Notes |
|---|---|---|---|---|---|
| **1M** | 1,000,000 | 1 day | 1.0M | ⌈1.0M / (18×86,400)⌉ = **1** worker | one box finishes in <1 day; use 2–3 for headroom/SLA |
| **1M** | 1,000,000 | 2 hours | 12M/day-equiv | **8** workers | burst SLA |
| **10M** | 10,000,000 | 1 day | 10M | ⌈10M / 1.55M⌉ = **7** workers | ~6.5 rounded to 7; run 10 for retries/skew |
| **10M** | 10,000,000 | 6 hours | 40M/day-equiv | **26** workers | quarter-day refresh |
| **50M** | 50,000,000 | 1 day | 50M | ⌈50M / 1.55M⌉ = **33** workers | + browser/parse pools below |
| **50M** | 50,000,000 | 7 days | 7.1M/day | **5** workers | low-cost steady backfill |

Worked math: 18 entities/s × 86,400 s = **1.55M entities/day/worker**.
- 1M → 0.65 worker-days → **1 worker** (finishes in ~15 h).
- 10M → 6.5 worker-days → **7 workers** for 1-day.
- 50M → 32.3 worker-days → **33 workers** for 1-day, or **5 workers** for a relaxed 7-day backfill.

**Companion pools at the 50M/1-day line:**
- **Browser pool:** if 5% (2.5M) need rendering at 1.2/s/ctx → 2.5M / (1.2 × 86,400) ≈ **24 contexts** → ~4 browser pods (6 ctx each). Add headroom → **6 pods**.
- **CPU parse/NER:** 50M docs / (300 docs/s × 86,400) ≈ **2 proc-days** → comfortably **8 cores on 1–2 pods** with batching.
- **GPU OCR:** only the document/vehicle-image fraction; one GPU pod at 500 img/s clears ~43M img/day — usually **1 GPU** suffices.

So **50M companies/contacts in a single day ≈ 33 IO workers + 6 browser pods + 2 CPU pods + 1 GPU pod**, all stateless on spot, KEDA-scaled on backlog — squarely inside the "Large Scale" cost envelope in `architecture_patterns_reference.md` (≈$0.15/profile, dominated by proxy bandwidth, not compute).

**Scaling law:** throughput is **linear in IO workers** until you hit a *shared* ceiling — broker (~100k msg/s Redis), proxy egress bandwidth, or a registry's global quota. Past that, shard the broker (Redis Cluster / Kafka partitions) and add proxy vendors. Compute is never the wall; politeness budget and proxy bandwidth are.

---

## 9. Putting it together — one request's life

1. **Intake** → Bloom-gate + registry-bulk diff (§3a, §5). ~50% never fetched.
2. **Schedule** → sharded by `(country, domain)`, priority lane, token-bucket metered (§2c).
3. **Race** → `FIRST_COMPLETED` across cache / registry API / Apollo / HTTP / browser / licensed tool; cheapest acceptable answer wins, rest cancelled (§3b).
4. **SENSE/ADAPT** → record method win-rate + block-rate; AIMD the concurrency; reorder sources for this host (§6).
5. **Parse** → raw bytes handed over broker to CPU/GPU batch pool; never block the loop (§4).
6. **Dedup + canonicalize** → content-hash skip, MinHash-LSH entity merge (§5).
7. **Sink** → Fabric / Postgres / lake; update Bloom + freshness TTL so re-runs skip it.
8. **Scale** → KEDA watches backlog, spawns spot workers per pool independently (§7).

The result satisfies all eight platform goals: every OSS tool and every licensed tool is a selectable "method" in one adaptive race; the system runs at the hardware/politeness ceiling; it senses and self-corrects per target; it parallelises across sources, hosts, countries, and pools at once; and combining sources raises coverage **and** speed because the cheapest confirmation cancels the slowest scrape.
