# OpenClaw — Personal AI Assistant Gateway Integration

> **Framework:** OpenClaw (open-source AI assistant gateway) | **Local LLM:** Ollama

OpenClaw provides a channel-based AI assistant gateway that can be used as a control plane for the data platform — triggering scrapes, monitoring progress, receiving alerts, and running interactive data queries via chat interfaces (WhatsApp, Telegram, Discord, etc.).

## What it solves

The data platform needs a human-in-the-loop control surface. OpenClaw gives you:
- Trigger scrape jobs via chat ("scrape all Swedish companies in SNI 45")
- Receive progress alerts ("45,000/100,000 companies processed, 92% success rate")
- Query the database conversationally ("how many German companies in automotive with >50 employees?")
- Debug failures interactively ("why did Handelsregister.de block worker #7?")

## Integration Pattern

```python
# OpenClaw channel → platform orchestrator
# When OpenClaw receives a command, it calls the platform API

import requests

# Register a skill in OpenClaw for platform control
skill = {
    "name": "nordic-eu-data-platform",
    "description": "Control the Nordic+EU B2B data platform",
    "commands": {
        "scrape_country": {
            "description": "Start scraping a country",
            "parameters": {"country": "SE/NO/DK/DE/etc."},
            "handler": "http://localhost:8000/api/jobs/scrape",
        },
        "scrape_status": {
            "description": "Get scraping status",
            "handler": "http://localhost:8000/api/jobs/status",
        },
        "query_companies": {
            "description": "Query enriched company database",
            "parameters": {"country": "SE", "sni": "45", "min_employees": "50"},
            "handler": "http://localhost:8000/api/query/companies",
        },
        "health_check": {
            "description": "Run full platform health check",
            "handler": "http://localhost:8000/api/health",
        },
    }
}
```

## Use Cases

1. **Remote job trigger**: "scrape all French companies in the SIRENE database" → starts Crawlee workers
2. **Progress monitoring**: OpenClaw pushes periodic updates to chat channel
3. **Alert escalation**: worker pool saturated, proxy pool depleted, registry down → OpenClaw message
4. **Interactive debugging**: "show last 10 errors" → returns stack traces + recovery actions
5. **Database query**: "give me all Swedish IT consulting companies 10-50 employees" → returns CSV via chat

## Local LLM Integration

OpenClaw routes through Ollama (uncapped, free):

```yaml
# openclaw config
llm:
  provider: ollama
  model: qwen2.5:14b
  api_base: http://localhost:11434/v1

skills:
  - name: nordic-eu-data-platform
    endpoint: http://localhost:8000/api
    auth_token: ${PLATFORM_API_KEY}
```

## Related

- [Ollama + LM Studio](lmstudio-ollama.md) — the LLM backend
- [Crawlee Orchestrator](crawlee.md) — handles the actual jobs
- [Docker Full Stack](docker-compose.full-stack.yml) — OpenClaw runs in the compose stack
