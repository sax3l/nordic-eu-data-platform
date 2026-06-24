# pdfplumber — PDF Text + Table Extraction

> **Repo:** https://github.com/jsvine/pdfplumber | **Stars:** ~7K | **Language:** Python | **License:** MIT

Extracts text, tables, and metadata from PDFs with precise positioning. Better than PyMuPDF for complex table extraction. The platform's primary tool for financial statement PDFs from European registries.

## What it solves

Company registries output PDFs — annual reports, tax filings, registration certificates. These PDFs contain tables (balance sheets, income statements, board lists) that general-purpose PDF tools lose. pdfplumber preserves table structure with cell-level precision.

## Install

```bash
pip install pdfplumber
```

## Extract Tables from Annual Report PDF

```python
import pdfplumber

with pdfplumber.open("annual_report.pdf") as pdf:
    for page in pdf.pages:
        # Extract all tables on this page
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            print(f"--- Table {i+1} on page {page.page_number} ---")
            for row in table:
                print(" | ".join([str(cell or "") for cell in row]))

        # Extract text with position info
        text = page.extract_text()
        print(f"Page {page.page_number}: {len(text)} chars")
```

## Extract Financial Data (Balance Sheet)

```python
def extract_balance_sheet(pdf_path: str) -> dict:
    """Extract balance sheet from Swedish annual report PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Detect if this is a balance sheet by looking for key words
                text_lower = " ".join([str(cell or "") for cell in sum(table, [])]).lower()
                if any(kw in text_lower for kw in ["balansräkning", "tillgångar", "eget kapital", "balance sheet", "assets"]):
                    # Parse rows into structured data
                    data = {}
                    for row in table:
                        if len(row) >= 3 and row[0]:
                            label = row[0].strip()
                            current_year = row[1].strip() if row[1] else None
                            prev_year = row[2].strip() if len(row) > 2 and row[2] else None
                            data[label] = {"current_year": current_year, "prev_year": prev_year}
                    return data
    return {}

# Extract board members from registration PDF
def extract_board_members(pdf_path: str) -> list[dict]:
    """Extract board members from Bolagsverket registration PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""

    # Feed to spaCy/LLM for structured extraction
    # (pdfplumber gets the text; NER extracts the names)
    return full_text
```

## Bounding Box Extraction for Forms

```python
# Swedish registration certificates have standard layouts
# Use bounding boxes to target specific fields
with pdfplumber.open("registration_certificate.pdf") as pdf:
    page = pdf.pages[0]

    # Extract text in a specific rectangle (x0, top, x1, bottom)
    # Org number is typically in the top-right corner
    org_number_area = page.within_bbox((300, 50, 500, 100))
    org_number_text = org_number_area.extract_text()

    # Company name is typically centered at the top
    company_name_area = page.within_bbox((50, 100, 550, 150))
    company_name_text = company_name_area.extract_text()
```

## In the Pipeline

```
PDF (registry) → pdfplumber → tables + text → spaCy NER → LLM enrichment → database
                          ↓
                    Table structure preserved
                    (critical for financial data)
```

## pdfplumber vs PyMuPDF vs Unstructured

| | pdfplumber | PyMuPDF (fitz) | Unstructured |
|---|---|---|---|
| **Table extraction** | **Best** (cell-level) | Good | Good |
| **Speed** | Medium | **Fastest** | Medium |
| **Text extraction** | Good | **Best** | Good |
| **OCR** | No | No | **Yes** (with Tesseract) |
| **Element types** | Tables + text | Text + images | Tables + text + images + headers |
| **Use case** | Financial PDFs with tables | General PDF text | Multi-format documents |

**Platform strategy:** Use pdfplumber for financial statement PDFs (tables matter). Use PyMuPDF for general PDF text extraction (fast). Use Unstructured when you need OCR or the doc is not a PDF.

## Related

- [Unstructured](unstructured.md) — handles DOCX/HTML/PDF + OCR
- [OCR Pipeline](ocr-pipeline.md) — when pdfplumber can't extract text (scanned PDFs)
- [spaCy](spacy.md) — structures the extracted text
