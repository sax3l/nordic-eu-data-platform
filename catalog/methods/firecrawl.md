# Firecrawl — AI-Powered Web Crawler

> **Repo:** https://github.com/firecrawl/firecrawl | **Stars:** ~130K | **Language:** TypeScript/Python | **License:** MIT (self-hosted) / AGPL (cloud)

Turns entire websites into clean Markdown or structured JSON. LLM-ready output with one API call. Excellent for bulk company website extraction when you want the full site content in one shot without writing per-site selectors.

## What it solves

Writing per-site selectors for 40M+ company websites is impossible. Firecrawl takes a URL and returns the entire site's content in clean Markdown — navigation, about pages, contact pages, team pages, all extracted. The LLM then processes the Markdown instead of raw HTML. This collapses the "parse each site differently" problem into "give the LLM clean text."

## Install

```bash
# Self-hosted (free, local)
git clone https://github.com/firecrawl/firecrawl
cd firecrawl
docker compose up -d
# API at http://localhost:3002
```

## Python SDK

```bash
pip install firecrawl-py
```

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_url="http://localhost:3002")

# Crawl entire company site, get all pages as Markdown
result = app.crawl_url(
    "https://example-company.se",
    params={
        "limit": 50,            # Max pages to crawl
        "scrapeOptions": {
            "formats": ["markdown"],  # Clean Markdown (ready for LLM)
        },
        "includePaths": ["/om-oss*", "/kontakt*", "/medarbetare*", "/team*"],
        "excludePaths": ["/blog/*", "/nyheter/*", "/produkter/*"],
    },
    poll_interval=30,
)

# result["data"] = list of {url, markdown, metadata}
for page in result["data"]:
    print(f"--- {page['metadata']['title']} ---")
    print(page["markdown"][:500])
```

## Quick Single-Page Extraction

```python
# Extract a single page
result = app.scrape_url("https://example-company.se/kontakt", params={
    "formats": ["markdown", "html"],
    "onlyMainContent": True,  # Skip nav/footer
})
print(result["markdown"])
```

## Structured Extraction (with LLM Prompt)

```python
# Extract structured data from any site with a prompt
result = app.scrape_url("https://example-company.se/om-oss", params={
    "formats": ["extract"],
    "extract": {
        "prompt": "Extract: company name, org number, founding year, CEO name, number of employees, office location, contact email, and all board members with their titles.",
        "schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string"},
                "org_number": {"type": "string"},
                "founding_year": {"type": "integer"},
                "ceo_name": {"type": "string"},
                "employees": {"type": "integer"},
                "office_location": {"type": "string"},
                "contact_email": {"type": "string"},
                "board_members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                        }
                    }
                }
            }
        }
    }
})
print(json.dumps(result["extract"], indent=2))
```

## Key vs Crawlee

| | Firecrawl | Crawlee |
|---|---|---|
| **Best for** | Full-site Markdown extraction + LLM | Programmatic scraping pipelines |
| **Coding required** | Zero (prompt-based) | Full code control |
| **Speed** | 50-100 pages/min | 100-500 pages/min (tuned) |
| **Flexibility** | Low (fixed output formats) | High (any logic you want) |
| **Use case** | "Give me the whole site as clean text" | "I need specific data from specific pages" |

Firecrawl is the fast path for when you just want all content. Crawlee is the precision path for structured crawling with custom logic.

## In the Pipeline

```
URL → Firecrawl (full site → Markdown) → Unstructured (partition) → NER/LLM
                        ↓
                  Every page from site,
                  already clean and ready
```

## Speed

- Self-hosted: ~50-100 pages/min (depends on site size)
- Cloud: ~200+ pages/min
- Memory: ~500MB (Docker container)

## Related

- [Crawlee](crawlee.md) — the programmatic alternative
- [Unstructured](unstructured.md) — partitions the Markdown output
- [Trafilatura](trafilatura.md) — lighter alternative for single pages
