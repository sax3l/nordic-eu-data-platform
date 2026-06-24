# Nordic + EU Adaptive Data Platform

> An adaptive, self‑healing, maximally‑parallel B2B data‑harvesting platform covering **every company, contact person, website and vehicle** across the Nordics and the major European markets — built to out‑cover and out‑honest Apollo / Cognism / ZoomInfo / LinkedIn Sales Navigator.

**Status:** 🚧 Design + documentation phase. **13 operational runbooks, 85+ OSS tool catalog, docker-compose full‑stack, example pipeline.** Code lands once the blueprint is ratified.

**Live repo:** https://github.com/sax3l/nordic-eu-data-platform

---

## The thesis

Incumbent ICP tools (Apollo, Cognism, ZoomInfo, Lusha, …) advertise 90‑97% accuracy and deliver 62‑70% in independent testing (see [`docs/competitive/`](docs/competitive/)). Their moat is *scale + UX*, not *correctness* — and almost none of their underlying data is proprietary. The opportunity:

1. **Adaptive multi‑method harvesting** — sense which method works per target and adapt method *and* speed in real time; auto‑correct blocks/errors.
2. **Source‑racing** — fire the cheapest source and the deep scrape together, take the first good answer, cancel the slow one → combining sources raises *speed*, not just coverage.
3. **Every market, every primary source** — 20 Nordic + EU national registries, vehicle registries, financial filings, and the public web, fused on a cross‑border key (LEI/GLEIF).
4. **Honest, GDPR‑native confidence** — per‑field provenance, multi‑source agreement scoring, freshness/decay tracking. This is the EU moat the US tools cannot match.

## Quick Start (Local, Free, No API Keys)

```bash
git clone https://github.com/sax3l/nordic-eu-data-platform
cd nordic-eu-data-platform

# Launch full stack (15+ services)
docker compose -f docs/infrastructure/docker-compose.full-stack.yml up -d

# Run example pipeline
pip install crawlee playwright unstructured-client spacy openai psycopg2-binary
python examples/extraction_pipeline.py
```

## Tech Stack (All FOSS, All Local)

| Layer | Primary | Fallback |
|---|---|---|
| **Browser stealth** | CloakBrowser (C++ patched Chromium) | Playwright + stealth plugins |
| **Orchestration** | Crawlee (Apify OSS) | Scrapy |
| **CF/WAF bypass** | FlareSolverr | cloudscraper → Camoufox → Botasaurus |
| **Proxy rotation** | Rota + Tor pool | HAProxy + free lists |
| **Document parsing** | Unstructured.io | pdfplumber, PyMuPDF |
| **OCR** | PaddleOCR → Surya → GOT-OCR2 | Vision LLM (Qwen3-VL) |
| **NER** | spaCy (sv/de/fr/it/es bundles) | GLiNER → Transformers |
| **LLM (local)** | Ollama (Qwen2.5-14B, Phi-4-14B) | vLLM (high-throughput) |
| **AI agents** | Browser-Use (81% CF bypass) | Skyvern, Stagehand |
| **Database** | PostgreSQL + pgvector | Redis (queue/cache) |
| **Monitoring** | Prometheus + Grafana | — |
| **Licensed tools** | Screaming Frog · Sequentum · UiPath · Ranorex | (seat-limited pool) |

## Repository map

| Path | What's in it |
|---|---|
| [`docs/architecture/`](docs/architecture/) | The 5 architecture pillars + the **MASTER_BLUEPRINT** |
| [`docs/competitive/`](docs/competitive/) | Apollo / Cognism / LinkedIn / ZoomInfo teardown + ICP landscape |
| [`docs/infrastructure/`](docs/infrastructure/) | Docker / Kubernetes / worker / monitoring guides + **`docker-compose.full-stack.yml`** |
| [`docs/pipelines/`](docs/pipelines/) | Web‑extraction + NER pipeline spec |
| [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) | **Read first.** Legal posture, source tiers, the hard lines |
| [`catalog/`](catalog/) | 85+ OSS repos, CF/WAF bypasses, headless browsers |
| [`catalog/methods/`](catalog/methods/) | **13 operational runbooks** (how we chain tools together) |
| [`catalog/methods/stealth-bypass-chain.md`](catalog/methods/stealth-bypass-chain.md) | **Complete 8-level anti-detection escalation** |
| [`catalog/methods/cloakbrowser.md`](catalog/methods/cloakbrowser.md) | CloakBrowser integration (C++ stealth, 30/30 benchmarks) |
| [`catalog/methods/unstructured.md`](catalog/methods/unstructured.md) | Unstructured.io document parsing pipeline |
| [`catalog/methods/lmstudio-ollama.md`](catalog/methods/lmstudio-ollama.md) | Local LLM infrastructure (free, no API keys) |
| [`catalog/methods/browser-use.md`](catalog/methods/browser-use.md) | AI agents for browser automation |
| [`catalog/methods/ocr-pipeline.md`](catalog/methods/ocr-pipeline.md) | 6-level OCR cascade |
| [`catalog/methods/account-creation.md`](catalog/methods/account-creation.md) | Automated signup + credential vault |
| [`catalog/icp-tools/`](catalog/icp-tools/) | Every ICP / sales‑intelligence tool in the world (profiles) |
| [`catalog/ai-agents/`](catalog/ai-agents/) | Every free open‑source AI agent / automation framework |
| [`examples/extraction_pipeline.py`](examples/extraction_pipeline.py) | **Full pipeline example** (Crawlee → Unstructured → spaCy → Ollama → Postgres) |
| [`sources/`](sources/) | **The source registry** — every website with recurring data |
| [`country-data/`](country-data/) | Verified per‑country source inventories (20 markets) |
| [`src/`](src/) | Implementation (orchestrator, scrapers, ocr, ner, fusion, ui‑automation) |
| [`plans/`](plans/) | Roadmap + [`DOCUMENTATION_PLAN.md`](DOCUMENTATION_PLAN.md) |

## The 5 architecture pillars

1. **Adaptive self‑healing engine** — multi‑armed‑bandit method router, AIMD adaptive concurrency, failure classifier → auto‑remediation, coherent identity rotation.
2. **Maximum‑speed parallelism** — distributed work fabric, source‑racing / hedged requests, batched OCR/NER, queue‑depth autoscaling.
3. **OSS combination matrix** — ordered tool‑chains per situation (static → CF → CloakBrowser → AI Agent → RPA → OCR → NER → dedup).
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
