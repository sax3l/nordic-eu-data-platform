# Strategy: Parser Cascade (structured-first extraction)

**Layer:** EXTRACTION · **Component:** `extract-parser-cascade`
**Last updated:** 2026-06-24
**Builds on:** `docs/architecture/pillars/oss-combo-matrix.md` (rows 1-4, 11, 15), `docs/architecture/MASTER_BLUEPRINT_FULL.md` §4.7, §5; `catalog/OPEN_SOURCE_TOOLS_CATALOG.md` (selectolax, lxml, unstructured, PyMuPDF, pdfplumber).

---

## 1. Mechanism

Once a fetch lane has returned bytes (HTML/JSON/PDF), the parser cascade extracts fields by climbing a **cost-and-loss ladder, stopping at the first rung that yields a valid payload**. The governing rule mirrors the fetch router: the cheapest, most exact parser is tried first; only its residual escalates. The ordered rungs:

1. **Structured-state shortcut** — before any DOM walk, probe for embedded machine-readable state: `__NEXT_DATA__`, `__NUXT__`, `window.__INITIAL_STATE__`, inline JSON-LD, GraphQL/XHR JSON. Pull the `<script>` block and `orjson.loads` it. This is exact, schema-stable, and ~25-90 ms — it is the single biggest win because it returns *typed fields*, not text to re-parse.
2. **CSS/XPath rule extraction** — `selectolax` (Modest/Lexbor, ~2-5 ms/page) for CSS selectors; `lxml.html`/`etree` + `cssselect` when XPath, namespaces, or sitemap/XML are involved. Deterministic site-specific rules live in a per-`(domain, page-type)` rule registry.
3. **ML-assisted document partition** — `unstructured` (`partition_html`/`partition_pdf`) when the layout is irregular and no stable selector exists: it segments the document into typed elements (title, table, list, narrative) so downstream NER runs only on free-text residual.
4. **PDF text lane** — `PyMuPDF` (fitz) fast text extraction first; `pdfplumber` for tables (character-coordinate aware); `pdfminer.six` as the zero-dependency fallback. **Text-bearing PDFs never touch OCR.**
5. **OCR cascade** — only invoked when a page yields no extractable text layer (scanned image, empty `get_text()`). Handed off to `extract-ocr-cascade`.

A parser-memory cache records the winning rung per `(domain, page-type)`, so the next visit starts at known-good and probes one cheaper rung occasionally to detect a site simplification.

## 2. Tools / repos

`selectolax` (Lexbor backend), `lxml` + `cssselect`, `Unstructured-IO/unstructured`, `pymupdf/PyMuPDF`, `jsvine/pdfplumber`, `pdfminer.six`, `orjson` for JSON state. `publicsuffix2` for URL canonicalization at the website-field stage. Arelle is *not* here — structured XBRL filings divert to `extract-xbrl-structured-lane` before this cascade.

## 3. Failure mode it eliminates

It eliminates the **over-rendering / over-OCR failure**: the naive pipeline either spins up a headless browser or runs OCR on every document, which is 100-1000× slower and *loses precision* (OCR'd digits vs. tagged facts; rendered DOM vs. the JSON that built it). selectolax over BeautifulSoup is 10-30× (the catalog measures ~2-5 ms vs. 40-150 ms) — that delta is exactly what lets the static-HTML rung run at 100-200 concurrent workers per the blueprint. The structured-state shortcut additionally eliminates **brittle-selector failure**: when a site ships its data as embedded JSON, scraping the rendered table breaks on every redesign while the JSON contract is stable.

## 4. Composition

- **Receives from** the fetch fabric (`oss-combo-matrix` rows 1-8) and the licensed backends (Screaming Frog feeds URL frontiers + bulk-extracted rows). It is the universal post-fetch stage.
- **Diverts to `extract-xbrl-structured-lane`** for iXBRL/XBRL filings (financials) — a pre-check on content-type / `ix:` namespace routes those away before rung 4.
- **Escalates to `extract-ocr-cascade`** only on no-text-layer documents (rung 5 handoff).
- **Feeds `extract-ner-ensemble`** the free-text residual that rules couldn't structure (rung 2/3 leftover) — NER runs on the *minimum* text, not the whole page.
- **Feeds `resolve-entity-resolution` and `resolve-fusion-confidence`** each extracted field as a claim with its `method` provenance (`registry_api` | `scrape` | `inference`), which the fusion layer's reliability weights depend on.
- **Governed by** the per-source policy gate: a parser never runs on bytes from a source tagged `automated_access_forbidden`.

## 5. Success contribution

Per-target *extraction* success is a fallback cascade: `p_extract = 1 − Π(1 − pᵢ)` across rungs. With structured-state shortcut (~0.5 hit rate, ~0.99 when it hits), CSS/XPath rules (~0.9 on rule-covered pages), unstructured (~0.8 on the irregular residual), and PDF-text (~0.95 on text PDFs), the cascade pushes per-document field-extraction reliability toward ~0.97-0.99 on the lawfully-fetched set — the residual flows into OCR/NER, which catch most of what remains. Crucially it does this while *removing* compute: by answering structured pages in single-digit milliseconds it frees the browser/GPU pools for the genuinely hard tail, raising whole-pipeline throughput (blueprint's "cheapest request is the one you never make," extended to parsing).

The residual it cannot close is honest and bounded: pages whose data is genuinely absent from the lawful surface (registry-gated financials, anonymised bulk like NL KVK), which is a *coverage* limit set by law, not an extraction limit.

## 6. Compliance envelope

The parser cascade is read-only post-processing and adds no new fetch, so it inherits the lawful basis of the bytes it receives. Constraints it must honour: (a) it runs **only** on content the fetch layer was permitted to retrieve — it must not be used to re-parse archived copies of `automated_access_forbidden` sources (DE Handelsregister, ES CORPME); (b) every field it emits carries `{source_id, source_url, method, collected_at}` provenance so the output layer can enforce `lawful_basis` and `reuse_restriction` (e.g. BE KBO / DE-directory contact fields tagged `no_direct_marketing`); (c) personal-data fields (names, emails parsed from imprints) are passed through with their jurisdiction so DNC/erasure suppression applies at intake. It never bypasses a technical control — if a page is empty because a WAF served a challenge, that is a fetch-layer concern, not something the parser "tries harder" to defeat.
