# Catalog gaps — completeness critique

> Critic pass over `catalog/icp-tools/`, `catalog/ai-agents/`, and `docs/ui-automation/` on 2026-06-24.
> Each item is something **notable and missing**, with a one-line reason it matters. Priority: **P1** = clear hole a reviewer would flag immediately; **P2** = worth adding for completeness; **P3** = nice-to-have / watch.
> Compliance frame unchanged: competitor ICP tools stay **T5 (benchmark/feature-intel only)**; UI/OCR capability is for **T1 primary official sources**, never competitor logins (per `docs/COMPLIANCE.md`).

The four ICP batches (42 tools) and four AI-agent batches are genuinely strong. The gaps below are the tools/capabilities a domain expert would notice are absent, not padding.

---

## (a) Missing ICP / sales-intelligence tools

### P1 — would be flagged immediately
- **Bright Data** — the elephant: largest proxy + web-data-collection platform, the named migration target for ex-Proxycurl users (already cited in `data-providers.md`!) yet never profiled. Core to any "where does scraped substrate come from" map.
- **Apify** — the dominant actor/scraper marketplace (incl. LinkedIn/company actors); the other Proxycurl-migration destination named in our own doc but not profiled. Defines the "rent-a-scraper" tier.
- ** On Surfe/Wiza/Kaspr but **Sales-Nav-scraper / LinkedIn-data resellers as a class** — at least **Evaboot** and **PhantomBuster/TexAu** (LinkedIn automation suites) deserve a profile as the T5 ToS-risk archetype we explicitly position against.
- **Nordic/DACH registry-grounded rivals beyond Vainu/Dealfront** — **Bisnode/Dun & Bradstreet Nordic**, **Enento/Bisnode (UC, Asiakastieto)**, **Proff/Allabolag/Largestcompanies (NHST/Bonnier)**. These ARE our home-turf incumbents; their absence is the biggest EU-coverage hole given the platform's Nordic thesis.
- **D&B / Dun & Bradstreet (D-U-N-S)** and **Bureau van Dijk / Moody's Orbis** — the global firmographic reference databases every enterprise buyer benchmarks against. No serious "data-providers" map is complete without them.

### P2 — worth adding
- **Sales-engagement / signals not yet covered:** **HubSpot Sales Hub & Salesforce/Sales Cloud (incl. Data Cloud)** as the CRM-native competition; **Salesforce** is the gravity well every tool integrates into.
- **Warmly, Clearbit-style reverse-IP rivals:** **RB2B** (person-level US de-anon), **Vector**, **Koala** — the 2025–26 "website visitor → person" wave that 6sense/Albacross only do at account level.
- **Intent beyond Bombora:** **G2 Buyer Intent**, **TrustRadius**, **Gartner Digital Markets** — review-site intent, a distinct signal class from Bombora's co-op.
- **Cognism's true peers missed:** **SalesQL**, **ContactOut**, **Datagma**, **Nymeria** — the LinkedIn-email cluster; and **Leadfeeder** is folded into Dealfront but **Visitor Queue / Leadinfo / Dealsignal** are separate EU visitor-ID players.
- **Email-verification-as-a-service** (the layer *under* every finder): **ZeroBounce, NeverBounce, Bouncer, MillionVerifier, Emailable** — we cite ZeroBounce benchmarks but never profile the verification commodity our own bounce-SLA depends on.
- **Crunchbase peer:** **Tracxn, Dealroom (EU/Amsterdam — directly on-thesis), CB Insights** — startup/funding intelligence; Dealroom is the EU-native funding-signal source we should know cold.

### P3
- **AI-SDR / autonomous-outbound agents** (a fast-rising *category* entirely absent): **11x (Alice), Artisan (Ava), Qualified (Piper), Relevance AI, Clay's Claygent**. These reframe the buyer from "data tool" to "AI rep" — a strategic threat the catalog doesn't yet acknowledge.
- **Regional long-tail:** **Sales.Rocks, Cebes/Echobot legacy, Kompass, Europages, Creditsafe** (EU credit+firmographic).

---

## (b) Missing OSS AI-agent / browser-automation / local-LLM / extraction frameworks

### P1
- **Playwright/Selenium are assumed but never first-classed**, and **Patchright / undetected-playwright / nodriver / camoufox** appear only in `methods/` — the **stealth-browser layer** (the actual anti-bot survival kit) is missing from `ai-agents/browser-ai.md`, which jumps straight to AI agents over a clean browser. That's the biggest practical hole for real registry/anti-bot work.
- **LiteLLM** — the universal OpenAI-compatible proxy/router across 100+ providers + local; the glue that makes "swap engine = config change" actually true. Underpins Instructor's multi-provider claim; should be its own entry.
- **Firecrawl is covered but its main OSS peers aren't:** **Jina AI Reader (r.jina.ai)** (free URL→markdown), **Trafilatura** (best-in-class boilerplate-stripping main-content extraction, gold standard for web corpora), **Crawlee** (Apify's mature OSS crawler framework). Trafilatura in particular is a glaring omission for a harvesting platform.
- **Surya** (datalab) — SOTA OSS OCR + layout + reading-order + table detection across 90+ languages, Apache-cousin to Marker; the OCR cascade lists PaddleOCR/docTR/Tesseract but not Surya, the strongest current open OCR.

### P2
- **Structured-output / agent libs not covered:** **LangChain core** (the ecosystem LangGraph sits in — named but not profiled), **LlamaParse alternatives**, **BAML** (schema-first LLM function language, strong typed-extraction story), **Marvin** (Prefect's structured-extraction lib), **Mirascope**.
- **Local-LLM engines missing:** **TGI is excluded correctly, but **TensorRT-LLM** (NVIDIA, peak throughput), **LMDeploy**, **KTransformers**, **MLC-LLM** (cross-platform/edge), and **ExLlamaV2** (consumer-GPU quant king) are absent — `local-llm.md` covers vLLM/SGLang/llama.cpp/Ollama but skips the rest of the serving frontier.
- **Models missing:** **Qwen3-VL / InternVL3 / MiniCPM-V** (open VLMs stronger than Gemma-3 for the screenshot-extraction path the platform leans on), **Command-R/R+ (Cohere, RAG-tuned)**, **OlmoOCR**, **GOT-OCR2** (transformer OCR). The VLM gap matters because the whole UI-automation tier needs a vision brain.
- **Entity-resolution / fusion OSS** is named in `methods/` (Splink, dedupe, RapidFuzz, datasketch) but **never catalogued in `ai-agents/`** despite `fusion-confidence` being a core pillar — add **Splink** (probabilistic record linkage, the obvious EU-scale dedup engine), **dedupe.io OSS**, **Zingg**.
- **CAPTCHA / challenge handling** as a capability is absent everywhere (only "route to human" is mentioned) — even for *lawful* registry access, note the legitimate options and the hard line.

### P3
- **Agent eval/observability:** **Langfuse** (OSS LLM tracing — essential for the per-field provenance + cost telemetry the docs promise), **Phoenix/Arize**, **DeepEval**, **Ragas**. The catalog measures agents with WebVoyager/WebArena but has no production-tracing story.
- **Orchestration runtime gap:** **Temporal** is referenced in `ocr-capture.md`/architecture but never catalogued as the durable-execution backbone alongside Celery; **Prefect/Dagster** for the data-pipeline side.
- **DSPy peers:** **TextGrad**, **AdalFlow** — the auto-prompt-optimization lane has only DSPy.

---

## (c) UI / OCR design capability gaps

### P1
- **No anti-bot / fingerprinting survival section.** The RPA doc handles seats, self-heal, and CSRF beautifully but assumes the browser gets through. Missing: TLS/JA3 + canvas/WebGL fingerprint management, **stealth driver choice (Patchright/camoufox/nodriver)**, residential-proxy/geo strategy at the RPA tier. For DE Handelsregister / IT Registro Imprese this is the real failure mode, not selector rot.
- **Surya / modern VLM-OCR not in the cascade.** The OCR cascade (PaddleOCR→docTR→Tesseract→Vision-LLM) predates Surya and open VLMs (Qwen3-VL, GOT-OCR2) that can collapse layout+OCR+extraction into one pass for hard scans — at least benchmark them as a cascade tier.

### P2
- **Handwriting / signature / stamp handling** is hinted ("signature block") but there's no real design for handwritten officer signatures, stamps, or seals common in DE/IT/older Nordic filings — TrOCR or a dedicated path.
- **CAPTCHA decision tree** absent from OCR doc (it's in RPA doc only): when a scanned official source is gated by a challenge, the lawful options vs hard-no aren't specified.
- **Cost/throughput model for the Vision-LLM tier** caps cells at ≤5% but gives no **local-VLM** path (Gemma-3/Qwen3-VL on our own GPU) as the cheaper-than-frontier option the local-llm catalog argues for — the two docs aren't wired together.
- **Active-learning loop:** the human-review queue feeds nothing back. No design for using corrected fields to fine-tune GLiNER/the OCR post-processor per source (the self-improving promise the agent docs make).

### P3
- **PDF-native edge cases:** encrypted/permission-locked PDFs, PDF forms (AcroForm/XFA) with a text layer hidden behind appearance streams, and digitally-signed filings (extract + verify the signature as provenance) — none addressed.
- **Multilingual NER coverage** lists xx/de/it/sv but omits **fi/no/da/nl/pl** explicitly despite the Nordic+EU scope; name the per-language models or the GLiNER-only fallback for them.
- **Provenance for OCR**: the record schema is excellent, but there's no **W3C PROV / dataset-level lineage** story tying field-level provenance up to a sellable, auditable dataset manifest.

---

## Cross-cutting observation
The single most strategically important missing **category** (not tool) is **(P1) the autonomous AI-SDR wave** (11x, Artisan, Clay's Claygent, Relevance) — it reframes every profiled tool from "data source" to "AI rep," which is the competitive narrative shift of 2026. The single most important missing **capability** is the **stealth/anti-bot browser layer in the AI-agent + RPA docs** — without it the UI-automation tier is designed for cooperative pages, not the hostile anti-bot registries it names as targets.
