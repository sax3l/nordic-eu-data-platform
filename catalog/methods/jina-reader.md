# Jina AI Reader — Free URL-to-Markdown

> **Service:** https://r.jina.ai | **GitHub:** https://github.com/jina-ai/reader | **Cost:** Free (no API key needed)

Takes any URL and returns the main content as clean Markdown. No scraping, no selectors, no boilerplate. One HTTP call → clean Markdown ready for LLM processing.

```python
import requests
# Just prepend r.jina.ai to any URL
content = requests.get("https://r.jina.ai/https://example-company.se/om-oss").text
# → Clean Markdown, ready for LLM

# Self-host (no limits):
# docker compose up -d  (from github.com/jina-ai/reader)
```

Rate: ~20 req/min free, unlimited self-hosted. Use for quick extraction; Firecrawl for bulk.
