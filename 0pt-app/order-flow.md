# 0pt.app — Order Flow & API

> Complete customer journey from discovery to delivery. API-first design for all operations.

---

## Order Lifecycle

```
  ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ DISCOVER │ ──► │ ESTIMATE │ ──► │  ORDER   │ ──► │  QUEUE   │ ──► │ RUNNING  │
  └─────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                                           │
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐         │
  │ ARCHIVED │ ◄── │ DELIVERED│ ◄── │  QA/REVIEW│ ◄── │ COMPLETE │ ◄───────┘
  └──────────┘     └──────────┘     └──────────┘     └──────────┘

  FAILED ──► retry (auto) or manual review
  CANCELLED ──► refund if pre-execution
```

### Statuses

| Status | Description | Customer Visible | Actions Available |
|---|---|---|---|
| `pending` | Order created, not yet estimated | Yes | Edit, Cancel |
| `estimated` | Price/time estimate ready | Yes | Approve, Edit, Cancel |
| `approved` | Customer approved, payment pending | Yes | Pay, Cancel |
| `queued` | Payment done, waiting for worker | Yes | Cancel (if not started) |
| `running` | Workers processing | Yes | — |
| `qa_review` | Automated QA finished, confidence check | Partially | — |
| `ready` | Data ready for delivery | Yes (notified) | Download, View Preview |
| `delivered` | Customer downloaded data | Yes | Download again, Request update |
| `failed` | Job failed | Yes (with reason) | Retry, Cancel, Contact support |
| `cancelled` | Cancelled (by customer or system) | Yes | Re-order |

---

## REST API

### Base URL: `https://0pt.app/api/v1`

### Authentication

```
Authorization: Bearer <API_KEY>
```

API keys generated per customer in dashboard.

### Endpoints

#### Orders

```
POST   /orders                    Create order
GET    /orders                    List customer orders
GET    /orders/{id}               Order details + status
PATCH  /orders/{id}               Update pending order
DELETE /orders/{id}               Cancel order
GET    /orders/{id}/data          Download order data
GET    /orders/{id}/preview       Preview first 10 records
POST   /orders/{id}/retry         Retry failed order
```

#### Estimates

```
POST   /estimates                 Get price/time estimate
```

Request:
```json
{
  "service_id": "ICP_LEAD_LIST_SE",
  "parameters": {
    "industry": "IT",
    "employees_min": 10,
    "employees_max": 50,
    "country": "SE",
    "roles": ["VD", "CEO", "CTO", "Marknadschef"],
    "output_format": "csv",
    "urgency": "standard"
  }
}
```

Response:
```json
{
  "estimate_id": "est_abc123",
  "service": "ICP Lead List — Sweden",
  "estimated_cost_low": 2245,
  "estimated_cost_high": 3365,
  "estimated_time_hours": 4,
  "estimated_records_low": 2500,
  "estimated_records_high": 4000,
  "confidence_tier": "high",
  "breakdown": {
    "base_price": 1995,
    "volume_discount": "0%",
    "complexity_factor": 1.2,
    "urgency_factor": 1.0
  },
  "valid_until": "2026-06-25T12:00:00Z"
}
```

#### Catalog

```
GET    /catalog                   List all services
GET    /catalog/{category}        Services by category
GET    /catalog/{service_id}      Service details
```

#### AI Assistant

```
POST   /assistant/query           Natural language → service recommendation
```

Request:
```json
{
  "query": "Jag vill ha alla svenska IT-bolag med 10-50 anställda och deras beslutsfattare",
  "context": {
    "previous_orders": ["ICP_LEAD_LIST_SE"],
    "preferred_format": "csv"
  }
}
```

Response:
```json
{
  "recommended_service": "ICP_LEAD_LIST_SE",
  "confidence": 0.95,
  "estimated_price": "~2 500 kr",
  "estimated_time": "3-5 timmar",
  "estimated_records": "~3 200 bolag, ~9 500 kontakter",
  "explanation": "Detta matchar vår ICP Lead List-tjänst. Vi hämtar data från Bolagsverket (alla IT-bolag), extraherar kontaktpersoner från deras webbplatser, och berikar med email och telefon där det finns tillgängligt. Du får en CSV-fil med alla fält.",
  "alternatives": [
    {"service": "COMPANY_DB_SE", "reason": "Bara bolagsdata, billigare (995 kr)"},
    {"service": "LEAD_FEED_DAILY", "reason": "Löpande leverans av nya leads (1 995 kr/mån)"}
  ]
}
```

#### Subscriptions

```
POST   /subscriptions             Create subscription
GET    /subscriptions              List subscriptions
GET    /subscriptions/{id}         Subscription details
PATCH  /subscriptions/{id}         Update subscription
DELETE /subscriptions/{id}         Cancel subscription
GET    /subscriptions/{id}/data    Latest delivery
```

#### Webhooks

```
POST   /webhooks/register         Register webhook endpoint
GET    /webhooks                  List registered webhooks
DELETE /webhooks/{id}             Remove webhook
POST   /webhooks/test             Send test event
```

Webhook events:
```json
{
  "event": "order.completed",
  "order_id": "ord_xyz789",
  "status": "ready",
  "data_url": "https://0pt.app/api/v1/orders/ord_xyz789/data",
  "timestamp": "2026-06-24T15:30:00Z"
}
```

---

## Customer Dashboard

Every customer gets a dashboard at `0pt.app/dashboard` showing:

- **Active Orders** — Status, progress bar, estimated completion
- **Order History** — All past orders, downloadable
- **Subscriptions** — Active subscriptions, next delivery date
- **Credits** — Remaining credits, purchase more
- **API Keys** — Generate, rotate, revoke
- **Usage Stats** — Monthly spending, records delivered, average confidence
- **Saved Templates** — Reusable order configurations

---

## Admin Dashboard (Internal)

At `0pt.app/admin` for SIAX team:

- **Job Queue Monitor** — All running/queued jobs, worker status, queue depth
- **Revenue Dashboard** — Daily/weekly/monthly revenue, by service, by customer
- **Failure Monitor** — Failed jobs, error patterns, retry queue
- **Worker Health** — CPU, memory, proxy pool status, WAF block rates
- **Customer Management** — Customer list, order history, credits
- **Catalog Manager** — Add/edit services, update prices, toggle availability
- **System Logs** — Full extraction logs, method stats, error traces

---

## Notification Flow

| Trigger | Channel | Content |
|---|---|---|
| Order created | Email | Confirmation + order ID |
| Estimate ready | Email | Price + time estimate |
| Payment confirmed | Email | Receipt |
| Job started | Email (optional) | "Your data is being extracted" |
| Job at 50% | — | (Dashboard only) |
| Job completed | Email + Webhook | "Your data is ready" + download link |
| Job failed | Email | Error description + retry button |
| Subscription renewal | Email | Upcoming charge notice |
| Credits low | Email | "You have 100 credits remaining" |

---

Next: See [Integrations](integrations.md) for CRM/ERP/BI export options.
