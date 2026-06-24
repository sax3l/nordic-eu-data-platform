# PyMuPDF (fitz) — Fastest PDF Text Extraction

> **Repo:** https://github.com/pymupdf/PyMuPDF | **Stars:** ~5K | **Language:** Python/C++ | **License:** AGPL 3.0

The fastest PDF text and metadata extraction library. 5-10x faster than pdfplumber for pure text. Use when you need text fast and don't need table structure preservation.

## Install

```bash
pip install pymupdf
```

## Fast Text Extraction

```python
import fitz  # pymupdf

doc = fitz.open("annual_report.pdf")
full_text = ""
for page in doc:
    full_text += page.get_text()  # ~1000 pages/sec

# Metadata
print(doc.metadata)  # {title, author, subject, keywords, ...}
print(f"Pages: {doc.page_count}")

doc.close()
```

## Extract Company Data from PDF metadata

```python
def extract_pdf_info(filepath: str) -> dict:
    doc = fitz.open(filepath)
    meta = doc.metadata
    text = ""
    for page in doc:
        text += page.get_text() or ""
    doc.close()
    return {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "page_count": doc.page_count,
        "text_sample": text[:2000],
        "full_text_length": len(text),
    }
```

## Speed

- Text extraction: ~1000 pages/sec (no OCR)
- Memory: ~50MB for 500-page PDF
- Best for: bulk PDF text extraction

## In the Pipeline

Use for fast text passes on registry PDFs. pdfplumber when tables matter.

## Related

- [pdfplumber](pdfplumber.md) — better table extraction
- [Unstructured](unstructured.md) — handles multi-format + OCR
