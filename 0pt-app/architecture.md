# 0pt.app — Technical Architecture

> **Stack:** Next.js 15 + TypeScript + shadcn/ui + Vercel (frontend) · FastAPI + Redis + Crawlee (backend)
> **Data Engine:** nordic-eu-data-platform (CloakBrowser, Unstructured, Ollama, Splink, etc.)
> **Database:** Postgres + pgvector · **Cache:** Redis · **Storage:** Local / S3-compatible

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         0pt.app (Next.js + Vercel)                       │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Service      │  │ Order        │  │ Delivery     │  │ Account &    │ │
│  │ Catalog      │  │ Wizard       │  │ Dashboard    │  │ Billing      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐│
│  │  AI Order Assistant (Ollama / LM Studio)                              ││
│  │  "Jag vill ha alla IT-bolag i Göteborg med fler än 50 anställda"     ││
│  │  → Rekommenderar tjänst + estimerar pris/tid/volym                   ││
│  └──────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST API (JSON)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Orchestrator API (FastAPI)                           │
│                                                                          │
│  POST /api/orders           Create order                                 │
│  GET  /api/orders/{id}      Order status                                 │
│  GET  /api/orders/{id}/data Download result                              │
│  POST /api/estimate         Get price/time estimate                      │
│  GET  /api/catalog          List available services                      │
│  POST /api/subscribe        Create subscription                          │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ Order Queue  │  │ Job Scheduler│  │ Price Engine │                   │
│  │ (Redis)      │  │ (Celery)     │  │              │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  nordic-eu-data-platform (data engine)                    │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐ │
│  │ Adaptive Router│  │ Scraping Workers│  │ Processing Pipeline        │ │
│  │ (multi-armed   │  │ (Crawlee +     │  │ Unstructured → spaCy →    │ │
│  │  bandit)       │  │  CloakBrowser) │  │  Ollama → Splink → DB      │ │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘ │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐ │
│  │ Proxy Fabric   │  │ OCR Pipeline   │  │ MCP Gateway                 │ │
│  │ (Rota + Tor)   │  │ (PaddleOCR,    │  │ (Brave, Postgres, Docker)   │ │
│  │                │  │  Surya, VL)    │  │                             │ │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Order → Delivery

```
1. ORDER CREATED
   Customer → 0pt.app UI → POST /api/orders
   { service: "ICP_LEAD_LIST_SE", filters: { industry: "IT", employees: "10-50" }, output: "csv" }

2. PRICE CALCULATION
   Price Engine estimates: data volume, methods needed, time, confidence tier
   → Returns: { estimated_cost: 2495, estimated_time: "4h", estimated_records: 3200 }

3. CUSTOMER APPROVES
   Payment processed (Stripe) → Order status: "queued"

4. JOB EXECUTION
   Orchestrator → Job Scheduler → Appropriate workers:
     - Tier 1 (easy): curl_cffi → Bolagsverket API (free, fast)
     - Tier 2 (if needed): Crawlee → Company websites (contact page extraction)
     - Tier 3 (if needed): CloakBrowser → CF-protected sites
     - Processing: Unstructured → spaCy NER → Ollama enrichment → Splink dedup
     - Confidence scoring per field

5. QUALITY CHECK
   Automated QA: confidence thresholds, completeness checks
   If confidence < 70% → flag for manual review
   If OK → status: "ready_for_delivery"

6. DELIVERY
   Customer notified (email/webhook)
   Download available (CSV, JSON, Parquet, Excel)
   API endpoint active (if subscription)

7. SUBSCRIPTION (if applicable)
   Scheduler runs on cadence (daily/weekly/monthly)
   Delta detection: only new/changed records
   Auto-delivery via webhook or API
```

---

## Frontend Architecture (0pt.app — Next.js)

```
0pt.app/
├── app/
│   ├── layout.tsx              # Root layout (siax.io design system)
│   ├── page.tsx                # Landing page
│   ├── catalog/
│   │   ├── page.tsx            # Service catalog browser
│   │   ├── [category]/
│   │   │   └── page.tsx        # Category detail
│   │   └── [service]/
│   │       └── page.tsx        # Service detail + order
│   ├── order/
│   │   ├── page.tsx            # Order wizard (AI-assisted)
│   │   ├── [id]/
│   │   │   └── page.tsx        # Order status + download
│   ├── dashboard/
│   │   ├── page.tsx            # Customer dashboard
│   │   ├── orders/             # Order history
│   │   ├── subscriptions/      # Active subscriptions
│   │   └── api-keys/           # API key management
│   ├── api/
│   │   ├── orders/             # Order CRUD endpoints
│   │   ├── estimate/           # Price estimation
│   │   ├── catalog/            # Dynamic catalog
│   │   └── webhooks/           # External integrations
│   └── admin/
│       ├── page.tsx            # Admin dashboard
│       ├── jobs/               # Job monitoring
│       └── customers/          # Customer management
├── components/
│   ├── ui/                     # shadcn/ui components
│   ├── catalog/                # Service cards, filters
│   ├── order/                  # Order wizard steps
│   ├── dashboard/              # Charts, stats, tables
│   └── ai/                     # AI assistant chat widget
├── lib/
│   ├── api.ts                  # Backend API client
│   ├── catalog.ts              # Service catalog data
│   ├── pricing.ts              # Price calculation
│   ├── auth.ts                 # Authentication
│   └── stripe.ts               # Payment integration
└── styles/                     # Tailwind + siax design tokens
```

---

## Backend Architecture (Orchestrator — FastAPI)

```
orchestrator/
├── main.py                     # FastAPI app
├── routes/
│   ├── orders.py               # Order CRUD
│   ├── catalog.py              # Service catalog
│   ├── estimate.py             # Price/time estimation
│   ├── delivery.py             # Result delivery
│   └── admin.py                # Admin endpoints
├── services/
│   ├── order_service.py        # Order lifecycle management
│   ├── price_engine.py         # Dynamic pricing
│   ├── job_dispatcher.py       # Route jobs to workers
│   ├── quality_checker.py      # Automated QA
│   └── notification.py         # Email/webhook notifications
├── workers/
│   ├── scraping_worker.py      # General scraping jobs
│   ├── ocr_worker.py           # OCR processing jobs
│   ├── enrichment_worker.py    # NER + LLM enrichment
│   └── dataset_worker.py       # Dataset compilation jobs
├── models/
│   ├── order.py                # Order schema
│   ├── service.py              # Service definition schema
│   └── customer.py             # Customer schema
├── integrations/
│   ├── fivecrm.py              # FiveCRM export
│   ├── vehiq.py                # VehIQ integration
│   ├── hubspot.py              # HubSpot export
│   ├── salesforce.py           # Salesforce export
│   └── stripe.py               # Payment processing
└── config.py                   # Environment config
```

---

## Database Schema (0pt.app-specific tables)

```sql
-- Orders
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL,
    service_id TEXT NOT NULL,          -- e.g., "ICP_LEAD_LIST_SE"
    service_category TEXT NOT NULL,    -- e.g., "lead_gen"
    parameters JSONB NOT NULL,         -- Filters, preferences
    status TEXT DEFAULT 'pending',     -- pending, estimated, approved, queued, running, qa, ready, delivered, failed
    estimated_cost NUMERIC,
    estimated_time_minutes INTEGER,
    estimated_records INTEGER,
    actual_cost NUMERIC,
    actual_time_minutes INTEGER,
    actual_records INTEGER,
    confidence_score REAL,
    output_format TEXT DEFAULT 'csv', -- csv, json, parquet, excel, api
    output_url TEXT,                   -- Download URL
    api_endpoint TEXT,                 -- For subscription API access
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL,
    service_id TEXT NOT NULL,
    cadence TEXT NOT NULL,             -- daily, weekly, monthly, quarterly
    status TEXT DEFAULT 'active',
    stripe_subscription_id TEXT,
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Customers
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    company TEXT,
    stripe_customer_id TEXT,
    api_key TEXT UNIQUE,
    credits_remaining INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Price rules
CREATE TABLE price_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id TEXT NOT NULL,
    base_price NUMERIC NOT NULL,
    price_per_record NUMERIC,
    price_per_hour NUMERIC,
    min_price NUMERIC,
    max_price NUMERIC,
    factors JSONB                      -- { complexity: 1.5, urgency: 2.0, volume_discount: 0.8, ... }
);
```

---

## AI Order Assistant

```python
# Natural language → service recommendation
async def ai_assist(query: str, customer_context: dict) -> dict:
    """Convert Swedish/English natural language to service recommendation."""
    prompt = f"""Customer query: "{query}"
    Available services: {json.dumps(CATALOG_SUMMARY)}
    Customer context: {json.dumps(customer_context)}

    Return JSON:
    {{
        "recommended_service": "service_id",
        "estimated_price_range": "500-2500 kr",
        "estimated_time": "2-4 hours",
        "estimated_records": "1000-5000",
        "confidence_tier": "high",
        "explanation_sv": "Förklaring på svenska...",
        "alternatives": ["alt_service_1", "alt_service_2"]
    }}"""

    resp = client.chat.completions.create(
        model="phi4:14b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
```

---

## Integration Points

| System | Direction | Data |
|---|---|---|
| **nordic-eu-data-platform** | Backend engine | All data extraction, scraping, enrichment |
| **siax.io** | Frontend host + content | Blog posts → 0pt.app landing pages |
| **VehIQ** | Data source + consumer | Vehicle data input; analytics output |
| **FiveCRM** | Export target | Company + contact data → CRM |
| **Stripe** | Payment | One-time + subscription billing |
| **Vercel** | Deployment | Next.js hosting |
| **PostHog** | Analytics | User behavior tracking |
| **Resend** | Email | Order confirmations, delivery notifications |

---

Next: See [Pricing Model](pricing.md) for complete pricing strategy.
