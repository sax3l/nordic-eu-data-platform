# Unstructured.io — Universal Document Parser

> **Repo:** https://github.com/Unstructured-IO/unstructured | **Stars:** ~13K | **Language:** Python | **License:** Apache 2.0

Best-in-class OSS for parsing PDF, HTML, DOCX, XLSX, PPTX, images, emails, markdown, and CSV into clean structured data (JSON elements, Markdown, or Pandas DataFrames). The platform's primary document-to-structured-data bridge for company registries, financial filings, and corporate websites.

## What it solves

Company data lives in 50+ formats across 20 countries. PDF annual reports (Sweden), HTML registry pages (Denmark CVR), DOCX filings (Germany), scanned images (Italy). Unstructured normalizes all of them into the same element tree — paragraphs, tables, headers, lists, images — with bounding boxes and metadata. That's the input to our NER + LLM pipeline.

## Install

```bash
# Full pipeline (PDF + DOCX + images + HTML)
pip install "unstructured[all-docs]"

# Lightweight (HTML/plaintext only, for web scraping path)
pip install "unstructured[local-inference]"

# Docker (prebuilt with all deps)
docker pull quay.io/unstructured-io/unstructured-api:latest
docker run -p 8000:8000 quay.io/unstructured-io/unstructured-api:latest
```

## Core Patterns

### Parse a PDF Annual Report (Bolagsverket)

```python
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_json

elements = partition_pdf(
    "annual_report.pdf",
    strategy="ocr_only",            # or "auto" / "hi_res" / "fast"
    languages=["swe", "eng"],       # multi-language OCR
    infer_table_structure=True,     # extract tables
    extract_images_in_pdf=True,     # extract embedded images/charts
)
# elements = [Title, NarrativeText, Table, Image, ...]
print(elements_to_json(elements))
```

### Parse HTML from CVR.dk company page

```python
from unstructured.partition.html import partition_html
import requests

html = requests.get("https://datacvr.virk.dk/data/...").text
elements = partition_html(text=html)
# → paragraphs, tables, lists categorized automatically
```

### Parse DOCX filing (German Handelsregister)

```python
from unstructured.partition.docx import partition_docx

elements = partition_docx("filing.docx", infer_table_structure=True)
```

### Batch Process via API (Docker)

```python
import requests
files = {"files": open("annual_report.pdf", "rb")}
resp = requests.post(
    "http://localhost:8000/general/v0/general",
    files=files,
    data={
        "strategy": "hi_res",
        "languages": "swe",
        "output_format": "application/json",
        "include_page_breaks": "true",
    }
)
print(resp.json())
```

## Element Types (the canonical output)

| Type | What | Example use |
|---|---|---|
| `Title` | Document/section titles | Company name |
| `NarrativeText` | Paragraphs | Description, notes |
| `Table` | Tables (with cell structure) | Financials, officer lists |
| `ListItem` | Bullet/list items | Board member lists |
| `Address` | Postal/email addresses | Registered address |
| `FigureCaption` | Image/figure captions | Chart descriptions |
| `Header` / `Footer` | Page metadata | Page numbers |

## In the Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Raw Download │ ──► │ Unstructured │ ──► │ NER (spaCy)  │
│ (PDF/HTML/DOCX)│     │  Partition   │     │ + LLM enrich │
└──────────────┘     └──────────────┘     └──────────────┘
                                               │
                                               ▼
                                       ┌──────────────┐
                                       │ Entity Link  │
                                       │ + Dedup      │
                                       └──────────────┘
```

## Speed

- `fast` strategy (HTML/text): ~100 docs/sec
- `hi_res` strategy (PDF with table detection): ~2-5 pages/sec
- `ocr_only`: ~0.5-1 page/sec (GPU-accelerated with CUDA)
- API mode (Docker): 1-3 docs/sec (depends on document complexity)

## Languages Supported for OCR

sv, no, da, fi, de, fr, it, es, nl, pl, cs, hu, pt, en — all 20 target languages.

## Related

- [OCR Pipeline](ocr-pipeline.md)
- [NER Pipeline Cookbook](spacy.md)
- [LM Studio + Local LLM](lmstudio-ollama.md) — for the enrichment pass after Unstructured
