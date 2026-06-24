# Strategy: Distributed Work Fabric — saturate global throughput within every per-host cap

**Cluster:** Orchestration · **Layer:** scheduling / distribution
**Builds on:** `docs/architecture/pillars/speed-parallelism.md` (§1 async/proc/distributed matrix, §2 work fabric, §2c sharding), `docs/architecture/MASTER_BLUEPRINT_FULL.md` §4.3, `docs/architecture/pillars/adaptive-engine.md` §4 (AIMD).
**Compose with:** `orchestrate-autoscale-seatbroker` (consumes this queue's depth signal), `cost-aware-fallback` (the budgeted counter rides on these task envelopes), `freshness-delta-decay` (re-verification jobs enter as a priority lane), `monitor-bandit-feedback` (every task emits the metrics that tune the router).

---

## 1. Mechanism

The work fabric is the distributed nervous system that turns "resolve 35M companies + 50–65M contacts" into a stream of independently schedulable, independently retryable, independently rate-metered tasks — and keeps the global fleet pinned at the hardware/network ceiling **without ever exceeding a single host's politeness limit**.

Three primitives do the work:

1. **Right framework per pool (never one tool):**
   - **IO fetch fleet → Arq** (asyncio + Redis): one worker = one event loop = thousands of in-flight sockets. This is the 90% path — every registry API, VIES, GLEIF, JSON endpoint, static HTML.
   - **CPU parse/NER/OCR fleet → Dramatiq** (process actors, `prefetch=1`, GPU affinity, built-in rate-limit + backoff middleware).
   - **Stateful enrichment saga → Temporal**: the 6-step "company → officers → emails → verify" pipeline resumes at the *failed* step, so a crash never re-spends an Apollo credit or re-solves a CAPTCHA.
   - **Change firehose → Faust/Kafka**: replayable, partitioned registry-delta and vehicle-listing streams (feeds `freshness-delta-decay`).

2. **Broker by job shape:** Redis Streams as the default broker + cache + Bloom + rate-limit store (one dependency, four jobs, ~100k msg/s); RabbitMQ where true message-level priority + reliable acks matter (LinkedIn risk-budgeted work, `x-max-priority`); Kafka only for the streaming change-feed lane.

3. **Priority + per-host sharding (the core invariant):**
   - **Shard key = `(country, registrable_domain)`** — `q:SE:allabolag.se`, `q:NO:data.brreg.no`. Each shard owns its own Redis stream **and its own token bucket** (atomic leaky-bucket Lua), so the per-host RPS cap is enforced *at the shard*, decoupled from global concurrency.
   - **Fair-share dispatch:** the global dispatcher pulls **round-robin across active shards**, not FIFO across one queue, so a 2M-row `.se` domain cannot starve a 5k-row `.fi` registry.
   - **Priority lanes** urgent / normal / batch drained **8:3:1** (RabbitMQ `x-max-priority` or three Redis lists). Urgent = a user-triggered single-company lookup; batch = the overnight 50M backfill.

Each shard's token bucket is fed by the per-host **AIMD** window from the adaptive engine (`adaptive-engine.md` §4): the bucket rate *is* `cwnd`, so when a host blocks, the shard slows globally across all workers at once — the politeness ceiling is a fleet-wide property, not a per-worker guess.

## 2. Tools / repos it uses

- **[Arq](https://github.com/python-arq/arq)** — asyncio IO task fleet.
- **[Dramatiq](https://github.com/Bogdanp/dramatiq)** — CPU/NER/OCR actor fleet.
- **[Temporal](https://github.com/temporalio/temporal)** — durable enrichment saga.
- **[Faust-streaming](https://github.com/faust-streaming/faust)** on **Kafka** — change firehose.
- **Redis (Streams/Lists)** + **RabbitMQ** — brokers; Redis also holds Bloom (`datasketch`) + token buckets.
- **[pyrate-limiter](https://github.com/vutran1710/PyrateLimiter) / [aiolimiter](https://github.com/mjpieters/aiolimiter) / aiometer** — per-shard token buckets.
- **[pybreaker](https://github.com/danielfm/pybreaker)** — per-shard circuit breaker → slow retry queue.
- **[tenacity](https://github.com/jd/tenacity)** — jittered exponential retry (kills thundering-herd).

## 3. Failure mode it eliminates

- **The "one big domain starves everything" pathology** — naive FIFO queues let a 2M-row crawl monopolise all workers while a small registry's quota sits idle. Round-robin fair-share sharding eliminates it.
- **Global politeness violations** — without per-shard token buckets, N parallel workers each "respect" a host's RPS locally and collectively hammer it into a block (and a compliance breach). The shard-level bucket makes the cap a fleet invariant.
- **Lost work on crash** — without checkpoint/resume and Temporal sagas, a restart re-scrapes everything and re-spends paid credits. State per URL (`pending → inflight → done | dlq`) + last-good method/identity is persisted, so a crash resumes exactly.
- **Head-of-line blocking of urgent lookups** behind the overnight batch — the 8:3:1 priority drain eliminates it.

## 4. Composition

- → **`orchestrate-autoscale-seatbroker`**: queue depth per shard is the demand signal KEDA scales on; the licensed-seat backlog is a lane in this same fabric.
- → **`cost-aware-fallback`**: every task carries a cost-budget envelope; the fabric is where the free-first cascade is sequenced and where paid arms are gated.
- → **`freshness-delta-decay`**: delta-feed events (Faust/Kafka) and decay-triggered re-verifications are injected as normal-priority shards, so refresh competes fairly with first-pass discovery.
- → **`monitor-bandit-feedback`**: each `FetchResult` (method, status, latency, block-signal) flows from the fabric into the metrics store that tunes the bandit and AIMD.

## 5. Success contribution

The fabric is the *enabler* multiplier, not a per-target probability: it lets the platform run **33 IO workers + 6 browser pods + 2 CPU pods + 1 GPU pod** at the 50M/day line, linear in IO workers until a shared ceiling (Redis ~100k msg/s, proxy egress, a registry's global quota). Its direct success contribution is (a) **+throughput** — keeps every lawful lane saturated simultaneously, raising *universe coverage per unit time*; (b) **−lost-work** — checkpoint/resume + Temporal sagas push effective task-completion from "best-effort" toward ~1.0 by removing re-spend and re-scrape on crash; (c) **enables the fallback cascade** — because each rung is a discrete task, the per-target extraction success `1 − Π(1−pᵢ)` can actually be realised stage by stage rather than collapsing on the first failure. Without the fabric, the other four strategies in this cluster have nowhere to run.

## 6. Compliance envelope

- **Per-shard token buckets are a hard precondition, not an optimisation.** `COMPLIANCE.md` §5 ("respect technical signals") and the per-source policy gate require that DE Handelsregister's **≤60 req/hr §§303a/b StGB criminal cap** and ES CORPME's `automated_access_forbidden` flag are enforced *before dispatch*. The shard's bucket rate is seeded from the policy table, and forbidden sources are routed away (DE → OffeneRegister, ES → BOE BORME) at intake — the fabric never schedules a task that would breach the cap.
- **Suppression at intake:** national DNC (SE NIX, DE Robinsonliste, FR Bloctel) and erasure tombstones are checked when a task is *enqueued*, so suppressed/erased contacts never enter a shard.
- **`429`/`Retry-After` is obeyed**, never brute-forced: a soft block multiplicatively shrinks the shard bucket; it is never treated as an obstacle to push through.
- **No competitor-DB exfiltration and no authenticated LinkedIn** ride this fabric — those are excluded upstream by the policy gate; the fabric only ever carries lawful, primary-source and public-SERP work.
