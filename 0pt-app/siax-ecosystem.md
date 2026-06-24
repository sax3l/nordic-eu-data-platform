# 0pt.app — SIAX Ecosystem Integration

> How 0pt.app fits into the broader SIAX Technology AB ecosystem.

---

## The SIAX Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SIAX Technology AB                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  siax.io (Huvudsajt)                                                     │
│  ├── Fractional CTO                                                      │
│  ├── RevOps & CRM                                                        │
│  ├── Development & Automation                                            │
│  ├── AI & ML                                                             │
│  ├── Bilhandlarpaket (17 st)                                             │
│  └── Content (blogg, guider, case studies)                               │
│                                                                          │
│  VehIQ (Fordonsintelligens)                                              │
│  ├── Vehicle Data & Inventory Intelligence                               │
│  ├── Market Analysis & Pricing                                           │
│  └── Dashboard & BI                                                      │
│                                                                          │
│  0pt.app (Data Service Marketplace) ← NY                                │
│  ├── Data Acquisition & Scraping                                         │
│  ├── Data Structuring & Parsing                                          │
│  ├── Datasets & Data Products                                            │
│  ├── ICP, Lead Gen & Sales Intelligence                                  │
│  ├── Market Analysis & BI                                                │
│  ├── ML / AI & Advanced Analytics                                        │
│  └── Document & Media Processing                                         │
│                                                                          │
│  Protosell (Internt)                                                     │
│  ├── FiveCRM (CRM-system)                                                │
│  ├── Data Loader OS                                                      │
│  ├── Blikk (tidrapportering)                                             │
│  └── Hogia (lön/ekonomi)                                                 │
│                                                                          │
│  nordic-eu-data-platform (Data Engine)                                   │
│  ├── Adaptive scraping (20 länder)                                       │
│  ├── CloakBrowser, Unstructured, Ollama, Splink                          │
│  └── sources.yaml, country-data/                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Cross-Sell Flows

### siax.io → 0pt.app

| siax.io-sida | 0pt.app-erbjudande |
|---|---|
| Fractional CTO | "Behöver du data för ett specifikt projekt? Beställ direkt på 0pt.app" |
| RevOps | "Saknar du bra leads? Få ICP-leads med 92% accuracy" |
| Bilhandlarpaket | "Vehicle Data-paketet inkluderar nu 0pt.app-feed" |
| Blogg: "Så bygger du en data-driven organisation" | CTA: "Beställ ditt första dataset" |
| Case studies | "Kunden använde 0pt.app för att..." |

### VehIQ → 0pt.app

| VehIQ-funktion | 0pt.app-data |
|---|---|
| Vehicle Inventory | Löpande scraping av Blocket/Bytbil/KVD |
| Market Pricing | Marknadsprisdata, försäljningsstatistik |
| Fleet Analysis | Bolagsägda fordon från Transportstyrelsen/RDW |
| Export/Import | Gränsöverskridande fordonsdata |

### 0pt.app → Protosell (Internt)

| 0pt.app-tjänst | Protosell-användning |
|---|---|
| ICP Lead Lists | Bättre leads till CSMs databasbeställningar |
| Company Databases | Datakvalitet i FiveCRM |
| Data Enrichment | Automatisk berikning av befintliga kontakter |
| Data Cleaning | Dedup och validering av CRM-data |
| Market Analysis | Underlag för kunddialoger |

---

## Revenue Synergies

### 1. Paketförsäljning (Bundles)

| Paket | Innehåll | Pris |
|---|---|---|
| **Bilhandlare Premium** | 1 bilhandlarpaket + 12 mån 0pt.app Vehicle Data-löpande | 120 000 kr/år |
| **RevOps Complete** | RevOps-tjänst + 0pt.app Lead Feed (daglig) | 14 995 kr/mån |
| **Data+Dev** | Utvecklingstjänst + 0pt.app Data API | Offereras |
| **Growth Stack** | Fractional CTO + 0pt.app Growth Subscription | 29 995 kr/mån |

### 2. Content → Order-funnel

```
Bloggartikel (sia.io)
  ↓
  "Vill du ha denna data för ditt bolag?"
  ↓
  0pt.app order wizard (förifylld med artikelns parametrar)
  ↓
  Betalning → Leverans
  ↓
  "Fler databehov? Utforska vår katalog"
```

### 3. Kund-case → Produkt

Varje kundprojekt på siax.io identifierar databehov → 0pt.app bygger tjänsten → nästa kund kan självbetjäna.

---

## Sales Playbook Integration

### För bilhandlare
1. **Discovery:** "Hur hanterar ni fordonsdata idag?"
2. **Pitch:** "Med VehIQ + 0pt.app får ni realtidsdata direkt"
3. **Demo:** Visa live vehicle data från deras konkurrenters lager
4. **Close:** Paketpris med implementation + löpande data

### För SaaS-bolag
1. **Discovery:** "Hur hittar ni nya kunder idag?"
2. **Pitch:** "0pt.app ger er ICP-leads med 92% accuracy, direkt i CRM"
3. **Demo:** Visa leadlista med deras faktiska målgrupp
4. **Close:** Månadsprenumeration med första månaden rabatterad

---

## Technical Integration Points

```
siax.io (Next.js, Vercel)
  └── 0pt.app routes:
      /0pt/*          → 0pt.app sub-app (samma Next.js-instans)
      /api/0pt/*      → 0pt.app API routes

  └── Shared components:
      - Design system (siax.io tokens)
      - Auth (samma användarkonton)
      - Navigation (enhetlig header/footer)
      - Analytics (PostHog)
```

---

## Content Strategy

### Bloggämnen (siax.io → 0pt.app-trafik)
1. "Så bygger du din egen ICP-lista (utan att betala 5 000 kr/mån)"
2. "Vad kostar ett dataset egentligen? Prismodeller för B2B-data"
3. "GDPR och B2B-data: Vad får du egentligen samla in?"
4. "Jämförelse: Apollo vs Cognism vs DIY — vad är bäst för svenska bolag?"
5. "5 sätt bilhandlare kan använda data för att öka marginalerna"
6. "Så strukturerar du 10 000 PDF:er automatiskt (OCR + AI)"
7. "Vad är egentligen 'data enrichment' och varför behöver du det?"

Varje artikel har CTA: "Testa 0pt.app — första datasetet 50% rabatt"

---

## Launch Checklist

- [ ] 0pt.app domän (0pt.app eller 0pt.siax.io)
- [ ] Landing page med servicekatalog
- [ ] 3 case studies (Protosell-internt + 2 bilhandlare)
- [ ] 5 bloggartiklar som leder till 0pt.app
- [ ] Stripe integration (betalning)
- [ ] 15 tjänster live (MVP-omfattning)
- [ ] Pricing page
- [ ] Order wizard (AI-assisted)
- [ ] Customer dashboard
- [ ] Admin dashboard
- [ ] Email-automation (welcome, order updates, delivery)
- [ ] Analytics (PostHog)
- [ ] Legal (terms of service, GDPR policy, DPA)

---

Next: See the complete [0pt.app README](README.md) for vision and architecture overview.
