# Screaming Frog — SEO Crawler + Bulk Data Extraction

> **Tool:** Screaming Frog SEO Spider | **License:** Paid ($199/year — absurdly cheap for what it does)
> **Speed:** 100+ pages/min | **OS:** Windows, macOS, Ubuntu | **Real-time:** Yes

The platform's Tier 1 bulk crawler for open websites. Crawls entire domains, extracts data via CSS selectors and custom extraction rules, exports to CSV/Excel. Handles sitemap discovery, JavaScript rendering, and structured data extraction at insane speed.

## What it solves

For open company websites (no WAF, no login), Screaming Frog is 20-50x faster than Playwright for bulk crawling. Crawl 10,000 company sites per hour, extracting contact pages, about pages, team pages. Export all extracted data to CSV for batch NER processing. The $199/year license is the single best ROI tool in the entire platform.

## Key Features for the Platform

1. **Custom Extraction** — Define CSS selectors, XPath, or regex to extract specific data from every page
2. **JavaScript Rendering** — Built-in Chromium for JS-heavy sites (slower but comprehensive)
3. **Structured Data Extraction** — Auto-extracts Schema.org, Microdata, JSON-LD
4. **Sitemap Discovery** — Auto-discovers XML sitemaps, RSS feeds
5. **URL Discovery** — Crawls all internal links, finds contact/about/team pages
6. **Export to CSV/Excel** — Direct feed into our NER/LLM pipeline
7. **Headless CLI Mode** — Automatable via command line, Docker-friendly

## Custom Extraction Configuration

Configure these extraction rules in Screaming Frog for company contact harvesting:

```
# Extraction Rules (CSS Selectors)
XPath:
  //a[contains(@href, 'mailto:')]                        → Emails
  //a[contains(@href, 'tel:')]                             → Phone numbers
  //*[contains(text(), 'Organisationsnummer')]/following-sibling::*  → Org numbers (SE)
  //*[contains(text(), 'Org.nr')]/following-sibling::*     → Org numbers (NO)
  //*[contains(text(), 'CVR')]/following-sibling::*        → Org numbers (DK)

CSS Selector:
  .employee-card, .team-member, .person, .staff-card       → Person cards
  .contact-info, .contact-details                          → Contact blocks
  address, .address                                         → Physical addresses
```

## CLI Automation (Docker/Windows)

```bash
# Windows CLI (headless crawl)
screamingfrogseospider.exe \
  --crawl https://example-company.se \
  --headless \
  --output-folder "C:\data\crawl_output" \
  --export-format csv \
  --config "C:\config\extraction_rules.seospiderconfig"

# Bulk mode: crawl list of URLs from file
screamingfrogseospider.exe \
  --crawl-list "C:\data\company_urls.txt" \
  --headless \
  --output-folder "C:\data\crawl_output" \
  --export-tabs "Internal:All,Response Codes:Client Error (4xx),Custom Extraction:All"
```

## Orchestrator Integration (Python bridge)

```python
import subprocess, csv, json

def screaming_frog_crawl(urls: list[str], extraction_config: str) -> list[dict]:
    """Run Screaming Frog on a batch of URLs, return extracted data."""

    # Write URLs to temp file
    with open("temp_urls.txt", "w") as f:
        f.write("\n".join(urls))

    # Run Screaming Frog (headless, CLI)
    subprocess.run([
        "screamingfrogseospider.exe",
        "--crawl-list", "temp_urls.txt",
        "--headless",
        "--output-folder", "temp_output",
        "--config", extraction_config,
        "--export-format", "csv",
        "--export-tabs", "Custom Extraction:All",
        "--bulk-crawl",  # Don't recrawl existing
        "--overwrite",
    ], check=True, timeout=3600)

    # Parse CSV output back into our pipeline
    results = []
    with open("temp_output/custom_extraction_all.csv") as f:
        for row in csv.DictReader(f):
            results.append({
                "url": row["URL"],
                "title": row.get("Title", ""),
                "emails": row.get("Extraction 1", ""),
                "phones": row.get("Extraction 2", ""),
                "org_numbers": row.get("Extraction 3", ""),
                "contact_names": row.get("Extraction 4", ""),
            })
    return results
```

## Speed

- HTML-only crawl: 100-200 pages/min
- JS rendering: 20-50 pages/min
- 10,000 company sites (contact pages only, ~3 pages each): ~15-30 min
- Memory: ~2-4GB for large crawls

## In the Fallback Chain

```
Position: Licensed Tier
Primary use: Bulk static-site crawling (95% of company websites)
Not used for: WAF-protected sites, login-gated portals, SPAs
```

Screaming Frog is the **first line** for any open website. It's so fast and cheap that it replaces the entire HTTP tier for bulk. Only sites that return JS-only content or block the crawler escalate to Playwright/CloakBrowser.

## When to Use Which Tool

| Site Type | Tool | Reason |
|---|---|---|
| Static HTML, bulk (1000+ sites) | **Screaming Frog** | 100-200 pages/min, $199/yr, CSV export |
| Static HTML, single site | Trafilatura + requests | Lighter, no license needed |
| JS-heavy SPA | Playwright + CloakBrowser | SF JS rendering is slow, Playwright is specialized |
| CF-protected | CloakBrowser | Screaming Frog has no anti-bot |
| Login-gated portal | Sequentum / Browser-Use | SF can't handle auth flows |
| Full site to Markdown | Firecrawl | Prompt-based, no CSS rules needed |
| Contact/team pages specifically | **Screaming Frog** | Custom extraction rules built for this |

## Related

- [Sequentum](sequentum.md) — the visual-RPA escalation when SF fails
- [Crawlee](crawlee.md) — the OSS programmable alternative
- [Trafilatura](trafilatura.md) — single-page extraction (no license needed)
- [Firecrawl](firecrawl.md) — prompt-based alternative
- [Stealth Bypass Chain](stealth-bypass-chain.md) — for sites SF can't handle
