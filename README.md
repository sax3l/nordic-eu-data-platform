# Nordic + EU Adaptive Data Platform

> An adaptive, self‑healing, maximally‑parallel B2B data‑harvesting platform covering **every company, contact person, website and vehicle** across the Nordics and the major European markets — built to out‑cover and out‑honest Apollo / Cognism / ZoomInfo / LinkedIn Sales Navigator.

**Status:** 🚧 Design + documentation phase. This repository is the single source of truth for the architecture, the methods, the data sources, and the build plan. Code lands once the blueprint is ratified.

---

## The thesis

Incumbent ICP tools (Apollo, Cognism, ZoomInfo, Lusha, …) advertise 90‑97% accuracy and deliver 62‑70% in independent testing (see [`docs/competitive/`](docs/competitive/)). Their moat is *scale + UX*, not *correctness* — and almost none of their underlying data is proprietary. The opportunity:

1. **Adaptive multi‑method harvesting** — sense which method works per target and adapt method *and* speed in real time; auto‑correct blocks/errors.
2. **Source‑racing** — fire the cheapest source and the deep scrape together, take the first good answer, cancel the slow one → combining sources raises *speed*, not just coverage.
3. **Every market, every primary source** — 20 Nordic + EU national registries, vehicle registries, financial filings, and the public web, fused on a cross‑border key (LEI/GLEIF).
4. **Honest, GDPR‑native confidence** — per‑field provenance, multi‑source agreement scoring, freshness/decay tracking. This is the EU moat the US tools cannot match.

## Repository map

| Path | What's in it |
|---|---|
| [`docs/architecture/`](docs/architecture/) | The 5 architecture pillars + the **MASTER_BLUEPRINT** |
| [`docs/competitive/`](docs/competitive/) | Apollo / Cognism / LinkedIn / ZoomInfo teardown + ICP landscape |
| [`docs/infrastructure/`](docs/infrastructure/) | Docker / Kubernetes / worker / monitoring guides |
| [`docs/pipelines/`](docs/pipelines/) | Web‑extraction + NER pipeline spec |
| [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) | **Read first.** Legal posture, source tiers, the hard lines |
| [`catalog/`](catalog/) | 85+ OSS repos, CF/WAF bypasses, headless browsers |
| [`catalog/methods/`](catalog/methods/) | One runbook per scraping/OCR/NER method |
| [`catalog/icp-tools/`](catalog/icp-tools/) | Every ICP / sales‑intelligence tool in the world (profiles) |
| [`catalog/ai-agents/`](catalog/ai-agents/) | Every free open‑source AI agent / automation framework |
| [`sources/`](sources/) | **The source registry** — every website with recurring data |
| [`country-data/`](country-data/) | Verified per‑country source inventories (20 markets) |
| [`src/`](src/) | Implementation (orchestrator, scrapers, ocr, ner, fusion, ui‑automation) |
| [`plans/`](plans/) | Roadmap + [`DOCUMENTATION_PLAN.md`](DOCUMENTATION_PLAN.md) |

## The 5 architecture pillars

1. **Adaptive self‑healing engine** — multi‑armed‑bandit method router, AIMD adaptive concurrency, failure classifier → auto‑remediation, coherent identity rotation.
2. **Maximum‑speed parallelism** — distributed work fabric, source‑racing / hedged requests, batched OCR/NER, queue‑depth autoscaling.
3. **OSS combination matrix** — ordered tool‑chains per situation (static → CF → SPA → OCR → NER → dedup).
4. **Licensed‑tool orchestration** — Screaming Frog, Sequentum, UiPath, Ranorex as first‑class backends behind the same router, modeled as seat‑limited resource pools.
5. **Cross‑border fusion + confidence + GDPR** — canonical entity model across 20 ID schemes, entity resolution, multi‑source agreement scoring, freshness/decay, compliance‑by‑design.

## Coverage target

| Market | Companies (≈) | Notes |
|---|---|---|
| Nordics (SE/NO/DK/FI/IS) | ~3.5M | Open bulk registries — strongest coverage |
| DACH (DE/AT/CH) | ~6M | Mixed open/paid registries |
| Benelux + FR | ~14M | SIRENE open bulk (FR) is huge |
| Southern (IT/ES/PT) | ~9M | Mostly paid registries → scrape/aggregator path |
| British Isles + Central (UK/IE/PL/CZ/HU) | ~7M | UK Companies House fully open |
| **Total** | **~40M companies** | + contacts, websites, vehicles |

See [`sources/sources.yaml`](sources/sources.yaml) for the machine‑readable registry and [`country-data/`](country-data/) for verified per‑country detail.

---

© Protosell / SIAX. Internal — not for distribution. See [`LICENSE`](LICENSE) and [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).
