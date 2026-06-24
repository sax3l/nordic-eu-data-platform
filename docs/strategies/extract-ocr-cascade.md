# Strategy: OCR Cascade (image-to-text, accuracy-and-cost laddered)

**Layer:** EXTRACTION · **Component:** `extract-ocr-cascade`
**Last updated:** 2026-06-24
**Builds on:** `docs/architecture/pillars/oss-combo-matrix.md` (Chain C, rows 11-13), `docs/architecture/MASTER_BLUEPRINT_FULL.md` §4.7; `catalog/OPEN_SOURCE_TOOLS_CATALOG.md` §4 (PaddleOCR, RapidOCR, docTR, Tesseract, opencv, noteshrink).

---

## 1. Mechanism

OCR is the **last** text-extraction resort — reached only for documents with no machine-readable text layer (scanned annual reports, image-only filings, photographed imprints). The cascade has a preprocessing front-end and an engine ladder ordered by *throughput-then-accuracy*, with a vision-LLM as the paid backstop:

**Preprocess (opencv / noteshrink):** deskew, denoise, adaptive binarize, contrast-stretch, and upscale low-DPI scans before any engine sees them. Bad input is the dominant OCR error source; ~30-80 ms of preprocessing recovers more accuracy than swapping engines. Layout detection (PP-Structure) crops tables/columns so recognition runs on clean regions.

**Engine ladder:**
1. **RapidOCR** (ONNX, quantized, 1000+ img/s) — the volume tier; runs first on every page for a cheap transcript and a per-region confidence.
2. **PaddleOCR** (96.3% on ICDAR, 100+ languages incl. table/layout) — escalated when RapidOCR's mean confidence is below threshold or the page is a financial table where accuracy matters.
3. **docTR** (`mindee/doctr`, end-to-end with layout) — alternate recognizer for documents where Paddle's segmentation fails; useful cross-check / ensemble vote on disputed lines.
4. **Tesseract 5** (LSTM, CPU) — the dependency-light fallback for languages or fonts the deep models handle poorly, and for air-gapped/CPU-only nodes.
5. **Claude Vision** (`vision-LLM`) — paid, gated, last: only the residual pages where the OSS stack disagrees or returns sub-threshold confidence, and only when the field's *value* justifies a credit (financial figures on a target company we must resolve).

Per-line confidence drives escalation; a page is "done" when extracted text passes a plausibility gate (e.g. numeric columns sum, orgnr checksum validates, the page is mostly dictionary words).

## 2. Tools / repos

`RapidAI/RapidOCR`, `PaddlePaddle/PaddleOCR` (+ PP-Structure), `mindee/doctr`, `JaidedAI/EasyOCR` (optional GPU alternate), `tesseract` via `pytesseract`, `opencv-python`, `mzucker/noteshrink`. GPU pods run as Dramatiq actors (`prefetch=1`, micro-batch ≤512 images or 50 ms) per the speed spec. Vision-LLM backstop via the Claude API.

## 3. Failure mode it eliminates

It eliminates **single-engine OCR failure and the OCR-everything cost trap**. No single engine is robust across the platform's input distribution — Tesseract collapses on skew and low DPI, PaddleOCR is slow on CPU, RapidOCR trades accuracy for speed, vision-LLMs are expensive. A fixed choice either misses text or burns money. The cascade catches each engine's residual with the next, and the preprocessing front-end fixes the input-quality failures that cause most misreads regardless of engine. It also eliminates **silent OCR corruption** (plausible-but-wrong digits) via the plausibility gate, which is critical because financial figures feed downstream business logic.

## 4. Composition

- **Receives from `extract-parser-cascade`** only when a PDF/image has no text layer (the explicit rung-5 handoff). It is never the first thing tried on a document.
- **Diverts nothing to itself that XBRL covers:** if a filing is iXBRL/XBRL, `extract-xbrl-structured-lane` handles it with zero OCR — this composition is what keeps OCR volume to the genuinely scanned tail (mostly legacy/no-bulk-market filings: IT/ES/PT visure, LU/IS per-doc, older DE).
- **Feeds `extract-ner-ensemble`** the recovered text for entity extraction (officers, addresses on scanned imprints).
- **Feeds `resolve-fusion-confidence`** OCR output as a claim whose source reliability `r_s` is *lower* than structured sources, and whose plausibility-gate result is a validation signal — so an OCR'd value that disagrees with a registry is correctly down-weighted.
- **Composes with `verify-validation-qa`:** the plausibility checks (checksum, MX on OCR'd emails, libphonenumber on OCR'd numbers) are the same validators, reused to reject OCR garbage.

## 5. Success contribution

Per-document OCR recovery is `1 − Π(1 − pᵢ)` over engines after preprocessing. With preprocessing lifting each engine's base rate and four OSS engines plus a vision backstop, recoverable-page success approaches ~0.97-0.99 on legible scans; truly degraded originals (faint thermal prints, heavy stamps) are the irreducible residual and are flagged `needs_reverify`, never fabricated. The strategy's larger contribution is *cost containment*: by reserving the paid vision-LLM for sub-threshold residual only, it keeps the financial-document tail viable on the free/budget tier (the blueprint budgets a single GPU pod precisely because XBRL + parser cascade remove most documents before OCR). Combined with the XBRL lane, OCR is the failure-catcher for the small fraction of financials that exist only as images.

## 6. Compliance envelope

OCR runs on documents the platform lawfully obtained (registry-published annual accounts, company-website imprints) — it adds no fetch and inherits the source's lawful basis. Constraints: (a) it operates only on legally-retrievable documents — it must not be pointed at paywalled or `automated_access_forbidden` registry images; per-doc paid financials (DE ~€1, IT/ES visure) are fetched under the licensed/budget tier and OCR'd only after lawful purchase; (b) extracted personal data (officer names/addresses on scanned filings) carries provenance and jurisdiction so DNC, erasure, and `reuse_restriction` apply downstream; (c) the vision-LLM backstop sends document images to an external API, so it is **disabled for any source whose terms forbid third-party processing** and for documents containing special-category data — those stay on the local OSS engines. No OCR is ever used to defeat a CAPTCHA or bot-wall (that is the fetch layer's gated, detect-first-avoid path), keeping the cascade purely a transcription tool over lawful inputs.
