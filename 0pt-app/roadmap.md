# 0pt.app — Development Roadmap

> **Build approach:** One phase at a time. Each phase delivers value independently. No big-bang launch.

---

## Phase 0: MVP — Core Self-Service (Vecka 1-4)

**Goal:** First paying customer can order and receive data.

### Deliverables
- [ ] 0pt.app landing page (sia.io design system, svensk text)
- [ ] Service catalog (A+B categories: scraping + structuring, ~30 tjänster)
- [ ] AI-assisted order wizard (natural language → service)
- [ ] Price estimation engine
- [ ] Stripe payment integration
- [ ] Order queue + job execution (via nordic-eu-data-platform)
- [ ] Automated delivery (download link + email notification)
- [ ] Customer dashboard (my orders, downloads)
- [ ] Admin dashboard (monitor jobs, customers)

### Services Live at MVP
| # | Tjänster |
|---|---|
| 5 | Web scraping (single, bulk, JS, custom) |
| 3 | PDF/OCR processing |
| 3 | Company databases (SE, NO, DK) |
| 2 | ICP lead lists (SE, Nordic) |
| 2 | Vehicle data (SE lookup, fleet analysis) |
| 1 | Market analysis report |
| 2 | Subscription (weekly updates, lead feed) |

**Target:** 10 paying customers, 50K+ SEK revenue in month 1.

---

## Phase 1: Expand Catalog + AI (Vecka 5-8)

**Goal:** Full Nordic coverage + AI-powered services.

### Deliverables
- [ ] Full Nordic company databases (SE+NO+DK+FI+IS)
- [ ] Expand to 100+ services across all categories
- [ ] AI assistant with Swedish+English NLP (Ollama-powered)
- [ ] Customer accounts + credits system
- [ ] API access for subscribers
- [ ] Webhook delivery
- [ ] Google Sheets integration
- [ ] FiveCRM direct export
- [ ] Quality dashboard (confidence scores visible to customer)

### New Services
| # | Tjänster |
|---|---|
| 5 | Advanced scraping (CF bypass, login-gated, stateful portal) |
| 5 | Full OCR pipeline (handwriting, tables, multi-language) |
| 5 | NER + enrichment services |
| 5 | ICP/Lead Gen (buying committees, signal-based) |
| 3 | ML services (classification, clustering, NLP) |
| 3 | BI dashboards |

**Target:** 30 paying customers, 200K+ SEK monthly recurring revenue.

---

## Phase 2: European Scale (Vecka 9-16)

**Goal:** Full EU coverage, enterprise features.

### Deliverables
- [ ] All 20 EU markets live in sources.yaml → product catalog
- [ ] vehicle data expanded to NL+FI+DE+UK
- [ ] Multi-language UI (SV, EN, DE, FR)
- [ ] Enterprise subscription tier (SLA, dedicated support)
- [ ] White-label option
- [ ] Zapier/Make integration
- [ ] Team accounts (multi-user, roles, budgets)
- [ ] Advanced analytics dashboard (customer-facing)
- [ ] Automated QA with confidence thresholds

### New Services
| # | Tjänster |
|---|---|
| 10 | EU company databases (DE, FR, NL, BE, AT, IT, ES, PL, UK, IE) |
| 5 | Cross-border datasets (Nordic+EU packs) |
| 3 | Vehicle data packs (EU markets) |
| 5 | Financial data services |
| 5 | Custom ML/AI projects |
| 5 | Managed services (fractional CDO, data strategy) |

**Target:** 100+ paying customers, 500K+ SEK MRR.

---

## Phase 3: Platform & Ecosystem (Vecka 17-24)

**Goal:** 0pt.app as the definitive European data marketplace.

### Deliverables
- [ ] Developer API (public, documented, rate-limited)
- [ ] Partner program (resellers, agencies)
- [ ] App marketplace (third-party integrations)
- [ ] Real-time data streaming (WebSocket/Kafka)
- [ ] Advanced AI: auto-detect customer needs from behavior
- [ ] Automated data freshness SLAs with penalties
- [ ] Compliance dashboard (GDPR, NIS2 audit trail)
- [ ] Multi-cloud deployment (AWS/Azure/GCP options)
- [ ] Data provenance blockchain (optional, for regulated industries)

**Target:** 500+ customers, 2M+ SEK MRR. The "Apollo of Europe" — but honest.

---

## Timeline Overview

```
Month 1     Month 2     Month 3     Month 4     Month 5     Month 6
├───────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│ Phase 0   │ Phase 1                 │ Phase 2                           │
│ (MVP)     │ (Nordic + AI)          │ (EU Scale)                        │
│           │                        │                                   │
│ 10 cust.  │ 30 cust.              │ 100+ cust.                        │
│ 50K SEK   │ 200K SEK/mån          │ 500K+ SEK/mån                     │
└───────────┴────────────────────────┴───────────────────────────────────┘
```

---

## Immediate Next Actions

1. **Stand up 0pt.app landing page** on siax.io subdomain or 0pt.app domain
2. **Wireframe order wizard** — the core UX differentiator
3. **Connect nordic-eu-data-platform** as the backend engine
4. **Launch with 15 services** — the highest-demand, lowest-complexity ones
5. **Get first 3 customers** — SIAX internal + 2 external bilhandlare
6. **Iterate based on real usage** — what do people actually order?

---

Next: See [SIAX Ecosystem Integration](siax-ecosystem.md) for how 0pt.app fits into the broader SIAX offering.
