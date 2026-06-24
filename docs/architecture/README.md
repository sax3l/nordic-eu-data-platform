# Architecture

The 5 pillars. The ratified design lands in `MASTER_BLUEPRINT.md` (produced by the running research pass); each pillar gets its own deep‑dive file alongside it.

1. **`adaptive-engine.md`** — the brain. Multi‑armed‑bandit method router (per‑host success/latency/block tracking), AIMD adaptive concurrency, failure classifier → auto‑remediation, coherent identity rotation (UA+headers+TLS+proxy+viewport bound together).
2. **`speed-parallelism.md`** — maximum throughput. Distributed work fabric (Celery/Redis or Temporal), **source‑racing / hedged requests** (fire cheap + deep together, take first good, cancel slow), batched OCR/NER, queue‑depth autoscaling, throughput math to 50M records.
3. **`oss-combination-matrix.md`** — situation → ordered tool‑chain → fallback, operationalising the 85‑repo catalog.
4. **`licensed-tools.md`** — Screaming Frog / Sequentum / UiPath / Ranorex as first‑class backends behind the router, modelled as seat‑limited resource pools, with the escalation order.
5. **`fusion-confidence.md`** — canonical entity model across 20 national ID schemes, LEI/GLEIF cross‑key, entity resolution (Splink/RapidFuzz), multi‑source agreement scoring, freshness/decay, GDPR‑by‑design.

> Until `MASTER_BLUEPRINT.md` lands, the authoritative summaries live in the root [`README.md`](../../README.md) and the per‑pillar intent above.
