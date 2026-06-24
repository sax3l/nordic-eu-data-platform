# 0pt.app — Pricing Model

> **Principles:** Transparent, pay-per-use, no hidden fees, volume discounts, subscription options.
> All prices in SEK (incl. moms for B2C, ex. moms for B2B).

---

## Pricing Strategies

### 1. Pay-Per-Job (One-Time)

Majoriteten av tjänsterna. Kunden betalar per jobb. Pris baseras på:
- **Data volume** (antal records, sidor, dokument)
- **Method complexity** (enkel API → avancerad stealth scraping)
- **Processing required** (bara hämta → OCR + NER + enrichment)
- **Urgency** (standard 24-48h → express 4h)

| Complexity Tier | Beskrivning | Prisfaktor |
|---|---|---|
| **Tier 1 (Simple)** | Öppet API, statisk HTML, inget anti-bot | 1.0x baspris |
| **Tier 2 (Medium)** | JS-rendering, soft CF, enstaka login | 1.5x baspris |
| **Tier 3 (Complex)** | Aggressiv WAF, multi-step portal, OCR krävs | 3.0x baspris |
| **Tier 4 (Enterprise)** | Skalad infrastruktur, dedikerad worker, SLA | 5.0x+ baspris |

### 2. Subscription (Monthly)

För löpande behov. Fast månadskostnad med inkluderad volym. Överskjutande → pay-per-use.

| Nivå | Pris/mån | Inkluderat | Överskjutande |
|---|---|---|---|
| **Starter** | 499 kr | 1 dataset, 1 uppdatering/mån | Per jobb |
| **Growth** | 1 995 kr | 5 dataset, veckovis uppdatering, 10K records/mån | 0.25 kr/record |
| **Business** | 4 995 kr | 15 dataset, daglig uppdatering, 50K records/mån, API-åtkomst | 0.15 kr/record |
| **Enterprise** | 14 995 kr | Obegränsat dataset, real-time, 250K records/mån, SLA, dedikerad support | 0.10 kr/record |
| **Custom** | Offert | Skräddarsytt efter behov | Förhandlat |

### 3. Volume Pricing (Records)

För dataset-köp. Pris per 1 000 records, avtagande med volym.

| Volym | Pris/1 000 records (enkla) | Pris/1 000 records (enriched) |
|---|---|---|
| 1-10K | 199 kr | 499 kr |
| 10-100K | 149 kr | 399 kr |
| 100K-1M | 99 kr | 299 kr |
| 1M+ | 69 kr | 199 kr |

### 4. Credits System

För återkommande kunder. Köp krediter i förväg → använd för valfri tjänst.

| Kreditpaket | Pris | Krediter | Bonus |
|---|---|---|---|
| **Micro** | 1 000 kr | 1 000 | 0% |
| **Small** | 5 000 kr | 5 500 | 10% |
| **Medium** | 10 000 kr | 12 000 | 20% |
| **Large** | 25 000 kr | 32 500 | 30% |
| **XL** | 50 000 kr | 70 000 | 40% |

---

## Price Estimation Algorithm

```python
def estimate_price(service_id: str, params: dict) -> dict:
    """
    Estimate price for a service before the customer commits.
    Returns a range, not an exact number (locks in at order time).
    """
    service = CATALOG[service_id]

    # 1. Base price from catalog
    base = service["base_price"]

    # 2. Volume factor
    records = params.get("estimated_records", 1000)
    if records > 1_000_000:
        volume_factor = 0.4
    elif records > 100_000:
        volume_factor = 0.6
    elif records > 10_000:
        volume_factor = 0.8
    else:
        volume_factor = 1.0

    # 3. Complexity factor (from sources.yaml)
    complexity = estimate_complexity(service_id, params)
    # Complexity = 1.0 (simple API) to 5.0 (CF-bypass + OCR + multi-step)

    # 4. Urgency factor
    urgency = params.get("urgency", "standard")
    urgency_factor = {"standard": 1.0, "priority": 1.5, "express": 2.5}[urgency]

    # 5. Processing depth
    processing = params.get("processing", "raw")
    # raw = 1.0, structured = 1.5, enriched = 2.0, verified = 3.0

    # Calculate
    estimated = base * volume_factor * complexity * urgency_factor

    return {
        "estimated_cost_low": round(estimated * 0.8),
        "estimated_cost_high": round(estimated * 1.2),
        "estimated_time_hours": estimate_time(service_id, records, complexity),
        "estimated_records": records,
        "confidence_tier": estimate_confidence_tier(service_id, params),
        "breakdown": {
            "base": base,
            "volume_discount": f"{int((1-volume_factor)*100)}%",
            "complexity_multiplier": complexity,
            "urgency_multiplier": urgency_factor,
        }
    }
```

---

## Example Prices (vanliga tjänster)

| Tjänst | Volym | Standard | Prioritet | Express |
|---|---|---|---|---|
| **ICP Lead List SE** | 5 000 leads | 2 995 kr | 4 495 kr | 7 495 kr |
| **Swedish Company DB** | 1.2M bolag | 4 995 kr | 7 495 kr | 12 495 kr |
| **Nordic Company Pack** | 3.5M bolag | 11 995 kr | 17 995 kr | 29 995 kr |
| **Single Site Scrape** | 1 URL | 49 kr | 75 kr | 125 kr |
| **PDF → Data (100 st)** | 100 PDF:er | 1 995 kr | 2 995 kr | 4 995 kr |
| **Vehicle Fleet Analysis** | 1 bolag | 1 495 kr | 2 245 kr | 3 745 kr |
| **Market Analysis Report** | 1 bransch | 9 995 kr | 14 995 kr | 24 995 kr |
| **ML Model Training** | 1 modell | 9 995 kr | 14 995 kr | 24 995 kr |
| **BI Dashboard** | 1 dashboard | 14 995 kr | 22 495 kr | 37 495 kr |
| **Lead Feed (Daily)** | Löpande | 2 995 kr/mån | — | — |

---

## Payment Flow

```
1. Customer selects service → estimate shown
2. Customer approves → Stripe Checkout / invoice
3. Payment captured → order queued
4. Job runs → QA → delivery
5. For subscriptions: Stripe recurring billing
6. Invoices sent automatically (Fortnox integration for Swedish accounting)
```

---

## Refund Policy

| Situation | Policy |
|---|---|
| **Data not delivered** | Full refund |
| **Confidence < promised tier** | 50% refund + free re-run |
| **Confidence < 50%** | Full refund |
| **Delivery late (>2x estimated)** | 25% discount on next order |
| **Customer changes mind (pre-execution)** | Full refund |
| **Customer changes mind (post-execution)** | No refund (data already collected) |

---

## Competitive Pricing Comparison

| Tjänst | Apollo | Cognism | 0pt.app | Besparing |
|---|---|---|---|---|
| Lead list, 1 000 kontakter | $49 (incl. i månad) | $200+ | 499 kr | ~60-80% |
| Export, 10 000 kontakter | $99 (credit cost) | $500+ | 1 995 kr | ~50-70% |
| API access, monthly | $450 | $2 000 | 2 995 kr | ~50-85% |
| Custom dataset | Offerteras ej | $10 000+ | 4 995 kr | ~50-90% |
| Nordic coverage | Dålig | Medium | Bäst | — |

---

Next: See [Order Flow & API](order-flow.md) for the complete order lifecycle.
