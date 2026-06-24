# Tooling catalog

The arsenal — every open‑source repo, bypass technique, browser, OCR engine, NER model, ICP competitor, local LLM engine, and AI‑agent framework the platform can call on.

| File / dir | What |
|---|---|
| [`OPEN_SOURCE_TOOLS_CATALOG.md`](OPEN_SOURCE_TOOLS_CATALOG.md) | 85+ OSS repos across 10 categories (the master list) |
| [`cloudflare_waf_bypass_repos_2026.md`](cloudflare_waf_bypass_repos_2026.md) | CF / DataDome / Akamai bypass repos |
| [`headless_browser_automation_catalog.md`](headless_browser_automation_catalog.md) | Headless browsers + stealth |
| [`GITHUB_REPOSITORY_SEARCH_REPORT.md`](GITHUB_REPOSITORY_SEARCH_REPORT.md) | Raw GitHub search findings |
| [`methods/`](methods/) | **13 operational runbooks** — how we actually use each tool |
| [`methods/stealth-bypass-chain.md`](methods/stealth-bypass-chain.md) | **Complete anti-detection strategy** (8 escalation levels) |
| [`methods/cloakbrowser.md`](methods/cloakbrowser.md) | CloakBrowser — C++ stealth Chromium (30/30 benchmarks) |
| [`methods/crawlee.md`](methods/crawlee.md) | Crawlee — production crawler framework (Apify OSS) |
| [`methods/flaresolverr.md`](methods/flaresolverr.md) | FlareSolverr — Cloudflare challenge solver |
| [`methods/rota-proxy.md`](methods/rota-proxy.md) | Rota — proxy rotation engine + Tor integration |
| [`methods/unstructured.md`](methods/unstructured.md) | Unstructured.io — PDF/HTML/DOCX → structured data |
| [`methods/ocr-pipeline.md`](methods/ocr-pipeline.md) | OCR cascade (PaddleOCR → Surya → GOT-OCR2 → Vision LLM) |
| [`methods/lmstudio-ollama.md`](methods/lmstudio-ollama.md) | LM Studio + Ollama + vLLM — local LLM infra |
| [`methods/browser-use.md`](methods/browser-use.md) | Browser-Use / Skyvern / Stagehand — AI-driven browser |
| [`methods/openclaw.md`](methods/openclaw.md) | OpenClaw — AI assistant gateway integration |
| [`methods/account-creation.md`](methods/account-creation.md) | Account creation pipeline + credential vault |
| [`icp-tools/`](icp-tools/) | Profiles of every ICP / sales‑intelligence tool (benchmark intel) |
| [`ai-agents/`](ai-agents/) | Every free OSS AI agent / automation framework |

## Infrastructure

| File | What |
|---|---|
| [`../docs/infrastructure/docker-compose.full-stack.yml`](../docs/infrastructure/docker-compose.full-stack.yml) | **Complete local deployment** (15+ services: Redis, Postgres, Ollama, CloakBrowser, FlareSolverr, Unstructured, proxy rotator, Tor pool, Prometheus, Grafana) |

## Example Scripts

| File | What |
|---|---|
| [`../examples/extraction_pipeline.py`](../examples/extraction_pipeline.py) | **Full extraction pipeline**: Crawlee → Unstructured → spaCy NER → Ollama LLM enrichment → Postgres |

## Quick Start

```bash
# Full local stack (free, no API keys needed)
docker compose -f docs/infrastructure/docker-compose.full-stack.yml up -d

# Run the example pipeline
pip install crawlee playwright unstructured-client spacy openai psycopg2-binary
python examples/extraction_pipeline.py
```

The flat catalogs answer *"what exists"*. The `methods/` runbooks answer *"how we chain them"* — where the OSS combination matrix gets operationalised into per‑situation tool‑chains with fallbacks.
