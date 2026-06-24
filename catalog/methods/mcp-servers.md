# MCP Servers — Model Context Protocol Integration

> **MCP:** https://modelcontextprotocol.io | **Purpose:** Standardized AI-tool integration
> All MCP servers the platform can call — web search, database access, code execution, file system, API gateways

The Model Context Protocol (MCP) lets AI agents call tools through a standardized protocol. For the data platform, MCP servers provide: web search for company discovery, database read/write for the orchestrator, browser control for agents, filesystem access for batch processing, and log monitoring.

## MCP Servers in the Platform

### 1. Brave Search MCP — Company + Contact Discovery

```bash
npx @anthropic/mcp-server-brave-search --api-key $BRAVE_API_KEY
```

```python
# Use Brave Search to find company websites, contact pages, news
# The adaptive router calls this when sources.yaml doesn't have a URL
result = mcp_call("brave_search", {
    "query": "AB Volvo Göteborg kontakt kontaktperson ledning",
    "count": 5,
})
# Returns: [{title, url, description}] — top Google results for the company
# Pipe URLs into Crawlee/Playwright for extraction
```

### 2. Puppeteer MCP — Browser Control from Orchestrator

```bash
npx @anthropic/mcp-server-puppeteer
```

```python
# Let the orchestrator drive a browser through MCP
# Alternative to direct Playwright — useful when orchestrator is in
# a different container than the browser
result = mcp_call("puppeteer_navigate", {"url": "https://example-company.se/kontakt"})
content = mcp_call("puppeteer_screenshot", {"name": "screenshot"})
data = mcp_call("puppeteer_click", {"selector": ".team-section"})
```

### 3. Filesystem MCP — Batch File Processing

```bash
npx @anthropic/mcp-server-filesystem --directory C:\data\raw
```

```python
# Bulk read/write for batch processing
# Workers write extracted data to shared volume → orchestrator reads via MCP
files = mcp_call("list_directory", {"path": "/extracted/2026-06-24"})
for f in files:
    data = mcp_call("read_file", {"path": f"/extracted/2026-06-24/{f}"})
    # Process and store
```

### 4. Postgres MCP — Database Access

```bash
npx @anthropic/mcp-server-postgres --connection-string postgresql://platform:pass@localhost:5432/nordic_eu_data
```

```python
# Query enriched data from chat / API
results = mcp_call("postgres_query", {
    "query": """
        SELECT company_name, org_number, confidence
        FROM enriched_companies
        WHERE country = 'DE' AND industry LIKE '%automotive%'
        LIMIT 50
    """
})
```

### 5. GitHub MCP — Repo + Code Management

```bash
npx @anthropic/mcp-server-github --token $GITHUB_TOKEN
```

```python
# Auto-commit extracted data, manage code
# Create issues for failed extractions needing human review
mcp_call("create_issue", {
    "repo": "nordic-eu-data-platform",
    "title": "Handelsregister.de blocked — 403 errors on batch 2026-06-24-3",
})
```

### 6. Docker MCP — Container Orchestration

```bash
npx @anthropic/mcp-server-docker
```

```python
# Scale workers based on queue depth
queue_depth = redis.llen("extraction_queue")
if queue_depth > 10000:
    mcp_call("docker_compose_scale", {
        "service": "worker-browser",
        "replicas": 10,  # Scale up from 3 to 10
    })
elif queue_depth < 100:
    mcp_call("docker_compose_scale", {
        "service": "worker-browser",
        "replicas": 3,   # Scale down to save resources
    })
```

### 7. Slack/Teams MCP — Alerting + Human-in-the-Loop

```bash
npx @anthropic/mcp-server-slack --token $SLACK_TOKEN
```

```python
# Escalate to human when all methods fail
if all_methods_failed and retries_exhausted:
    mcp_call("slack_send_message", {
        "channel": "#platform-alerts",
        "text": f"All methods failed for {url}. Needs manual review. Error: {error}"
    })
```

### 8. SerpAPI / Google Search MCP — Web Research

Alternative to Brave Search. Better for some EU languages.

```bash
npx @anthropic/mcp-server-serpapi --api-key $SERPAPI_KEY
```

### 9. Tavily MCP — AI-Optimized Search

```bash
npx @anthropic/mcp-server-tavily --api-key $TAVILY_API_KEY
```

Better for AI to answer "what is the CEO of company X?"

## Full MCP Stack in docker-compose

```yaml
services:
  mcp-brave-search:
    image: node:20-alpine
    command: npx @anthropic/mcp-server-brave-search
    environment:
      BRAVE_API_KEY: ${BRAVE_API_KEY}
    restart: unless-stopped

  mcp-postgres:
    image: node:20-alpine
    command: npx @anthropic/mcp-server-postgres
    environment:
      DATABASE_URL: postgresql://platform:${DB_PASSWORD}@postgres:5432/nordic_eu_data
    depends_on:
      - postgres
    restart: unless-stopped

  mcp-docker:
    image: node:20-alpine
    command: npx @anthropic/mcp-server-docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker socket access
    restart: unless-stopped

  mcp-filesystem:
    image: node:20-alpine
    command: npx @anthropic/mcp-server-filesystem --directory /data
    volumes:
      - worker_data:/data
    restart: unless-stopped
```

## MCP as the Platform's Control Plane

```
┌───────────────────────────────────────────────────────────────┐
│                     OpenClaw / Chat Interface                  │
└───────────────────────────┬───────────────────────────────────┘
                            │ "scrape all German automotive companies"
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                     MCP Gateway (router)                       │
├─────────┬─────────┬──────────┬─────────┬──────────┬───────────┤
│ Brave   │ Puppeteer│ Postgres │ Docker  │ Slack    │ FileSystem│
│ Search  │ Browser  │  Query   │ Scale   │ Alerts   │  Read CSV │
└────┬────┴────┬─────┴────┬─────┴────┬────┴────┬─────┴────┬──────┘
     │         │          │          │         │          │
     ▼         ▼          ▼          ▼         ▼          ▼
  Find       Extract    Store      Scale    Notify     Process
  URLs       data       data       workers  human      batches
```

## Related

- [OpenClaw](openclaw.md) — the chat/control interface that triggers MCP
- [Crawlee](crawlee.md) — orchestrator that MCP commands route to
- [Docker Full Stack](../../docs/infrastructure/docker-compose.full-stack.yml)
- [Stealth Bypass Chain](stealth-bypass-chain.md)
