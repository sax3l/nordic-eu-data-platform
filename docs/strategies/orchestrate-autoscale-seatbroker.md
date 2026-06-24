# Strategy: Autoscaling + Global LicensedSeatBroker — elastic compute, scarce-seat priority, parse-pool backpressure

**Cluster:** Orchestration · **Layer:** elasticity / scarce-resource allocation
**Builds on:** `docs/architecture/pillars/speed-parallelism.md` §4.6 (backpressure), §7 (KEDA), `docs/architecture/pillars/licensed-tools.md` §6.3 + §7 (SeatPool, bin-packing, expected-utility), `docs/architecture/MASTER_BLUEPRINT_FULL.md` §4.8, §6.3.
**Compose with:** `orchestrate-work-fabric` (scales on its queue depth), `cost-aware-fallback` (Cloud-overflow spend ceiling is the same budget gate), `monitor-bandit-feedback` (seat-saturation + P_success are metrics-store-driven), `freshness-delta-decay` (scale-to-zero in quiet windows, surge for the morning refresh).

---

## 1. Mechanism

Two scarce resources must be governed at once: **stateless compute** (cheap, elastic, killable) and **licensed seats** (Screaming Frog ×4, Sequentum desktop ×2 + Cloud, UiPath robots, Ranorex agent VMs — few, expensive, the real throughput wall for the hard-target tail). This strategy gives each its own controller.

**(a) KEDA autoscaling on queue depth, not CPU.** IO workers sit at ~30% CPU while 5k sockets wait, so CPU is a lying signal. A `ScaledObject` scales the Arq IO fleet on **Redis backlog** (`listLength`), the browser pool on its own RAM-bounded trigger with a conservative `maxReplicaCount`, and the Dramatiq parse/GPU fleet on the **`parse` stream length** — three independent triggers so pools grow on their *own* demand. Workers are stateless + idempotent (job re-queued on SIGTERM) → they run on **spot/preemptible at 60–90% discount**; a killed worker drops its lease and the broker redelivers. KEDA scales to **zero** in quiet windows.

**(b) Global `LicensedSeatBroker` — one priority queue across all four tools.** Every licensed tool implements the same `ScraperBackend` interface with a `SeatPool` (an awaitable semaphore). The broker holds a **cross-backend global seat view** and allocates the highest-value ready target to the best-fit *free* seat using **expected-utility routing**:

```
EU(b, target) = P_success(b, domain)·value(target)
              − (cost(b) + latency_penalty(b))·urgency
              − seat_pressure(b)
```

`P_success` is Beta-Bernoulli per `(backend, domain)`, converging from a static prior to the observed rate — so the first CF challenge on a domain collapses every OSS tier's `P_success` and **lifts Sequentum/UiPath automatically**. A per-tick **bin-packing scheduler** maximises total expected yield subject to `Σ assigned(b) ≤ b.seats.total`, keeping every OSS lane saturated (∞ seats) while each scarce seat works its single best-fit target.

**(c) Cloud-overflow with a hard ceiling.** When desktop seats are full **AND** backlog age > threshold **AND** target value > cost-of-cloud-call → spill to Sequentum Cloud / UiPath cloud robots, under a **per-day spend ceiling**. When even Cloud is saturated, targets DLQ with an explicit `seat-starved` reason — never silent waiting, never fabricated.

**(d) Parse-pool backpressure (the bidirectional governor).** Raw scraped bytes are handed to the CPU/GPU pool over the broker so the fetch loop never blocks on a 200 ms parse. The reverse direction is closed too: when the `parse` stream depth crosses a high-water mark, the IO limiter's `acquire()` blocks (or the scheduler de-prioritises new fetches) until it drains. Throughput is thus governed by the **slowest *necessary* stage**, and Redis never OOMs on freshly-scraped HTML.

## 2. Tools / repos it uses

- **[KEDA](https://github.com/kedacore/keda)** — Kubernetes event-driven autoscaling on Redis/Kafka backlog.
- **Kubernetes HPA + spot/preemptible node groups** (tainted so only interruption-tolerant pools land on spot).
- **`asyncio.Semaphore`-backed `SeatPool`** + bin-packing scheduler (`licensed-tools.md` §6–7).
- **[mabwiser](https://github.com/fidelity/mabwiser)** Beta-Bernoulli for per-`(backend,domain)` `P_success`.
- Licensed CLIs/APIs: Screaming Frog `--headless`, Sequentum `RunAgent.exe` / Cloud REST, UiPath Orchestrator OData `StartJobs(JobsCount=k)`, Ranorex `Suite.exe`.

## 3. Failure mode it eliminates

- **Compute over/under-provisioning** — CPU-based autoscaling leaves IO workers starved (CPU low while sockets wait) or overscales the GPU pool. Queue-depth triggers per pool eliminate both, and scale-to-zero removes idle spend.
- **Seat thrash and starvation** — without a global broker, each backend's seats are allocated locally, low-value targets burn scarce UiPath robots, and high-value targets wait. The cross-backend bin-packer + `value`/`urgency` priority eliminates mis-allocation; raising the "is this worth a seat?" bar under pressure eliminates starvation of high-value work.
- **Silent seat-stall** — targets that can't get a seat are DLQ'd with a clear reason, not lost.
- **Redis OOM / runaway buffering** — the parse high-water-mark backpressure eliminates the classic "fetch faster than you can parse → broker explodes" failure.

## 4. Composition

- ← **`orchestrate-work-fabric`**: KEDA reads that fabric's per-shard backlog; the seat broker is a specialised consumer of the same fabric.
- ↔ **`cost-aware-fallback`**: the Cloud-overflow per-day spend ceiling **is** an instance of the budget-gated counter — the same ledger that gates paid proxies/CAPTCHA gates cloud-seat spillover.
- ← **`monitor-bandit-feedback`**: seat-saturation is a first-class metric both KEDA and the `EU(b,target)` threshold react to; `P_success` comes straight from the metrics store.
- ↔ **`freshness-delta-decay`**: re-verification surges (morning refresh) drive scale-up; quiet windows drive scale-to-zero.

## 5. Success contribution

This strategy converts the seat constraint from a hard cliff into a **graceful, value-prioritised degradation**. Its contribution is twofold: (a) **elasticity** lets the fallback cascade's expensive rungs actually exist at 50M scale on a viable budget (spot discounts + scale-to-zero keep the free/budget tiers affordable per `MASTER_BLUEPRINT_FULL.md` §9.2); (b) **scarce-seat priority routing** maximises the marginal coverage bought per seat — when seats are the wall, the platform spends them on the highest-`value` hard targets first, so the recovered tail (the records *only* a licensed tool can crack) is maximised rather than randomly sampled. Honestly: a hard-target tail will remain seat-bounded and land in DLQ under the Cloud ceiling — that residual is real and is reported, not papered over. The strategy maximises *achievable* recovery within the lawful, budgeted seat envelope.

## 6. Compliance envelope

- **Spend ceiling is a precondition** — Cloud-overflow cannot exceed the configured per-day budget; this keeps the platform inside its declared cost tier and prevents an autoscaler from silently running up paid-API/proxy bills.
- **Seats are spent only on lawful targets** — licensed tools are routed by the same policy gate as OSS; UiPath/Sequentum never drive an `automated_access_forbidden` source (ES CORPME) or a competitor login. They *are* the sanctioned path for stateful government portals (Bolagsverket interactive flows, PT VIEWSTATE) that the law permits but OSS can't drive deterministically.
- **No seat is allocated to authenticated LinkedIn** — that tier is off by default and forbidden; the broker's `can_handle` capability gates exclude it.
- **Backpressure protects source politeness** — by throttling fetch when parse is saturated, the system can't accumulate a backlog that would later be drained as an aggressive burst against a registry.
