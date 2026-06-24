# 0pt.app — SIAX Technology AB Data Service Platform

> **Domain:** 0pt.app | **Parent:** siax.io | **Status:** Planning & Design
> SIAX Technology AB:s marknadsplats för datatjänster — beställ allt från enkel dataskrapning till kompletta ML-projekt.

---

## Vision

0pt.app blir Nordens och Europas mest flexibla, kraftfulla och GDPR-nativa data service-plattform. Kunder beställer datatjänster lika enkelt som de beställer mat — via ett självbetjäningsgränssnitt med AI-driven rekommendation, direkt prissättning, och full transparens i leverans.

**Kärnprinciper:**
1. **Lokalt/Gratis-first** — All teknologi körs lokalt med öppen källkod. Noll API-kostnader för core extraction.
2. **Honest Accuracy** — Vi lovar inte 97% och levererar 65%. Vi publicerar faktisk confidence per fält.
3. **GDPR-native** — Varje datapunkt har provenance, källa, och laglig grund dokumenterad.
4. **Adaptive** — Plattformen känner av vilken metod som fungerar och byter automatiskt.
5. **SIAX Ecosystem** — Byggd på nordic-eu-data-platform, integrerad med siax.io, VehIQ, Protosell/FiveCRM.

---

## Competitive Positioning

| | Apollo | Cognism | ZoomInfo | 0pt.app |
|---|---|---|---|---|
| **Pris (månad)** | $450 | $2K-4K | $15K+ år | 500-5000 SEK |
| **Accuracy (real)** | 62-70% | 65-75% | 70-80% | 85-95% (provenanced) |
| **GDPR-native** | Nej | Delvis | Nej | **Ja** |
| **Nordic coverage** | Svag | Medium | Svag | **Bäst i världen** |
| **Vehicle data** | Nej | Nej | Nej | **Ja** |
| **Custom scraping** | Nej | Nej | Nej | **Ja** |
| **Lokal data** | Nej | Nej | Nej | **Ja** |
| **Self-service** | Ja | Nej | Nej | **Ja** |
| **Öppen prismodell** | Nej | Nej | Nej | **Ja** |

**Unfair advantage:** Vi har nordic-eu-data-platform (CloakBrowser, Unstructured, Ollama, adaptive router, 20 länders register). Ingen annan aktör har denna infrastruktur + proveniensmodell + lokala körning.

---

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│  Kund                                   0pt.app                  │
│  ┌────────┐                            ┌──────────────────┐     │
│  │ Beställ │ ──► "Jag vill ha alla     │ AI-assistent     │     │
│  │ på      │     svenska IT-bolag      │ förstår svenska  │     │
│  │ svenska │     10-50 anställda       │ + engelska       │     │
│  └────────┘     med beslutsfattare"    └────────┬─────────┘     │
│                                                 │               │
│                                          ┌──────▼──────────┐    │
│                                          │ Rekommenderar:  │    │
│                                          │ "ICP Lead List  │    │
│                                          │  SE, ~3 200 bolag│   │
│                                          │  ~9 500 kontakter│   │
│                                          │  Est. 4h, 895 kr│   │
│                                          └──────┬──────────┘    │
│                                                 │               │
│  ┌────────┐                            ┌──────▼──────────┐    │
│  │Betala  │ ◄── 895 kr ◄────────────── │ Beställ         │    │
│  └────────┘                            └──────┬──────────┘    │
│                                                 │               │
│                                          ┌──────▼──────────┐    │
│                                          │ Jobb i kö:      │    │
│                                          │ ████████░░ 73%  │    │
│                                          └──────┬──────────┘    │
│                                                 │               │
│  ┌────────┐                            ┌──────▼──────────┐    │
│  │Ladda   │ ◄── CSV/JSON ◄──────────── │ Klart!          │    │
│  │ner data │                            │ Confidence: 92% │    │
│  └────────┘                            └──────────────────┘    │
│                                                                  │
│  ┌────────┐                                                     │
│  │API-    │ ◄── Webhook dagligen ◄─── Prenumerera               │
│  │nyckel  │     (nya leads)          (499 kr/mån)                │
│  └────────┘                                                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      nordic-eu-data-platform                      │
│  Adaptive Router → CloakBrowser → Unstructured → Ollama → Splink │
│  20 länders register · Proxy rotation · OCR · MCP servers        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Target Customers

| Segment | Smärta | 0pt.app-värde |
|---|---|---|
| **Bilhandlare** | Manuell datainsamling, inventory, prissättning | Vehicle Data-paket (redan 17 paket på siax.io) |
| **SaaS-bolag (B2B)** | Leads av låg kvalitet, dyra ICP-verktyg | ICP Lead Lists med 92%+ accuracy |
| **Rekrytering** | Manuell research av kandidater/bolag | Company + Contact enrichment |
| **Konsultbolag** | Lång tid att hitta rätt kontakter | Beslutsfattar-data med direktkontakt |
| **Finans/Investment** | Svårt få överblick över marknader | Finansiell data + marknadsanalys |
| **Myndigheter** | Stora mängder ostrukturerad data | OCR + strukturering av dokument |
| **E-handel** | Konkurrentbevakning manuell | Konkurrentanalys + prisbevakning |

---

## Integration med SIAX Ecosystem

```
siax.io (huvudsajt)
├── Content (blogg, guider, case studies)
├── Tjänstesidor (fractional CTO, RevOps, Dev, Automation)
├── Bilhandlarpaket (17 st, 45K-220K SEK)
├── VehIQ (vehicle intelligence)
└── 0pt.app ← NY: data service marketplace
       │
       ├── Powered by: nordic-eu-data-platform
       ├── Integrated with: VehIQ (fordonsdata)
       ├── Exports to: FiveCRM / Data Loader OS / Blikk
       └── Uses: Unstructured · Ollama · CloakBrowser · spaCy · Splink
```

---

## Key Differentiators

1. **Natural Language Ordering** — Beställ på svenska. "Jag vill ha alla IT-bolag i Göteborg med fler än 50 anställda, och deras VD:ars email."
2. **Pay-per-job** — Inga dyra årskontrakt. Betala per jobb. Prenumeration finns men tvingas inte.
3. **Confidence Score** — Varje datapunkt har en confidence-siffra. Du ser exakt hur säker datan är.
4. **Freshness Tracking** — Du ser när datan senast uppdaterades. "Denna email verifierades 2026-06-22."
5. **GDPR Safe by Design** — All data har dokumenterad laglig grund. Inga gråzoner.
6. **Local-First** — All processning sker lokalt. Dina data lämnar aldrig vår infrastruktur.
7. **Adaptive Methods** — Plattformen använder alltid billigaste metoden som fungerar. Du betalar inte för onödig infrastruktur.

---

## Technology Foundation

0pt.app är ett **tunt frontend-lager** ovanpå nordic-eu-data-platform. Ingen duplicering av logik.

```
0pt.app (Next.js + shadcn/ui + Vercel)
    │
    ├── REST API → Orchestrator (FastAPI)
    │       │
    │       ├── Adaptive Router (multi-armed bandit)
    │       ├── Crawlee Workers (browser scraping)
    │       ├── OCR Workers (PaddleOCR, Surya)
    │       ├── NER Pipeline (spaCy, GLiNER)
    │       ├── LLM Enrichment (Ollama, LM Studio)
    │       └── Fusion Engine (Splink, confidence scoring)
    │
    ├── Database (Postgres + pgvector)
    ├── Cache (Redis)
    ├── Queue (Redis / BullMQ)
    ├── Storage (Local / S3)
    └── Monitoring (Prometheus + Grafana)
```

---

Next: See [Product Catalog](product-catalog.md) for the complete 200+ service catalog.
