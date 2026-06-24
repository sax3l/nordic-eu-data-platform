# Compliance posture & hard limits

> Read this before writing a single scraper. It is what keeps the platform sellable in the EU — and what keeps you out of court. The whole competitive thesis is *honest, lawful, provenance‑tracked data*. That advantage evaporates the moment the pipeline is built on data we have no right to use.

## Source tiers

| Tier | What | Posture |
|---|---|---|
| **T1 — Primary official** | Government registries, open‑data portals, official APIs (Bolagsverket, brreg, Companies House, SIRENE, GLEIF…) | ✅ Preferred. Use to the maximum. Mostly free/open, designed for reuse. |
| **T2 — Aggregators** | North Data, Pappers, OpenCorporates, Atoka… | ✅ Use within each provider's API ToS / licence. |
| **T3 — Public directories** | hitta, eniro, proff… | ⚠️ Public but personal data → GDPR lawful‑basis + suppression. Respect rate limits / robots. |
| **T4 — Open web** | Company websites, public LinkedIn profiles surfaced via search | ⚠️ Elevated. robots.txt + rate limits; LinkedIn gated (below). |
| **T5 — Benchmark** | Competitor ICP tools (Apollo, ZoomInfo, Cognism…) | 🚫 **Benchmark/feature‑intel only — see below.** |

## The hard lines (non‑negotiable)

1. **Do not exfiltrate competitors' databases.** Using OCR or UI‑automation to bulk‑extract contacts out of Apollo / ZoomInfo / Cognism / Lusha / Seamless behind their login is a breach of their ToS, likely an access‑control circumvention, and misappropriation of data they themselves licence. It also imports *their* errors and their consent problems into our "honest" product — destroying the entire value proposition. **We build coverage from primary sources, not by laundering a competitor's database.**

   *What we DO with competitor tools (T5, legitimate):*
   - **Feature / pricing intelligence** — profile each tool (see `catalog/icp-tools/`).
   - **Coverage benchmarking** — run a small, ToS‑permitted sample of *our own* known accounts through their free/trial tier to measure *their* accuracy vs ours. Sampling for measurement ≠ bulk harvesting.
   - **Use their official APIs** only for data we are licensed to receive (e.g. enriching *our* CRM under our own paid seat), never re‑sold.

2. **LinkedIn:** only public data surfaced via general search engines. Never automate a logged‑in session, never solve LinkedIn's auth challenges, never scrape connections/messages. This tier is **off by default** and requires explicit operator sign‑off per campaign.

3. **Vehicle + personal data:** national vehicle registries are heavily regulated. Individual‑level / owner data is permission‑gated in most markets — use the *open/aggregate* vehicle datasets (e.g. NL RDW, FI Traficom) and gated lookup APIs (UK DVLA VES) within their stated purpose. No bulk owner‑PII harvesting.

4. **GDPR by design (all personal data):**
   - Tag every personal‑data field with **source, lawful basis, and last‑verified timestamp**.
   - Maintain **per‑country suppression / DNC** lists; honour Art. 21 objections and Art. 14 notification where required.
   - Implement **right‑to‑erasure** plumbing from day one (a person → delete across all sources).
   - DE/FR are stricter on B2B contact data than SE/UK — encode per‑jurisdiction rules in the fusion layer.

5. **Respect technical signals:** robots.txt, rate limits, and `429`/`Retry‑After`. The adaptive limiter slows down on these — it never treats them as obstacles to brute through.

## Why this is also the *winning* strategy

The incumbents' weakness (see `docs/competitive/`) is exactly accuracy + consent provenance. A platform that can show, per field, *where it came from and that it's lawful* is the only durable EU moat. Compliance here is not a tax — it is the product.
