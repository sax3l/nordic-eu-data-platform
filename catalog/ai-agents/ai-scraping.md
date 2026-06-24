# AI scraping & extraction brains — OSS catalog

> Catalog of free / open-source AI tooling evaluated as the "AI brains" of our self-adapting
> data-harvesting platform. Star counts and licences confirmed via web search on **2026-06-24**
> (GitHub counts move; treat as approximate). All entries are self-hostable at **zero licence
> cost** unless noted.

## Compliance frame (read first)

Per `docs/COMPLIANCE.md`, the AI capabilities below are for **T1–T4 work**: primary official
registries, open-data portals, aggregator APIs we are licensed to use, public directories
(rate-limited, GDPR-tagged), and the open web (robots.txt + limits respected). The
**UI-automation + AI-vision tools (ScrapeGraphAI/Crawl4AI browser mode, llm-scraper) are for
PRIMARY OFFICIAL sources with no API** — e.g. DE Handelsregister, IT Registro Imprese — and
**never** for driving a logged-in competitor ICP tool (Apollo/ZoomInfo/Cognism). Competitor tools
stay T5: feature/pricing intel + small ToS-permitted accuracy benchmarks of our *own* accounts
only. No OCR/UI exfiltration of competitor databases. That is a hard line.

## Where these fit in our architecture

Our platform is an **adaptive router → worker pool**:

- **Adaptive router** picks, per (source, page-type), the cheapest extraction path that hits a
  quality bar, and escalates on failure: *static parse → markdown+schema LLM extract →
  headless browser + AI actions → human review*. It also throttles on `429`/`Retry-After`.
- **Worker pool** runs the chosen path. Workers are stateless; they pull a job
  (URL + target schema + tier policy) and return **structured records + provenance**
  (source URL, lawful basis tag, extracted-at, model/tool + version, confidence).

The tools below slot into four roles: **(A) crawl/fetch + AI navigation**, **(B) structured
extraction from a page/doc**, **(C) document/OCR parsing** for PDF-only registries, and
**(D) the constrained-decoding / NER substrate** that makes B and C reliable and cheap on local
GPUs.

---

## A. Crawl, fetch & AI navigation

### Crawl4AI
- **Repo:** https://github.com/unclecode/crawl4ai · ~60k★
- **License:** Apache-2.0 (fully permissive — safe to embed/modify in a commercial SaaS).
- **What it does:** LLM-friendly async crawler/scraper. Renders JS via Playwright, emits clean
  markdown tuned for LLM input, supports CSS/XPath *and* LLM-based extraction strategies,
  session reuse, hooks, proxy rotation, and a `429`-aware rate limiter.
- **Where it fits:** The **default fetch + markdownify layer** for every worker. Its markdown
  output is what we feed to the schema-extraction tier, so cheap static jobs never invoke an LLM.
- **Hardware/cost:** CPU-only for fetch+markdown; a headless-Chromium footprint (~0.5–1 GB RAM
  per concurrent browser). $0 licence. Marginal cost = optional LLM calls you choose to make.
- **Maturity:** Very high — most-starred crawler on GitHub, active, well-documented, Docker image.
- **Integration note:** Make Crawl4AI the **rung-1/rung-2 fetcher** in the router. Run it as the
  worker's HTTP/browser engine; pass its markdown to Instructor/Outlines for extraction. Its
  built-in rate limiter must be wired to the router's global per-domain budget so robots/`429`
  signals are honoured platform-wide, not just per worker.

### ScrapeGraphAI
- **Repo:** https://github.com/ScrapeGraphAI/Scrapegraph-ai · ~20k★
- **License:** MIT (fully permissive).
- **What it does:** Builds scraping **pipelines as graphs**; you give a prompt + a source
  (URL or local HTML/XML/JSON/markdown) and it orchestrates fetch → parse → LLM-extract.
  Works with OpenAI, local Ollama, Azure, etc. `SmartScraperGraph` / `SearchGraph` /
  `OmniScraperGraph` cover single-page, search-driven, and multimodal variants.
- **Where it fits:** **Orchestrating-agent option for stubborn, schema-fuzzy T4 pages** where we
  don't yet know the selector and want an LLM to plan the extraction. A higher rung than raw
  Crawl4AI; good for one-off / long-tail official sources where authoring a parser isn't worth it.
- **Hardware/cost:** Pipeline logic is light; cost is the LLM (point it at local Ollama to stay
  $0). Headless browser optional.
- **Maturity:** High — large community, MIT, actively maintained; a managed API exists but the
  OSS lib stands alone.
- **Integration note:** Wrap a `SmartScraperGraph` as a **router rung-3 worker** ("AI-planned
  extract"). Pin its LLM to our local model server so it never silently calls a paid API. Cache
  the inferred selector path so repeat pages on the same domain fall back to the cheap static rung.

### llm-scraper
- **Repo:** https://github.com/mishushakov/llm-scraper · ~4.7k★
- **License:** MIT.
- **What it does:** TypeScript library: turns any Playwright **page** into structured data via a
  Zod/JSON schema. v2 ships Vercel AI SDK 6 support; supports code-generation mode (emit a reusable
  scraping function) and works with local models.
- **Where it fits:** Our **AI-clicks / stubborn-UI path** in the Node/TS side of the worker pool.
  Because it operates on a live Playwright page, it's the tool for **PRIMARY OFFICIAL sources that
  need real interaction** — pagination, form submit, "search then read" flows on registries with no
  API (DE Handelsregister, IT Registro Imprese). Its codegen mode lets us *promote* a one-shot AI
  extraction into a cached deterministic scraper (cost collapses to $0 LLM on repeat runs).
- **Hardware/cost:** Node + Playwright (Chromium RAM as above). LLM optional/local. $0 licence.
- **Maturity:** Medium-high — popular, MIT, active; smaller surface than the Python options.
- **Integration note:** Use for TS workers that already drive Playwright; feed the same Zod schema
  the router stores per source. **Codegen output is the key lever:** persist generated functions so
  the router demotes the source to the deterministic rung after first success. Keep it strictly on
  T1/official targets per compliance.

### Firecrawl (OSS)
- **Repo:** https://github.com/firecrawl/firecrawl (a.k.a. mendableai/firecrawl) · ~50k★ core repo
  (project-wide marketing cites higher).
- **License:** **AGPL-3.0** for the core (SDKs MIT). ⚠️ See note.
- **What it does:** "URL → clean LLM-ready markdown/structured data" with crawl, scrape, search,
  and `/extract`. Strong at JS-heavy sites, batching, and schema extraction.
- **Where it fits:** Capable alternative to Crawl4AI for the fetch+markdown+extract rung; nice
  `/extract` ergonomics.
- **Hardware/cost:** Self-host stack (API + workers + Redis + Playwright); heavier to operate than
  a library. $0 licence but **AGPL**.
- **Maturity:** Very high — one of the largest repos in the space, fast-moving.
- **Integration note / caveat:** **AGPL-3.0 is the catch.** If we self-host and expose *any*
  network service built on a modified Firecrawl, the AGPL network-use clause obliges us to release
  our modifications. For a commercial EU SaaS that's a real obligation. **Recommendation: prefer
  Apache-2.0 Crawl4AI as the default engine**; keep self-hosted Firecrawl only as an *unmodified*
  drop-in fallback, or isolate it behind a process boundary so it doesn't pull our proprietary
  router code under AGPL. Legal sign-off before it touches our codebase.

---

## B. Structured-extraction substrate (the reliability layer)

### Instructor
- **Repo:** https://github.com/567-labs/instructor · ~11k★ (orig. jxnl/Jason Liu)
- **License:** MIT.
- **What it does:** Structured outputs for LLMs via **Pydantic** models — validation, automatic
  retries on schema-violation, streaming partials. Multi-provider (OpenAI, Anthropic, Cohere,
  Ollama/local via LiteLLM), multi-language.
- **Where it fits:** The **canonical "page-markdown → typed record" call** across the whole worker
  pool. Every rung that uses an LLM (ScrapeGraphAI, Crawl4AI LLM-extract, doc pipelines) should
  return through an Instructor-validated Pydantic model so the record either conforms or triggers a
  controlled retry/escalation.
- **Hardware/cost:** Library only; cost = underlying model (free against local Ollama). $0 licence.
- **Maturity:** Very high — 3M+ monthly downloads, the de-facto standard.
- **Integration note:** Define **one Pydantic schema per source/record type** (company, officer,
  filing) with the provenance fields baked in (source, lawful_basis, extracted_at, confidence).
  Instructor's retry hook is where the router decides "re-ask vs escalate to browser rung vs
  human." This is plumbing every other tool plugs into.

### Outlines
- **Repo:** https://github.com/dottxt-ai/outlines · ~11k★ (web cites 8k+; trending higher)
- **License:** Apache-2.0.
- **What it does:** **Constrained / structured generation** — forces a *local* model's tokens to
  conform to a JSON Schema, regex, or context-free grammar at decode time. Output is guaranteed
  valid by construction, not by post-hoc parsing.
- **Where it fits:** The reliability backbone for **local cheap inference**. Where Instructor
  validates-and-retries (great for hosted APIs), Outlines makes a **self-hosted GPU model emit
  valid JSON on the first pass**, which is what makes large-scale local extraction affordable.
- **Hardware/cost:** Runs with vLLM/transformers/llama.cpp on our GPU box; $0 licence. Pairs with
  a 7–8B local model for the bulk tier.
- **Maturity:** High — backed by .txt, widely used in serving stacks (`outlines-core` in Rust).
- **Integration note:** Make Outlines the decoding layer of our **local model server** behind the
  cheap extraction rung. Router policy: small/known schemas + high volume → local model + Outlines;
  fuzzy/novel pages → hosted model + Instructor. Same Pydantic/JSON schema feeds both, so the rung
  swap is transparent to the worker.

### GLiNER
- **Repo:** https://github.com/urchade/GLiNER · ~3.2k★
- **License:** Apache-2.0 (models on HF Apache-2.0).
- **What it does:** Generalist, lightweight **zero-shot NER**. Define entity labels at runtime
  (`company_name`, `org_number`, `vat_id`, `officer_name`, `jurisdiction`) and it extracts them
  with no training data. Runs on **CPU**; competitive with much larger LLMs on NER benchmarks.
- **Where it fits:** **Rung-0 / pre-LLM cheap extraction.** For the high-volume, entity-shaped
  fields that dominate company data, GLiNER pulls them on CPU for ~zero marginal cost — reserving
  LLM calls for genuinely unstructured pages. Also a cross-check/validator over LLM output.
- **Hardware/cost:** CPU-friendly, tiny footprint; ideal to colocate on workers. $0 licence.
- **Maturity:** Medium-high — NAACL 2024 paper, active, well-adopted.
- **Integration note:** Put GLiNER as the **first extraction attempt** in the router for
  entity-dense pages/registry text; if it returns confident, complete entities we skip the LLM
  entirely. Great fit for our GDPR tagging too — label runs are explicit per field. Belongs on
  every worker as a cheap local capability.

---

## C. Document / PDF / OCR parsing (registry filings)

Many primary registries (annual reports, filings, scanned officer docs) are **PDF-only**. These
turn documents into clean structured text the B-layer can extract from.

### Docling
- **Repo:** https://github.com/docling-project/docling (IBM DS4SD; now LF AI & Data) · ~62k★
- **License:** MIT (code; individual model licences apply).
- **What it does:** Document conversion for gen-AI: advanced PDF understanding (layout, reading
  order, tables), plus DOCX/PPTX/XLSX/HTML/EPUB/images and even audio. Outputs structured
  markdown/JSON with layout fidelity; strong table extraction.
- **Where it fits:** The **default doc-ingestion stage** of the document worker. Registry PDF →
  Docling → markdown/JSON → Instructor/Outlines → typed record.
- **Hardware/cost:** CPU works; GPU accelerates layout models. $0 licence, MIT.
- **Maturity:** Very high — IBM-originated, huge adoption, foundation-governed.
- **Integration note:** Make Docling the **C-rung** feeding the same schema pipeline as the web
  rungs. Prefer it over heavier OCR when the PDF has a usable text/layout layer. Tables → our
  financial fields with minimal post-processing.

### Marker
- **Repo:** https://github.com/datalab-to/marker · ~36k★
- **License:** ⚠️ **GPL-3.0 (code)** + **modified AI-Pubs OpenRAIL-M (model weights)** — the RAIL
  licence is **free only** for research/personal/startups under **$2M funding/revenue**, paid
  otherwise.
- **What it does:** Fast, high-accuracy PDF/image/PPTX/DOCX/XLSX → markdown/JSON/HTML, with strong
  tables, equations, inline math, references.
- **Where it fits:** A high-accuracy alternative to Docling for difficult/scanned filings.
- **Hardware/cost:** GPU recommended for throughput. $0 *only under the RAIL eligibility cap*.
- **Maturity:** High — very popular, actively released.
- **Integration note / caveat:** **Licensing risk for a commercial platform.** GPL-3.0 on the code
  plus a revenue-capped model licence means Marker is **not a safe default** for a sellable EU SaaS
  once we exceed the cap. **Recommendation: use Docling (MIT) as the default doc engine**; keep
  Marker only for offline/research evaluation or behind a clear licence purchase. Needs legal
  sign-off before production use.

### unstructured (unstructured.io OSS)
- **Repo:** https://github.com/Unstructured-IO/unstructured · ~14k★
- **License:** Apache-2.0 (OSS lib; the hosted Platform/Serverless is the paid product).
- **What it does:** Open-source **ETL/partitioning** for 50+ file types (PDF, HTML, DOCX, images,
  email…) into normalized "elements," with chunking/cleaning helpers. The connector ecosystem
  (S3, SharePoint, GDrive…) is broad.
- **Where it fits:** **Normalization + ingestion glue** when our document sources are heterogeneous
  (mixed PDF/HTML/email/office) and we want one partitioning API + many source connectors before
  the extraction tier.
- **Hardware/cost:** CPU works; some models pull extra deps. $0 licence (Apache-2.0).
- **Maturity:** High — long-standing, widely used; note the OSS lib lags the paid Platform on the
  newest parsing quality.
- **Integration note:** Use as the **multi-format intake normalizer** ahead of Docling/extraction
  when a source dumps mixed document types, or to reuse its connectors. For pure PDF-layout quality,
  Docling generally wins; `unstructured` wins on breadth + connectors.

### ExtractThinker
- **Repo:** https://github.com/enoch3712/ExtractThinker · ~1.6k★
- **License:** Apache-2.0.
- **What it does:** Document-intelligence **orchestration ("ORM for documents")**: classify →
  split → load (Tesseract/Azure/Textract/Docling) → extract into Pydantic contracts, async, with
  multi-LLM support (OpenAI, Anthropic, Cohere, Ollama).
- **Where it fits:** A **ready-made IDP pipeline framework** that ties C-layer loaders to B-layer
  Pydantic extraction with classification/splitting built in — i.e. it can *be* our document-worker
  controller rather than us hand-wiring Docling+Instructor.
- **Hardware/cost:** Library; cost = chosen loader + LLM (local Ollama → $0). Apache-2.0.
- **Maturity:** Medium — smaller but active and purpose-built for IDP; permissive licence.
- **Integration note:** Evaluate as the **orchestrator for the document worker**: plug Docling as
  its loader and our Pydantic contracts as its extraction target, so classification/splitting of
  multi-doc filings comes for free. If we'd otherwise hand-roll that glue, ExtractThinker is the
  shortcut; if not, Docling+Instructor directly is leaner.

---

## Adoption decision (router/worker mapping)

| Role in router | Default (adopt now) | Why default | Alt / conditional |
|---|---|---|---|
| Fetch + markdown (rung 1–2) | **Crawl4AI** (Apache-2.0) | Permissive, huge, `429`-aware | Firecrawl — AGPL, fallback only |
| Typed record from LLM (all rungs) | **Instructor** (MIT) | De-facto standard, retries+validation | — |
| Local cheap decode (bulk rung) | **Outlines** (Apache-2.0) | Guaranteed-valid JSON on local GPU | — |
| Entity pre-extract (rung 0) | **GLiNER** (Apache-2.0) | CPU, zero-shot, skips the LLM | — |
| AI-planned web extract (rung 3) | **ScrapeGraphAI** (MIT) | Prompt-driven, local-model-able | — |
| Stubborn official UI (TS workers) | **llm-scraper** (MIT) | Playwright + codegen → cache | — |
| PDF/doc parse (C-rung) | **Docling** (MIT) | MIT, best-in-class layout/tables | Marker — GPL+RAIL cap, gated |
| Multi-format intake | **unstructured** (Apache-2.0) | Breadth + connectors | — |
| Document-worker orchestration | evaluate **ExtractThinker** (Apache-2.0) | Free IDP glue | else Docling+Instructor |

**Licence guardrails:** avoid **Firecrawl (AGPL-3.0)** and **Marker (GPL-3.0 + revenue-capped
RAIL)** as defaults in the sellable SaaS; both need legal sign-off and isolation. Everything else
is MIT/Apache-2.0 and safe to embed.

---

### Sources
- Crawl4AI — https://github.com/unclecode/crawl4ai
- ScrapeGraphAI — https://github.com/ScrapeGraphAI/Scrapegraph-ai
- llm-scraper — https://github.com/mishushakov/llm-scraper
- Firecrawl — https://github.com/firecrawl/firecrawl
- Instructor — https://github.com/567-labs/instructor
- Outlines — https://github.com/dottxt-ai/outlines
- GLiNER — https://github.com/urchade/GLiNER
- Docling — https://github.com/docling-project/docling
- Marker — https://github.com/datalab-to/marker
- unstructured — https://github.com/Unstructured-IO/unstructured
- ExtractThinker — https://github.com/enoch3712/ExtractThinker

*Catalogued 2026-06-24. Stars approximate; verify licences against the repo at integration time.*
