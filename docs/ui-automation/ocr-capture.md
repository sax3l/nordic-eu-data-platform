# OCR-Capture Pipeline
## Turning rendered pixels into structured, provenance-tracked records

**Last Updated:** 2026-06-24
**Scope:** PRIMARY OFFICIAL sources whose data ships only as rendered pixels — scanned registry extracts, image-only filing PDFs, image-embedded tables, scanned org charts.
**Architecture:** capture → preprocess → OCR cascade → layout/table reconstruction → NER → structured records (+ per-field confidence + provenance).

---

## 0. Compliance gate (read first)

This pipeline exists for **Tier 1 primary official sources that have no machine API** and only expose data as pixels — e.g. **DE Handelsregister** filings, **IT Registro Imprese / `registroimprese.it`** visure, scanned **Bolagsverket** historical extracts, **GLEIF**/registry PDFs, image-embedded officer tables, scanned org charts in annual reports.

It is **NOT** for competitor ICP tools (Apollo / ZoomInfo / Cognism / Lusha / Seamless). Per [`../COMPLIANCE.md`](../COMPLIANCE.md), those are **Tier 5 = benchmark/feature-intel only**. OCR-exfiltration of a competitor's proprietary DB behind their login is forbidden: it breaches their ToS, is an access-control circumvention, and launders *their* errors and consent problems into our "honest" product — destroying the moat.

| Allowed (T1, this doc) | Forbidden |
|---|---|
| OCR a scanned official registry extract that has no API | Bulk OCR/screen-scrape of a competitor's gated result grid |
| Read an image-only official filing PDF you are entitled to access | Circumventing a login / paywall / rate-limit to harvest a DB |
| Reconstruct a table from an official visura | Re-selling or re-keying a licensed third-party dataset |

**Every emitted field carries `source`, `lawful_basis`, `captured_at`, plus OCR `confidence`** (GDPR-by-design, §7). Respect robots.txt / rate limits / `429`+`Retry-After`; the adaptive limiter (see `../architecture/adaptive-engine.md`) backs off — it never brutes through.

---

## 1. When to reach for OCR at all

OCR is the **last** extraction tier, not the first. Cost and error rate are both an order of magnitude above text extraction. Decision order:

```
Does the source expose a machine-readable form?
├─ Official API / open-data dump (T1) .......... USE IT. Stop. (catalog/registries)
├─ Structured download (XBRL/iXBRL, CSV, JSON) . USE IT. Stop.
├─ HTML with real text in the DOM ............... text-extract (WEB_EXTRACTION_NER_PIPELINE.md). Stop.
├─ PDF with a real text layer ................... pdfplumber / PyMuPDF text layer. Stop.
└─ Pixels only (scanned img, image-PDF, canvas)  ── THIS PIPELINE ──┐
                                                                     ▼
                                                          capture → OCR → NER
```

> **Always probe for a text layer before OCR.** `PyMuPDF page.get_text("words")` returning non-empty = native text; OCR would only *add* error. Run OCR strictly on the pages/regions where the text layer is empty or the element is a raster image.

---

## 2. Pipeline diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SOURCE (T1 official): scanned PDF · image-only filing · image-embedded table  │
│                        · canvas-rendered registry page · scanned org chart     │
└───────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                    ┌────────────────▼─────────────────┐
                    │  STAGE 0 — TEXT-LAYER PROBE        │
                    │  PyMuPDF/pdfplumber get_text       │
                    │  non-empty? → skip OCR (native)    │
                    └────────────────┬─────────────────┘
                          (pixels only)│
                    ┌────────────────▼─────────────────┐
                    │  STAGE 1 — CAPTURE                 │
                    │  • PDF → raster (PyMuPDF @300 DPI) │
                    │  • screen/region (mss + bbox)     │
                    │  • headless page → full-page PNG  │
                    │    (Playwright, no logged-in sess)│
                    └────────────────┬─────────────────┘
                                     │  raw image(s)
                    ┌────────────────▼─────────────────┐
                    │  STAGE 2 — PREPROCESS (OpenCV)     │
                    │  grayscale → deskew (Hough/minAreaRect)
                    │  → denoise → adaptive threshold    │
                    │  → upscale small text → dewarp     │
                    │  → border crop · DPI normalize     │
                    └────────────────┬─────────────────┘
                                     │  clean binarized image
                    ┌────────────────▼─────────────────┐
                    │  STAGE 3 — LAYOUT ANALYSIS         │
                    │  Docling / Marker / PP-Structure   │
                    │  → reading order · blocks · TABLES │
                    │  → figure/heading/paragraph regions│
                    └──────┬───────────────────┬────────┘
                  (text regions)        (table regions)
                           │                   │
            ┌──────────────▼──────┐   ┌─────────▼──────────────┐
            │ STAGE 4 — OCR CASCADE│   │ STAGE 4b — TABLE OCR    │
            │ ┌──────────────────┐ │   │ cell grid → per-cell OCR│
            │ │1 PaddleOCR (PP-   │ │   │ → reconstruct DataFrame │
            │ │  OCRv4/v5) PRIMARY│ │   │ (PP-Structure/Marker)   │
            │ │  GPU-batched      │ │   └─────────┬──────────────┘
            │ ├──────────────────┤ │             │
            │ │2 docTR / RapidOCR │ │             │
            │ │  (2nd opinion if  │ │             │
            │ │  conf<τ / disagree)│ │            │
            │ ├──────────────────┤ │             │
            │ │3 Tesseract (LSTM, │ │             │
            │ │  lang packs;      │ │             │
            │ │  cheap broad net) │ │             │
            │ ├──────────────────┤ │             │
            │ │4 Vision-LLM       │ │             │
            │ │  (hard/contextual │ │             │
            │ │  ONLY; §5.4)      │ │             │
            │ └──────────────────┘ │             │
            └──────────┬───────────┘             │
                       │  text + per-token conf  │
                       └───────────┬─────────────┘
                    ┌──────────────▼─────────────────┐
                    │  STAGE 5 — POST-OCR NORMALIZE     │
                    │  unicode NFC · ligature fix ·     │
                    │  diacritics (åäöøæ/üß/àèìòù) ·     │
                    │  O↔0 l↔1 confusion repair ·       │
                    │  orgnr/VAT checksum validation    │
                    └──────────────┬─────────────────┘
                                   │  clean text + spans
                    ┌──────────────▼─────────────────┐
                    │  STAGE 6 — NER / FIELD EXTRACT    │
                    │  spaCy (xx/de/it/sv) + GLiNER     │
                    │  zero-shot (ORG, PERSON, ROLE,    │
                    │  ORGNR, ADDRESS, DATE, AMOUNT)    │
                    └──────────────┬─────────────────┘
                                   │  typed entities
                    ┌──────────────▼─────────────────┐
                    │  STAGE 7 — CONFIDENCE + PROVENANCE │
                    │  fuse OCR conf × NER conf ×        │
                    │  checksum × cross-engine agreement │
                    │  → field conf; attach source/      │
                    │  lawful_basis/captured_at/bbox     │
                    └──────────────┬─────────────────┘
                       ┌───────────┴────────────┐
                  conf ≥ τ_auto            conf < τ_review
                       │                        │
              ┌────────▼────────┐      ┌─────────▼──────────┐
              │ STRUCTURED RECORD│      │ HUMAN-REVIEW QUEUE │
              │ → fusion layer   │      │ (crop + overlay +  │
              │ (fusion-         │      │  candidate values) │
              │  confidence.md)  │      └────────────────────┘
              └─────────────────┘
```

---

## 3. Stage-by-stage detail

### Stage 1 — Capture

| Mode | Tool | Use | Notes |
|---|---|---|---|
| **PDF → raster** | PyMuPDF (`fitz`) | image-only filing PDFs | render at **300 DPI** (200 floor, 400 for tiny text); per-page so OCR runs only on raster pages |
| **Region capture** | `mss` + bbox | a fixed panel of a desktop registry viewer with no export | grab the smallest bbox that holds the data — less to deskew, faster OCR |
| **Full-page render** | Playwright (`page.screenshot(full_page=True)`) | canvas/image-rendered official pages with no DOM text | headless, **never a logged-in competitor session**; T1 public/entitled pages only |
| **Multi-monitor / native viewer** | `mss` per-monitor | thick-client registry apps | crop to content; record monitor+bbox in provenance |

Capture writes `{image_bytes, dpi, source_url|file, page, bbox, captured_at}` — the bbox/page travels with every downstream field for traceability.

### Stage 2 — Preprocess (OpenCV)

Order matters; each step assumes the previous ran.

```python
import cv2, numpy as np

def preprocess(img_bgr, target_dpi=300):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 1) Deskew — estimate dominant text angle, rotate to level
    coords = np.column_stack(np.where(gray < 128))
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) > 0.2:
        h, w = gray.shape
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        gray = cv2.warpAffine(gray, M, (w, h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)

    # 2) Denoise (scans / fax artefacts)
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # 3) Upscale small text BEFORE threshold (helps faint registry print)
    if gray.shape[0] < 1000:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # 4) Adaptive threshold — robust to uneven scan lighting
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=31, C=15)

    # 5) Light morphological open to kill speckle
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return binary
```

Add **dewarp** (page-curl / camera capture) via `page_dewarp` or a thin-plate-spline grid only when the source is photographed rather than flatbed-scanned — it is expensive, so gate it on a curvature estimate.

### Stage 3 — Layout analysis

Run a layout model *before* OCR so text and tables go down different paths and reading order is preserved (registry extracts are multi-column).

- **Docling** (IBM) — strong PDF/scan layout + reading order + table structure; emits a clean document tree. First choice for filings.
- **Marker** — PDF/scan → Markdown with good table fidelity; great when you want a linear, diff-able artefact.
- **PP-Structure** (PaddleOCR) — layout + table cell-structure model; pairs natively with the PaddleOCR text recognizer used in Stage 4.

Output: ordered regions tagged `heading | paragraph | table | figure | kv-pair`, each with a bbox. Text regions → Stage 4; table regions → Stage 4b.

### Stage 4 — OCR cascade

Each tier only runs when the previous tier is uncertain — keeps the GPU on the hard cases.

| # | Engine | Role | Strengths | When it fires |
|---|---|---|---|---|
| **1** | **PaddleOCR (PP-OCRv4/v5)** | **Primary** | best speed/accuracy on dense multilingual print; GPU-batchable; angle classifier | every region |
| **2** | **docTR** or **RapidOCR** | 2nd opinion | docTR strong on clean docs; RapidOCR = ONNX, light, no Paddle dep | token conf `< τ_low` **or** to break ties |
| **3** | **Tesseract 5 (LSTM)** | broad net | mature lang packs (`deu`, `ita`, `swe`, `nor`, `fin`), `--psm` control, cheap | engines 1–2 disagree or region is odd script/spacing |
| **4** | **Vision-LLM** | hard/contextual only | reads degraded scans, handwriting hints, uses *context* (e.g. which token is the org number vs a date) | §5.4 — only on still-low-confidence / context-dependent cells, never bulk |

Disagreement handling: if engine 1 and engine 2 produce different strings for a span, escalate to engine 3 and take a **2-of-3 vote** weighted by per-engine confidence. Persist all candidates so review can see them.

```python
# Cascade core (illustrative)
def ocr_region(image, tau_low=0.80, tau_review=0.92):
    p = paddle_ocr(image)                       # tier 1
    if p.conf >= tau_review:
        return p.with_source("paddleocr")
    d = doctr_ocr(image)                        # tier 2
    if p.text == d.text and max(p.conf, d.conf) >= tau_low:
        return best(p, d).with_source("paddle+doctr")
    t = tesseract_ocr(image)                    # tier 3
    voted = majority_vote([p, d, t])            # conf-weighted 2-of-3
    if voted and voted.conf >= tau_low:
        return voted.with_source("cascade-vote")
    return None  # → tier 4 vision-LLM (§5.4) or review queue
```

### Stage 4b — Table OCR / reconstruction

1. Detect the cell grid (PP-Structure table model or ruling-line detection via OpenCV `HoughLinesP` for bordered tables; whitespace clustering for borderless).
2. OCR **each cell crop independently** (small images → high accuracy, trivially GPU-batched).
3. Reassemble into a DataFrame keyed by `(row, col)`; carry per-cell confidence.
4. Header inference: first row / bold band → column names; reconcile against an expected schema (e.g. officer table = `name | role | dob | appointed`).

Marker/Docling can emit the table directly as Markdown/HTML — use that as a cross-check against the cell-grid reconstruction; disagreement on a cell drops its confidence.

### Stage 5 — Post-OCR normalization

Cheap, high-yield repairs before NER:

- Unicode **NFC**; fix split ligatures (`ﬁ`→`fi`).
- **Diacritic recovery** for Nordic/DACH/IT: `aÌ`→`å`, mojibake `Ã¥`→`å`, etc.
- **Confusable repair gated by field type**: in a numeric field (orgnr, VAT, postal) map `O→0, l/I→1, S→5, B→8`; in alpha fields do the inverse. Never globally.
- **Checksum validation as a correction signal**: SE orgnr Luhn, DE/IT VAT check digits, IBAN mod-97. A passing checksum sharply raises field confidence; a near-miss with one confusable swap is auto-corrected and flagged.

### Stage 6 — NER / field extraction

Feed normalized, reading-ordered text into NER to turn strings into typed fields. This reuses the platform NER stack (`pipelines/WEB_EXTRACTION_NER_PIPELINE.md`) but tuned for OCR noise and multilingual official docs:

- **spaCy** multilingual / per-language (`xx_ent_wiki_sm`, `de_core_news_lg`, `it_core_news_lg`, Swedish KB-BERT pipeline) for PERSON/ORG/GPE/DATE baseline.
- **GLiNER** zero-shot for the *registry-specific* labels spaCy lacks: `ORG_NUMBER`, `VAT_ID`, `ROLE` (Geschäftsführer / amministratore / styrelseledamot), `SHARE_CAPITAL`, `REGISTERED_ADDRESS`, `APPOINTMENT_DATE`. Zero-shot means no retraining per country.
- Anchor entities to their **source bbox/cell** so every field is traceable back to a pixel region.

```python
from gliner import GLiNER
labels = ["company name","org number","VAT id","person","role",
          "registered address","appointment date","share capital"]
model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
ents = model.predict_entities(ocr_text, labels, threshold=0.45)
# each ent → {text, label, score}; pair score with OCR conf in Stage 7
```

### Stage 7 — Confidence + provenance

Fuse independent signals into one per-field score:

```
field_conf = w_ocr·ocr_conf
           + w_ner·ner_conf
           + w_agree·engine_agreement      # 1.0 if 3/3 engines agree, scaled down otherwise
           + w_check·checksum_pass         # +bonus when orgnr/VAT/IBAN validates
   clipped to [0,1];  weights ≈ 0.35/0.25/0.20/0.20, tuned on a labelled gold set
```

Routing: `field_conf ≥ τ_auto (≈0.90)` → emit; `τ_review (≈0.70) ≤ conf < τ_auto` → human-review queue with the **crop + overlay + all engine candidates**; `< τ_review` → drop (never silently emit a guess into a sellable dataset).

Every emitted field record:

```json
{
  "field": "org_number",
  "value": "5560360793",
  "confidence": 0.97,
  "source": "de_handelsregister:HRB12345:doc7.pdf#p2",
  "lawful_basis": "public_register_art6_1f",
  "captured_at": "2026-06-24T09:12:33Z",
  "ocr_engine": "paddleocr",
  "bbox": [612, 1840, 980, 1888],
  "checksum_valid": true
}
```

This is what makes the data **sellable in the EU**: per field, *where it came from and that it's lawful* (per `../COMPLIANCE.md`).

---

## 4. Batching for speed (GPU)

OCR throughput lives and dies on batching. Targets and levers:

| Lever | What | Effect |
|---|---|---|
| **GPU batch inference** | feed PaddleOCR/docTR a batch of region crops, not one image at a time | 5–15× over per-image calls |
| **Cell-level batching (tables)** | all cells of a page in one batch | tables stop being the bottleneck |
| **Pad-to-bucket** | group crops by aspect ratio, pad within bucket | avoids wasteful max-width padding |
| **Mixed precision (FP16)** | half-precision recognizer | ~2× on modern GPUs, negligible accuracy loss |
| **Page-parallel preprocess** | OpenCV preprocess on a CPU pool while GPU does OCR | hides preprocess latency |
| **Async DNS-style fan-out** | distributed work fabric (Celery/Redis or Temporal, see `architecture/speed-parallelism.md`) — workers pull page jobs, GPU box runs the OCR queue | scales to 50M-record math |
| **Skip-on-text-layer** | Stage 0 short-circuit | the cheapest speedup — never OCR a page that already has text |

```python
# GPU-batched recognition over preprocessed region crops
import numpy as np
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="german", use_gpu=True,
                rec_batch_num=32)          # batch knob

def ocr_pages(page_images, batch=32):
    crops = [c for img in page_images for c in layout_regions(preprocess(img))]
    out = []
    for i in range(0, len(crops), batch):
        out.extend(ocr.ocr(np.stack(pad_to_bucket(crops[i:i+batch]))))
    return out
```

Rule of thumb on one mid-range GPU: **300-DPI A4 scan ≈ 0.3–0.8 s/page** end-to-end with batching and the text-layer short-circuit, vs ~3–5 s/page naive per-image. Vision-LLM tier (§5.4) is the cost ceiling — keep it under ~5% of cells.

---

## 5. Engine selection cheatsheet

| Situation | Use |
|---|---|
| Dense multilingual official print, need speed | **PaddleOCR** (PP-OCRv4/v5), GPU-batched |
| Clean flatbed scans, want a light ONNX dep | **RapidOCR** / **docTR** |
| Odd script, custom lang pack, fine `--psm` control | **Tesseract 5** |
| Tables / structured layout | **PP-Structure** + Stage 4b, cross-checked with **Docling/Marker** |
| Whole-document → linear Markdown artefact | **Marker** |
| Degraded / context-dependent cell (which token is the orgnr?) | **Vision-LLM**, gated, ≤5% of cells |

### 5.4 Vision-LLM fallback — strictly bounded

Fires **only** when (a) the cascade is still below `τ_review` after 3 engines, or (b) the value is context-dependent (disambiguating which of several numbers is the org number, reading a degraded signature block). Send **just the failing crop**, never whole documents in bulk — that is both a cost and a compliance discipline. The LLM returns a value **plus a self-reported confidence and a rationale**; treat its confidence as one more signal in Stage 7, never as ground truth. Keep a hard per-batch budget cap; over-cap cells go to the human queue instead of the LLM.

---

## 6. Failure modes & guards

| Failure | Symptom | Guard |
|---|---|---|
| OCR'ing a native-text PDF | wasted GPU, *added* errors | Stage 0 text-layer probe is mandatory |
| Skewed scan | garbled lines | deskew before threshold; re-check angle post-rotate |
| Faint/low-DPI print | missing chars | upscale + adaptive threshold; bump capture DPI |
| Column bleed in multi-col extract | scrambled reading order | layout model (Stage 3) before OCR, not after |
| Confusable digits in IDs | invalid orgnr/VAT | field-typed confusable repair + checksum (Stage 5) |
| Silent low-confidence guesses | poisoned dataset | hard `τ_review` floor; drop or queue, never emit |
| Over-reliance on vision-LLM | cost blowout, opaque provenance | ≤5% cell cap + per-batch budget |
| Scope creep to competitor tools | compliance breach | §0 gate — T1 official sources only |

---

## 7. GDPR-by-design hooks

Where OCR'd fields are personal data (officer names, signatures, addresses):

- Tag every field with `source`, `lawful_basis`, `captured_at` (Stage 7) — already in the record schema.
- Route into the same **per-country suppression / DNC** and **right-to-erasure** plumbing as the rest of the platform (`../COMPLIANCE.md` §4); a person → delete across all sources, OCR-derived included.
- **DE/FR stricter than SE/UK** on B2B personal data — encode the per-jurisdiction rule in the fusion layer, not here.
- Retain the source crop only as long as needed for review/audit, then purge per retention policy.

---

## 8. Reference stack

```json
{
  "capture":      ["pymupdf", "mss", "playwright"],
  "preprocess":   ["opencv-python", "page_dewarp"],
  "layout":       ["docling", "marker-pdf", "paddleocr[ppstructure]"],
  "ocr_cascade":  ["paddleocr", "doctr", "rapidocr-onnxruntime", "pytesseract", "vision-llm (gated)"],
  "normalize":    ["unicodedata", "checksum validators (orgnr/VAT/IBAN)"],
  "ner":          ["spacy (xx/de/it/sv)", "gliner"],
  "orchestration":["celery+redis | temporal", "gpu batch queue"],
  "review":       ["crop+overlay+candidates UI", "human-in-the-loop queue"]
}
```

### Links
- Compliance gate: [`../COMPLIANCE.md`](../COMPLIANCE.md)
- Downstream NER detail: [`../pipelines/WEB_EXTRACTION_NER_PIPELINE.md`](../pipelines/WEB_EXTRACTION_NER_PIPELINE.md)
- Throughput/work-fabric: `../architecture/speed-parallelism.md`
- Entity fusion + confidence: `../architecture/fusion-confidence.md`
- PaddleOCR · Docling · Marker · docTR · GLiNER · Tesseract · OpenCV (see each project's docs)
