# Trafilatura — Best-in-Class Web Content Extraction

> **Repo:** https://github.com/adbar/trafilatura | **Stars:** ~5K | **Language:** Python | **License:** GPL 3.0

The gold standard for stripping boilerplate from web pages — navigation, ads, footers, sidebars — leaving only the main content. Used in web corpus creation, NLP datasets, and now our platform for clean text extraction before NER/LLM passes.

## What it solves

Raw HTML from Playwright/Crawlee is 90% navigation/ads/footer. Trafilatura reduces it to 10% (the actual article/company description). Paired with Unstructured for document-format content, Trafilatura handles the web-page path at extremely high speed.

## Install

```bash
pip install trafilatura
```

## Extract Clean Text

```python
import trafilatura

html = requests.get("https://example-company.se/om-oss").text
text = trafilatura.extract(html, include_comments=False, include_tables=True)
# → Clean, boilerplate-free text ready for NER/LLM
```

## Extract with Metadata

```python
result = trafilatura.extract(
    html,
    output_format="json",
    include_comments=False,
    include_tables=True,
    include_images=False,
    with_metadata=True,  # title, author, date, url, etc.
)
data = json.loads(result)
# data["text"] → clean text
# data["title"] → page title
# data["date"] → publication date if detectable
# data["author"] → author if detectable
```

## Speed

- ~100-500 pages/sec (pure text extraction, no rendering)
- Memory: ~50MB per 1000 pages
- No GPU required

## In the Pipeline

```
Raw HTML → Trafilatura → clean text → spaCy NER → Ollama enrichment
                                │
                          (90% noise stripped,
                           ready for high-quality extraction)
```

## When to Use Trafilatura vs Unstructured

| Format | Use | Reason |
|---|---|---|
| HTML blog/news pages | Trafilatura | Faster, lower memory, designed for web |
| HTML with tables/data | Unstructured | Table structure preserved |
| PDF | Unstructured | Trafilatura doesn't handle PDF |
| DOCX/XLSX | Unstructured | Only Unstructured handles Office formats |
| Any non-HTML | Unstructured | Trafilatura is HTML-only |

## Related

- [Unstructured](unstructured.md) — for PDF/DOCX/structured documents
- [spaCy NER](spacy.md) — consumes the clean text
- [Extraction Pipeline Example](../../examples/extraction_pipeline.py)
