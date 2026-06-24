# Documentation plan — the full corpus

> Goal: produce **every plan and document** for the platform *before* writing production code, so the build is a matter of execution, not discovery. This file is the index of the entire corpus and tracks generation status. Hundreds of documents, organised into 12 families.

Legend: ☐ planned · ◐ in progress (research pass running) · ☑ drafted

## A. Architecture (5 pillars + integration) — ~12 docs
- ◐ `docs/architecture/MASTER_BLUEPRINT.md` — the ratified design (research pass)
- ◐ `docs/architecture/adaptive-engine.md`
- ◐ `docs/architecture/speed-parallelism.md`
- ◐ `docs/architecture/licensed-tools.md`
- ◐ `docs/architecture/oss-combination-matrix.md`
- ◐ `docs/architecture/fusion-confidence.md`
- ☐ data‑model / canonical entity schema · API contract · storage design · security model · observability design · cost model

## B. Country source inventories — 20 countries × ~3 = ~60 docs
For each of SE, NO, DK, FI, IS, DE, AT, CH, NL, BE, LU, FR, IT, ES, PT, GB, IE, PL, CZ, HU:
- ☐ `country-data/<cc>.md` — registry, UBO, financials, contacts, vehicles, language/NER, bypass (research pass fills these)
- ☐ `country-data/<cc>-compliance.md` — per‑jurisdiction GDPR/B2B rules
- ☐ `country-data/<cc>-coverage.md` — expected record counts + source reliability

## C. Per‑source scraper runbooks — ~120 docs
One runbook per entry in `sources/sources.yaml` (registries, aggregators, directories, vehicle registries, financial portals): discovery → selectors/endpoints → pagination → WAF profile → rate envelope → fields → fallback chain → refresh cadence. As sources scale to hundreds, so do these.

## D. Method runbooks — ~85 docs (one per catalogued repo)
From [`catalog/OPEN_SOURCE_TOOLS_CATALOG.md`](catalog/OPEN_SOURCE_TOOLS_CATALOG.md): `catalog/methods/<method>.md` — what it does, install, config, integration snippet, speed/accuracy, gotchas, where it sits in the fallback chain.

## E. ICP / sales‑intelligence tool profiles — ~50 docs
`catalog/icp-tools/<tool>.md` for **every** ICP tool worldwide (Apollo, ZoomInfo, Cognism, Lusha, Seamless.ai, Clearbit, Lead411, RocketReach, Hunter, Kaspr, Cognism, Adapt, UpLead, LeadIQ, Wiza, Datanyze, Demandbase, 6sense, Bombora, Ocean.io, Surfe, Dropcontact, Lemlist, …). Each: data sources, coverage, accuracy claims vs reality, pricing, API surface, **what we can learn**, and the *legitimate* benchmarking method (see COMPLIANCE.md — **profiling, not data exfiltration**).

## F. Open‑source AI agent / automation frameworks — ~50 docs
`catalog/ai-agents/<framework>.md` for every free OSS agent framework usable as a worker brain: LangGraph, CrewAI, AutoGen, AG2, OpenHands, SmolAgents, Llama‑Index agents, Haystack, Semantic Kernel, DSPy, Browser‑Use, Skyvern, LaVague, Stagehand, Agent‑E, WebVoyager, etc. — plus local LLM runtimes (Ollama, vLLM, llama.cpp) and open models (Llama, Qwen, Mistral, DeepSeek). Each: role in the platform, hardware, integration.

## G. UI‑automation & OCR‑capture design — ~20 docs
`docs/ui-automation/` — driving stubborn portals by **clicks in the UI** and reading results by **OCR**, *for primary sources that have no API* (DE Handelsregister, IT Registro Imprese, etc.):
- computer‑use / RPA architecture (UiPath + Ranorex + Playwright + browser‑use agents)
- OCR capture pipeline (screen → PaddleOCR/Tesseract → NER → structured)
- visual element recognition + self‑healing selectors
- when UI‑automation beats HTTP (and the seat‑limit economics)

## H. Infrastructure & ops — ~15 docs (mostly drafted)
Docker/K8s, worker image, autoscaling, monitoring, proxy fabric, secrets, DR, on‑call runbooks.

## I. Data quality & fusion — ~12 docs
Entity resolution, agreement scoring, validation (email/phone/web), freshness/decay, dedup, golden‑record rules.

## J. Compliance & legal — ~25 docs
Master posture (drafted) + per‑country GDPR notes + DPA templates + suppression‑list design + provenance schema + RoPA + erasure runbook.

## K. Product & GTM — ~15 docs
Positioning vs incumbents, pricing, API docs, onboarding, SLAs, the "honest accuracy" narrative.

## L. Build plans — ~10 docs
Phased roadmap (drafted) + per‑phase work breakdowns + test plans + acceptance criteria.

---

**Estimated total: ~470 documents.** Families A, B, C, E, F, G are being produced by orchestrated research passes; the rest are authored as the design firms up. This file is the live index — update status markers as docs land.
