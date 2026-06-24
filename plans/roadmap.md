# Build roadmap

Phased so each phase ships a usable product and de‑risks the next.

## Phase 0 — Nordic MVP (the proof)
**Markets:** SE, NO, DK, FI · **Why first:** open bulk registries → fastest, cleanest, lowest legal risk.
- Orchestrator skeleton + adaptive router (HTTP tier only) + Redis/Celery queue.
- Sources: Bolagsverket, brreg (open API), CVR/Virk, PRH/avoindata + allabolag/hitta directories.
- OCR (PaddleOCR→Tesseract) + spaCy NER (sv/no/da/fi models).
- Fusion v1: GLEIF/orgnr keying, RapidFuzz dedup, email MX + phone (libphonenumber) validation, agreement scoring.
- GDPR plumbing: provenance + last‑verified + erasure from day one.
- **Exit:** ~3.5M Nordic companies + contacts + websites, scored, queryable via API.

## Phase 1 — DACH + Benelux + France
- Add browser tier (undetected‑playwright + stealth) and **licensed‑tool tier** (Screaming Frog bulk site crawl; UiPath for DE Handelsregister; Sequentum for JS‑heavy aggregators).
- Sources: SIRENE open bulk (FR — huge), KVK (NL), KBO (BE), Handelsregister/Bundesanzeiger/North Data (DE/AT/CH), RDW (NL vehicles, open).
- Source‑racing online (cheap API cancels slow scrape).
- Multilingual NER (de/fr/nl). k8s + queue‑depth autoscaling.
- **Exit:** ~20M companies; vehicle data live for NL/Nordic.

## Phase 2 — Full EU + scale
- Southern (IT/ES/PT) + British Isles/Central (UK/IE/PL/CZ/HU). UK Companies House + DVLA (open) are easy wins; IT/ES via aggregators + gazette deltas.
- ICP‑tool benchmarking harness (legitimate sampling — see COMPLIANCE.md) to publish "our accuracy vs theirs".
- OSS AI‑agent workers for stubborn portals (browser‑use / Skyvern + OCR capture).
- Full observability, cost controls, DR.
- **Exit:** ~40M companies across 20 markets; honest, provenance‑tracked, GDPR‑native — the Apollo/Cognism alternative.

## Always‑on workstreams
Compliance (per‑country) · freshness re‑harvest scheduling · proxy/identity fabric health · accuracy QA vs ground truth.
