# Master Architecture Blueprint

> **Status:** Ratified design — implementation follows this document.
> **Last updated:** 2026-06-24

The single authoritative architecture document for the Nordic+EU adaptive data platform. Everything in `catalog/methods/`, `sources/`, `docs/infrastructure/`, and `src/` implements what is defined here.

---

## 1. System Overview

### 1.1 What We're Building

A self-healing, maximally-parallel data harvesting platform that:
- Covers **~40 million companies, 50M+ contacts, 100M+ vehicles** across 20 markets
- Uses **22+ harvesting methods** selected adaptively per target
- Runs **100% locally** with open-source tools (zero API costs for core extraction)
- Produces **GDPR-native, provenance-tracked** data with per-field confidence
- Outputs to FiveCRM, VehIQ, Datahub, and any ODBC-compatible destination

### 1.2 Core Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                                 │
│  OpenClaw / Chat │ Dashboard (Grafana) │ Prometheus │ MCP Gateway   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                     ADAPTIVE ORCHESTRATOR                            │
│  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Job Queue  │  │ Method    │  │ AIMD     │  │ Credential     │  │
│  │ (Redis)    │  │ Bandit    │  │ Concur-  │  │ Vault          │  │
│  │            │  │ Router    │  │ rency    │  │ (Fernet)       │  │
│  └────────────┘  └───────────┘  └──────────┘  └────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────────┐
        ▼                       ▼                           ▼
┌───────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  HTTP Tier    │    │  Stealth Tier     │    │  RPA Tier         │
│ curl_cffi     │    │ CloakBrowser      │    │ Screaming Frog    │
│ Trafilatura   │    │ FlareSolverr      │    │ Sequentum         │
│ Firecrawl     │    │ Crawlee+Playwright│    │ UiPath            │
│ Unstructured  │    │ Browser-Use agent │    │ Ranorex           │
└───────┬───────┘    └────────┬──────────┘    └────────┬──────────┘
        │                     │                        │
        └─────────────────────┼────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                                │
│  Raw Data → Trafilatura → Unstructured → spaCy/GLiNER NER           │
│          → Ollama LLM enrichment → Splink dedup → Fusion            │
│          → Confidence scoring → Postgres + pgvector                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Adaptive Method Router (The Brain)

### 2.1 Multi-Armed Bandit

Each host gets a bandit that tracks per-method performance:

```python
class AdaptiveRouter:
    def __init__(self):
        self.stats = {}  # host → {method: {successes, failures, latencies}}

    def choose_method(self, host: str, available_methods: list[str]) -> str:
        stats = self.stats.get(host, {})

        # 1. Always try the cheapest method first (explore)
        cheapest = sorted(available_methods, key=lambda m: METHOD_COST[m])[0]
        if cheapest not in stats or stats[cheapest]["failures"] < 3:
            return cheapest

        # 2. Pick best success/latency ratio (exploit)
        scores = {}
        for method in available_methods:
            s = stats.get(method, {})
            successes = s.get("successes", 0)
            failures = s.get("failures", 0)
            avg_latency = s.get("avg_latency", 5000)
            if successes + failures == 0:
                scores[method] = 0.5  # Unknown → give it a try
            else:
                success_rate = successes / (successes + failures)
                scores[method] = success_rate * (1.0 / (avg_latency / 1000))
        return max(scores, key=scores.get)

    def record(self, host: str, method: str, success: bool, latency_ms: int):
        if host not in self.stats:
            self.stats[host] = {}
        if method not in self.stats[host]:
            self.stats[host][method] = {"successes": 0, "failures": 0, "latencies": []}
        s = self.stats[host][method]
        if success:
            s["successes"] += 1
        else:
            s["failures"] += 1
        s["latencies"].append(latency_ms)
        s["avg_latency"] = sum(s["latencies"][-100:]) / len(s["latencies"][-100:])
```

### 2.2 Method Cost Ranking (cheapest first)

| Rank | Method | Cost per 1000 | Speed | WAF Survival |
|---|---|---|---|---|
| 1 | `curl_cffi` (TLS impersonate) | $0 | 500-1000 req/min | 50% |
| 2 | `trafilatura` (boilerplate strip) | $0 | 100-500 pgs/min | N/A (post-fetch) |
| 3 | `firecrawl` (Markdown extract) | $0 | 50-100 pgs/min | 60% |
| 4 | `screaming-frog` (bulk crawl) | ~$0.001 | 100-200 pgs/min | 40% |
| 5 | `cloudscraper` (CF basic) | $0 | 50-100 req/min | 70% |
| 6 | `flaresolverr` (CF solve) | $0 | 100-200 req/min | 75% |
| 7 | `crawlee+playwright` (browser) | $0 | 60-100 pgs/min | 80% |
| 8 | `cloakbrowser` (stealth) | $0 | 20-30 pgs/min | 98% |
| 9 | `browser-use` (AI agent) | $0 | 2-5 pgs/min | 85% |
| 10 | `sequentum` (RPA) | ~$0.01 | 1-3 pgs/min | 95% |
| 11 | `uipath` (enterprise RPA) | ~$0.05 | 1-2 pgs/min | 98% |
| 12 | `ranorex` (desktop) | ~$0.05 | 1-2 pgs/min | 100% (desktop) |

### 2.3 AIMD Adaptive Concurrency

Additive Increase / Multiplicative Decrease for worker scaling:

```
Start: concurrency = 1
On success: concurrency += 1 (explore up)
On 429/block: concurrency *= 0.5 (back off fast)
Ceiling: sources.yaml's max_concurrency per host
Floor: 1
```

```python
class AIMDController:
    def __init__(self, host: str, max_concurrency: int = 10):
        self.host = host
        self.concurrency = 1
        self.max = max_concurrency
        self.consecutive_successes = 0
        self.consecutive_failures = 0

    def on_success(self):
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        if self.consecutive_successes > 3:
            self.concurrency = min(self.max, self.concurrency + 1)
            self.consecutive_successes = 0

    def on_failure(self, status: int):
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        if status in (429, 403) or self.consecutive_failures > 2:
            self.concurrency = max(1, int(self.concurrency * 0.5))

    def on_block(self):
        self.consecutive_failures += 1
        self.concurrency = max(1, int(self.concurrency * 0.3))  # Heavy backoff
```

### 2.4 Source Racing (Hedged Requests)

Fire two methods simultaneously, use whichever returns first:

```python
async def source_race(host: str, url: str) -> dict:
    cheap_method = router.choose_method(host, METHOD_TIERS["cheap"])
    deep_method = router.choose_method(host, METHOD_TIERS["deep"])

    async with asyncio.TaskGroup() as tg:
        cheap_task = tg.create_task(scrape(url, cheap_method))
        deep_task = tg.create_task(scrape(url, deep_method))

    if cheap_task.done() and cheap_task.result():
        deep_task.cancel()  # Cancel the slower one
        return cheap_task.result()
    return deep_task.result()  # Fall through to deep result
```

---

## 3. Extraction Pipeline (end-to-end)

### 3.1 Input

```
sources.yaml → Crawlee RequestQueue → Parallel Workers
```

### 3.2 Per-URL Pipeline

```python
async def process_url(url: str, country: str, source_config: dict) -> dict:
    # 1. Fetch raw content
    html = await adaptive_fetch(url, source_config)

    # 2. Strip boilerplate
    clean_text = trafilatura.extract(html)

    # 3. Parse structured elements
    elements = unstructured.partition(html=html)

    # 4. First-pass NER (spaCy or GLiNER)
    entities = spacy_extract(clean_text, country) or gliner_extract(clean_text)

    # 5. LLM enrichment
    contacts = await llm_extract_contacts(clean_text)
    company = await llm_extract_company(clean_text)

    # 6. Entity resolution (Splink)
    company = splink_dedup(company, existing_db)

    # 7. Multi-source confidence scoring
    contacts = score_confidence(contacts, entities, source_config)

    # 8. Store
    await store_company(company)
    await store_contacts(contacts)

    return {"company": company, "contacts": contacts}
```

### 3.3 Confidence Scoring Algorithm

```python
def score_confidence(contact: dict, spacy_entities: dict, sources: list[str]) -> float:
    base = 0.0
    methods = 0

    # +0.50 per method that found this contact
    if contact.get("found_by_spacy"):
        base += 0.50
        methods += 1
    if contact.get("found_by_llm"):
        base += 0.50
        methods += 1
    if contact.get("found_by_regex"):
        base += 0.30
        methods += 1

    # +0.20 if email pattern matches name
    if email_matches_name(contact.get("email"), contact.get("name")):
        base += 0.20

    # +0.20 if multiple sources agree on title
    if contact.get("cross_validated_title"):
        base += 0.20

    # +0.10 if from official registry
    if contact.get("source_type") == "registry":
        base += 0.10

    # Cap at 0.99 (never claim 100%)
    return min(0.99, base)

# Confidence tiers:
# 0.90-0.99: Production-ready (3+ methods agree)
# 0.75-0.89: High confidence (2 methods agree)
# 0.50-0.74: Moderate (single method only)
# 0.00-0.49: Low (needs human review)
```

---

## 4. Country Coverage Architecture

### 4.1 Per-Country Pipeline Template

Every country in sources.yaml follows this template:

```yaml
SE:  # Sweden
  name: Sverige
  language: sv
  currency: SEK
  registries:
    - name: Bolagsverket
      url: https://bolagsverket.se
      api: https://api.bolagsverket.se/naringsliv/v1
      type: open_api
      data: [company, directors, financial_basic]
      refresh: weekly
      waf: none
      method: curl_cffi
      proxy_tier: none
      bulk: true  # Can download ALL companies at once
      max_concurrency: 5

    - name: Transportstyrelsen
      url: https://transportstyrelsen.se
      api: null
      type: scrape
      data: [vehicles, vehicle_owners]
      refresh: daily
      waf: soft
      method: crawlee
      proxy_tier: self-hosted
      bulk: false  # Per-vehicle lookup
      max_concurrency: 3

  nlp:
    spacy_model: sv_core_news_lg
    ner_labels: [PER, ORG, LOC, MONEY, DATE]
    title_patterns: [VD, Verkställande direktör, Styrelseordförande, ...]
    org_number_pattern: '\d{6}-\d{4}'
```

### 4.2 Country Tiers

| Tier | Markets | Approach | Refresh |
|---|---|---|---|
| **Tier 1 (Open Bulk)** | SE, NO, DK, UK, FR, NL | Direct API download, full dataset weekly | Weekly |
| **Tier 2 (Open API)** | FI, BE, IE, AT | API paginated, daily incremental | Daily |
| **Tier 3 (Scraped)** | DE, IT, ES, PL, CZ, HU, PT, IS, CH | Per-entity scrape with adaptive methods | Monthly |
| **Tier 4 (Aggregated)** | All markets | Cross-reference, LEI matching, enrichment | Continuous |

---

## 5. Infrastructure Architecture

### 5.1 Resource Requirements

| Environment | RAM | CPU | GPU | Storage | Workers |
|---|---|---|---|---|---|
| **Dev (laptop)** | 32GB | 8-core | RTX 4090 (optional) | 500GB SSD | 3-5 |
| **Prod (server)** | 128GB | 32-core | 2x A100 or 4x RTX 4090 | 4TB NVMe | 20-50 |
| **Cloud (optional)** | Auto-scale | Auto-scale | Optional | 10TB+ | Auto-scale |

### 5.2 Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Compose Stack (local) or Kubernetes (cloud)         │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure:                                             │
│    Redis (queue + cache) · Postgres + pgvector (storage)    │
│    Prometheus + Grafana (monitoring)                         │
│                                                              │
│  Proxy Layer:                                                │
│    Rota (rotation) · Tor Pool (4 circuits)                   │
│                                                              │
│  Scraping Layer:                                             │
│    FlareSolverr · CloakBrowser · Browser Workers (scale)    │
│                                                              │
│  AI Layer:                                                   │
│    Ollama · vLLM · Unstructured · Surya (OCR)               │
│                                                              │
│  Application Layer:                                          │
│    Orchestrator API · Dashboard                              │
│    MCP Gateway (Brave Search, Postgres, Docker, Slack)       │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Scaling Strategy

- **Workers:** Scale horizontally (`docker compose up --scale worker-browser=N`)
- **GPU:** If available, local LLM + OCR at zero cost. If not, CPU-only mode (slower but works)
- **Storage:** Postgres with partitioning by country + year for financial data
- **Proxies:** Auto-scale proxy pool from free lists; self-hosted pool for critical sites

---

## 6. Data Model

### 6.1 Core Entities

```
Company
├── org_number (national ID)
├── lei_number (cross-border golden key)
├── legal_name, trading_name
├── address, city, postal_code, country
├── website, email, phone
├── industry, industry_code (NACE/SNI)
├── employee_count, revenue, founding_year
├── status (active, inactive, liquidated)
├── confidence, last_verified
└── source_urls[], extraction_methods[]

Contact
├── org_number → Company
├── full_name, first_name, last_name
├── title, department
├── email, phone, mobile
├── linkedin_url
├── confidence, methods_used[]
└── last_verified

Vehicle
├── registration (license plate)
├── vin, make, model, year
├── owner_org_number → Company
├── country, status
└── source_urls[]

FinancialData
├── org_number, fiscal_year
├── revenue, operating_profit, net_income
├── total_assets, total_equity
├── employee_count
└── filing_type, source_url
```

### 6.2 Cross-Border Key: LEI/GLEIF

LEI (Legal Entity Identifier) is the golden key that links companies across borders. Same company in SE, DK, DE, UK → same LEI. All GLEIF data is free and open.

```python
LEI_LOOKUP_URL = "https://api.gleif.org/api/v1/lei-records"
```

---

## 7. Compliance Architecture

### 7.1 Source Tiers

| Tier | Sources | Legal Basis | Example |
|---|---|---|---|
| **T1 (Open Gov)** | Official registries, open data | Public information | Bolagsverket, Companies House, CVR, Brreg, SIRENE |
| **T2 (Public Web)** | Company websites, public pages | Legitimate interest | Contact pages, about pages, team pages |
| **T3 (Aggregated)** | GLEIF, OpenCorporates, OpenSanctions | Public data aggregation | LEI, Wikidata |
| **T4 (Derived)** | Computed from T1-T3 | Our own analysis | Confidence scores, enrichment |
| **T5 (ToS-Restricted)** | Competitor tools, LinkedIn, Facebook | **Benchmarking only** | Apollo, Lusha — never ingested |

### 7.2 GDPR Compliance

- **Right to be forgotten:** Automatic deletion pipeline — remove all records for a natural person within 30 days
- **Data minimization:** Only store what's publicly available + what we can prove legitimate interest for
- **Provenance:** Every record tracks source URLs + extraction method + timestamp
- **Consent:** Official registry data = public, no consent needed. Website data = legitimate interest with opt-out mechanism

---

## 8. Implementation Roadmap

| Phase | Timeline | Deliverable | Key Decision |
|---|---|---|---|
| **Phase 0: Nordic MVP** | Weeks 1-4 | SE+NO+DK scrape pipeline, full company+contact database | Go/no-go based on data quality |
| **Phase 1: DACH + Benelux** | Weeks 5-8 | DE+AT+CH+NL+BE+FR scrapers, cross-border matching | UI-automation tier active? |
| **Phase 2: Southern + Central** | Weeks 9-12 | IT+ES+PT+PL+CZ+HU+UK+IE, vehicle data integration | Scale infrastructure? |
| **Phase 3: Production** | Weeks 13-16 | API, dashboard, export pipelines, monitoring, auto-scaling | Cloud or on-prem? |
| **Phase 4: Market** | Week 17+ | FiveCRM integration, VehIQ integration, external API | Pricing model? |

---

## 9. Key Decisions Pending

1. **LinkedIn-at-scale:** T5 (ToS-risk). Decision: benchmarking only, never ingested.
2. **Personal vehicle data:** GDPR-sensitive. Decision: only fleet/company-owned vehicles.
3. **Cloud vs on-prem:** Local works for Phase 0-2. Phase 3 may need cloud for scale.
4. **Local LLM vs Claude API:** Local (Ollama) is free and good enough for 90%. Claude fallback for 10%.
5. **Sequentum license ROI:** Use for DE+IT+ES registries where OSS fails. ~$400/mo justified by 30% coverage increase in those markets.

---

© Protosell / SIAX. See [`COMPLIANCE.md`](../docs/COMPLIANCE.md) for legal details.
