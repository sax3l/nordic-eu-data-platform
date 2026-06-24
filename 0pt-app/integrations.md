# 0pt.app — Integrations & Export Targets

> How 0pt.app delivers data into the customer's existing tools.

---

## Direct CRM Exports

### FiveCRM (Primary — SIAX customers)
```python
# Auto-export enriched data directly to FiveCRM
POST /api/v1/export/fivecrm
{
  "order_id": "ord_xyz",
  "fivecrm_config": {
    "api_key": "encrypted",
    "module": "Companies",       # or Contacts, Deals
    "field_mapping": {
      "company_name": "Name",
      "org_number": "custom_orgnr",
      "email": "Email",
      "phone": "Phone"
    },
    "duplicate_check": "org_number"  # Upsert on org number
  }
}
```

### HubSpot
```python
# Export to HubSpot CRM
POST /api/v1/export/hubspot
{
  "order_id": "ord_xyz",
  "hubspot_config": {
    "access_token": "encrypted",
    "object_type": "companies",   # companies, contacts, deals
    "field_mapping": { ... }
  }
}
```

### Salesforce
```python
# Export to Salesforce
POST /api/v1/export/salesforce
{
  "order_id": "ord_xyz",
  "sf_config": {
    "instance_url": "https://xxx.my.salesforce.com",
    "access_token": "encrypted",
    "object": "Account",          # Account, Contact, Lead
    "field_mapping": { ... }
  }
}
```

### Blikk
```python
# Export to Blikk (existing SIAX integration)
POST /api/v1/export/blikk
{
  "order_id": "ord_xyz",
  "format": "blikk_csv"           # Blikk-specific CSV format
}
```

### Generic CSV/Excel
```
# Direct download links for any system:
GET /api/v1/orders/{id}/data?format=csv      → CSV file
GET /api/v1/orders/{id}/data?format=json     → JSON file
GET /api/v1/orders/{id}/data?format=parquet  → Parquet file
GET /api/v1/orders/{id}/data?format=excel    → Excel file
```

---

## Google Sheets Integration

```
# One-click export to Google Sheets
POST /api/v1/export/google-sheets
{
  "order_id": "ord_xyz",
  "sheet_name": "ICP Leads Sweden 2026"
}
# → Creates a new Google Sheet with the data
# → Customer authenticates via OAuth on first use
```

---

## BI & Analytics Exports

### Power BI / Microsoft Fabric
```
# Direct connector for Power BI
# Use the 0pt.app API as a Power BI data source:
GET /api/v1/orders/{id}/data?format=json
# → Import into Power BI via Web connector
# → Refresh schedule: subscription auto-delivers fresh data
```

### Looker Studio
```
# Direct connector for Looker Studio
# Use the 0pt.app API as a data source
```

---

## Webhook Delivery

```
POST /api/v1/webhooks/register
{
  "url": "https://customer-app.com/webhook",
  "events": ["order.completed", "subscription.delivered"],
  "secret": "whsec_xxx"  # For HMAC signature verification
}

# Payload delivered to webhook:
{
  "event": "order.completed",
  "order_id": "ord_xyz",
  "service": "ICP_LEAD_LIST_SE",
  "records": 3200,
  "confidence": 0.92,
  "data_url": "https://0pt.app/api/v1/orders/ord_xyz/data",
  "expires_at": "2026-07-24T00:00:00Z",
  "timestamp": "2026-06-24T15:30:00Z"
}
```

---

## Custom API Integration

For customers who want 0pt.app data in their own app:

```python
# Customer uses their API key to pull data programmatically
import requests

headers = {"Authorization": f"Bearer {API_KEY}"}

# Get latest delivery
resp = requests.get("https://0pt.app/api/v1/subscriptions/sub_abc/data", headers=headers)
data = resp.json()

# Pull into their app
for record in data["records"]:
    customer_app.upsert_lead(record)
```

---

## Zapier / Make (No-Code)

0pt.app provides a Zapier app for no-code integrations:

```
Triggers:
  - New Order Completed → trigger Zapier workflow
  - New Subscription Delivery → trigger on schedule

Actions:
  - Create Order → programmatically create orders
  - Get Order Data → pull data into any app

Example Zaps:
  Order Completed → Add to Google Sheet
  Order Completed → Create HubSpot Contacts
  Subscription Delivery → Email Report to Team
  New Lead in CRM → Create 0pt.app Enrichment Order
```

---

## Internal Integration Map

```
0pt.app
  │
  ├── nordic-eu-data-platform (data engine)
  │     └── sources.yaml → adaptive router → extraction → processing → storage
  │
  ├── VehIQ
  │     └── Vehicle data input → Vehicle analytics output
  │
  ├── FiveCRM (via Data Loader OS)
  │     └── Company + contact data → CRM
  │
  ├── siax.io
  │     └── Content + landing pages → traffic → 0pt.app orders
  │
  ├── Stripe
  │     └── Payment processing + subscription billing
  │
  ├── Fortnox
  │     └── Swedish accounting (invoices, bookkeeping)
  │
  ├── Resend / SendGrid
  │     └── Transactional emails
  │
  └── PostHog
        └── Product analytics + customer behavior
```

---

## Supported Output Formats

| Format | Use Case | Best For |
|---|---|---|
| **CSV** | Universal import | CRM, Excel, Google Sheets, BI tools |
| **JSON** | API consumption | Developer integrations, webhooks |
| **Parquet** | Big data | Data lakes, Spark, BigQuery, Fabric |
| **Excel (.xlsx)** | Business users | Manual review, presentations |
| **SQL Dump** | Database import | Direct DB-to-DB transfer |
| **API (JSON streaming)** | Real-time access | Applications, dashboards |

---

Next: See [Roadmap](roadmap.md) for development phases.
