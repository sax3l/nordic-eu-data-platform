# ICP tools — enrichment & intent batch

> Benchmark/feature intelligence only (Tier 5, see [`docs/COMPLIANCE.md`](../../docs/COMPLIANCE.md)). We profile these tools to copy what works and beat what doesn't. We do **not** bulk-extract their databases. The platform's edge is provenance-tracked, lawful, EU-first data — every weakness catalogued below is a place that edge bites.

This batch covers ten tools that sit *next to* the big contact databases (Apollo/Cognism/ZoomInfo, profiled in [`docs/competitive/`](../../docs/competitive/)) rather than competing head-on as one. They split into three jobs-to-be-done:

- **Enrichment / waterfall orchestration** — Clay, Surfe (multi-provider routers), Dropcontact (algorithmic, no database), UpLead, Adapt.io (own database).
- **Intent / ABM** — Bombora (co-op), 6sense, Demandbase (predictive + de-anonymisation).
- **Lookalike / ICP discovery** — Ocean.io (vector similarity), Datanyze (technographics).

The recurring lesson: none of them *own* clean European company truth. They rent it, infer it, or buy it — and it shows the moment you sample EU accounts.

---

## Clay

- **HQ / region:** New York, USA. Global.
- **Primary data sources:** It owns almost no data. Clay is a spreadsheet-shaped *orchestrator* that resells 150+ providers (Clearbit, People Data Labs, Hunter, Apollo, Dropcontact, etc.) via a credit marketplace, plus AI/HTTP enrichment columns and "waterfall" fallbacks.
- **Claimed coverage / accuracy:** No single number — coverage is whatever providers you stack. Pitches "comparable to going direct" because it negotiates volume discounts.
- **Independent accuracy:** Cleanlist's tested-on-real-lists review found waterfalls materially lift match rates vs any single source, but quality is bounded by the providers chosen — Clay can't beat its worst link.
- **Pricing:** Post-March-2026 restructure: Launch $185/mo (2,500 Data Credits + 15,000 Actions), Growth $495/mo (6,000 + 40,000). **Hidden cost:** a 5-provider waterfall bills all 5 lookups (~3 credits each ≈ 15 credits/contact); marketplace data is a second currency on top of Actions. Failed lookups are now free (a 2026 improvement).
- **API surface:** Full HTTP API + webhooks; built to *be* the integration layer (it calls everyone else's API).
- **EU/GDPR posture:** Inherits the posture of whatever provider you route to — i.e. no unified lawful basis. A compliance liability dressed as flexibility.
- **Biggest weakness:** Cost opacity and skill ceiling — power is real but the dual-credit model punishes naive waterfalls, and output is only as clean/lawful as the cheapest column.
- **WHAT WE LEARN:** Copy the **waterfall router** pattern and "don't charge for misses" — but beat Clay by making *our own primary-source layer the top of the waterfall* with per-field provenance, so the EU rows are clean before any paid provider is touched. Sources: [Salesmotion](https://salesmotion.io/blog/clay-pricing), [Landbase](https://www.landbase.com/blog/clay-pricing), [Cleanlist](https://www.cleanlist.ai/blog/clay-data-enrichment-review).

---

## Dropcontact

- **HQ / region:** Paris, France. EU-first.
- **Primary data sources:** **No database.** Proprietary algorithms generate and verify professional email patterns and company data in real time from public signals — nothing scraped or stored.
- **Claimed coverage / accuracy:** ~98% verified-email accuracy on standard corporate domains; markets itself as outperforming waterfalls on French/EU data.
- **Independent accuracy:** Honest in the small print — overall *match* rate is ~55–70% (their own 20,000-contact benchmark: 54.9% effective enrichment) because catch-all/non-standard domains can't be verified. But on France specifically, field tests show 87–94% enrichment with <2% bounce.
- **Pricing:** Transparent and cheap. ~€24/mo entry, Starter €79/mo, Growth ~€120/mo (~€96 annual). Credit-based, EU-billed.
- **API surface:** REST API + native Google Sheets / HubSpot / Pipedrive integrations.
- **EU/GDPR posture:** **Best-in-class.** No personal-data store, EU-only servers, and audited by the French CNIL with full source-code/server access. This is the gold standard we benchmark our own posture against.
- **Biggest weakness:** Lower raw coverage than database vendors (the price of being algorithmic + lawful), and it's email/company-centric — thin on phones and intent.
- **WHAT WE LEARN:** This is the closest competitor to *our* thesis. Copy the **"no stored PII, CNIL-audited, provenance is the product"** posture verbatim. Beat them on **coverage** by layering primary registry data (Bolagsverket/brreg/Companies House) under the same lawful, audited frame — algorithmic verification *plus* official-source breadth. Sources: [SyncGTM](https://syncgtm.com/blog/dropcontact-review), [Salesdorado](https://salesdorado.com/en/automation/review-dropcontact/), [Dropcontact benchmark](https://www.dropcontact.com/email-finder-benchmark).

---

## Surfe (ex-Leadjet)

- **HQ / region:** Paris, France (founded 2020, rebranded from Leadjet 2022).
- **Primary data sources:** A LinkedIn-Chrome-extension front-end over a 15+ provider waterfall (Apollo, RocketReach, Dropcontact, Hunter, People Data Labs), with ZeroBounce validation before write-to-CRM.
- **Claimed coverage / accuracy:** "Triple verification," find rates up to 93%.
- **Independent accuracy:** Users report ~90% average find rate on contact data — credible because it's a waterfall, not a single source; the LinkedIn context (you're on a real profile) sharpens the match key.
- **Pricing:** Transparent per-seat. Essential $39/user/mo (1,800 email + 600 mobile credits), Pro $79/user/mo (12,000 email + 1,200 mobile, AI lookalikes, API). 25% annual discount.
- **API surface:** API on Pro tier; deep native CRM sync (HubSpot, Salesforce, Pipedrive) is the actual product.
- **EU/GDPR posture:** EU-headquartered and CRM-resident (data flows into *your* CRM), but the underlying contacts inherit each provider's basis — same laundering problem as Clay, just nicer UX.
- **Biggest weakness:** Thin moat — it's a UX skin + ZeroBounce over the same providers everyone rents; defensibility is workflow stickiness, not data.
- **WHAT WE LEARN:** Copy the **"enrich at the point of context + write straight to CRM with validation already done"** loop — friction kills enrichment, and Surfe nails the last mile. Beat it by making the *data underneath* ours and lawful, not a rented waterfall. Sources: [SyncGTM](https://syncgtm.com/blog/surfe-review), [G2](https://www.g2.com/products/surfe/pricing), [EU-Startups](https://www.eu-startups.com/2022/10/paris-based-surfe-raises-e4-million-to-build-connected-workspace-for-revenue-teams-as-it-rebrands-from-leadjet/).

---

## Datanyze

- **HQ / region:** USA; a ZoomInfo subsidiary (acquired 2018). US-centric.
- **Primary data sources:** Originally a technographics crawler (what tech a company runs, scraped from websites); now a ZoomInfo-data-fed Chrome extension reading LinkedIn profiles. ~120M people / 84M emails / 63M direct dials.
- **Claimed coverage / accuracy:** Contractual 95% accuracy threshold with prorated refunds if data drops below it (after a 30-day cure).
- **Independent accuracy:** In head-to-head testing it returned verified emails for ~70% of contacts vs ZoomInfo's ~85% on the same list — i.e. the *budget* cut of ZoomInfo's database, not parity.
- **Pricing:** Cheapest in the batch. Nyze Lite $0 (90-day, 10 credits/mo, no card), Pro 1 $29/mo, Pro 2 $55/mo. Effective ~$0.24–0.36/credit.
- **API surface:** Minimal — a self-serve extension for individual reps, not a platform API.
- **EU/GDPR posture:** Weak. US-centric ZoomInfo lineage; not positioned for EU compliance.
- **Biggest weakness:** Strategically abandoned — a downscaled ZoomInfo upsell funnel with stale technographics and US-only depth.
- **WHAT WE LEARN:** The **accuracy refund guarantee** is a sharp trust signal cheap to copy and rare in EU tools — offering a contractual per-field accuracy SLA (which our provenance tags make *auditable*) would out-trust everyone here. The technographics origin is also a free signal layer worth rebuilding from open web. Sources: [AeroLeads](https://aeroleads.com/blog/datanyze-review-2026-how-it-compares-after-years-under-zoominfo/), [SyncGTM](https://www.syncgtm.com/blog/datanyze-review), [BookYourData](https://www.bookyourdata.com/blog/datanyze-pricing).

---

## Bombora

- **HQ / region:** New York, USA (founded 2014). Global intent.
- **Primary data sources:** The **Bombora Data Co-op** — a consent-based cooperative of 5,000+ B2B publisher sites sharing anonymised content-consumption data. 86% of co-op data is exclusive to Bombora. The "Company Surge" score spikes when many people at one company read about one topic in a week.
- **Claimed coverage / accuracy:** Largest consent-based intent network; weekly (premium: daily/real-time) refresh.
- **Independent accuracy:** A Brixon Group test put Company Surge at ~81% precision — meaning ~1 in 5 "surging" accounts has no real intent.
- **Pricing:** Quote-based, expensive. ~$25–30K/yr basic, $50–100K/yr enhanced, $100K+ full audience. **No contact data included** — you must pair a separate enrichment vendor.
- **API surface:** Data feeds/integrations into ABM and CRM platforms (it's an ingredient brand — embedded inside 6sense, Demandbase, etc.).
- **EU/GDPR posture:** Consent-based co-op is its compliance story, but it's account-level signal, not person data — GDPR exposure is lower by design.
- **Biggest weakness:** **Account-level only and noisy** — you learn a *company* is surging, never *who* (CTO vs an intern), and 19% of the signal is false. It's a topic heatmap, not a buyer.
- **WHAT WE LEARN:** The **co-op / data-sharing flywheel** (give signal, get exclusive signal) is the most defensible moat in the batch — exclusivity beats scale. We can't replicate a US publisher co-op, but a *Nordic/EU* consent co-op (or first-party engagement signal) would be a genuine moat. Beat Bombora on the "who" by tying any intent signal to a real, lawful contact. Sources: [Derrick](https://derrick-app.com/tools/bombora-pricing), [MarketBetter](https://marketbetter.ai/blog/bombora-review-2026/), [SyncGTM](https://syncgtm.com/blog/bombora-review).

---

## 6sense

- **HQ / region:** San Francisco, USA (founded 2013). Enterprise, global.
- **Primary data sources:** Predictive-AI ABM platform fusing first-party web activity (a tracking pixel that de-anonymises company-level visitors), third-party intent (Bombora + own network), firmographics and technographics into "in-market" account + buying-stage scores.
- **Claimed coverage / accuracy:** AI identifies in-market accounts "before they fill out a form"; strongest in tech/SaaS/financial-services where its network is dense.
- **Independent accuracy:** Users report 30–50% of "in-market" accounts never become real opportunities — the predictive layer over-calls intent.
- **Pricing:** Quote-based and steep. Median ~$55K/yr; Team $25–60K, Growth $75–180K, Enterprise $200–500K+. Anonymous-visitor de-anonymisation is the headline feature.
- **API surface:** Enterprise API + deep Salesforce/HubSpot/Marketo integrations; built to sit at the centre of an enterprise GTM stack.
- **EU/GDPR posture:** Company-level de-anonymisation is its dodge ("it's not a person"), but pixel-based visitor tracking is increasingly scrutinised under GDPR/ePrivacy in the EU.
- **Biggest weakness:** Expensive, heavy to implement, and the predictive "in-market" score is materially over-optimistic (30–50% phantom). You pay enterprise money for a probability.
- **WHAT WE LEARN:** **De-anonymising your own site traffic to the account level** is the highest-value, lowest-PII signal in the batch — copy it. Beat 6sense by being honest about confidence (show the score *and* its hit-rate) and by grounding the account in lawful EU contact data instead of a $200K black box. Sources: [MarketBetter](https://marketbetter.ai/blog/6sense-pricing-2026/), [Warmly](https://www.warmly.ai/p/blog/6sense-pricing), [SyncGTM](https://syncgtm.com/blog/6sense-review).

---

## Demandbase

- **HQ / region:** San Francisco, USA (founded 2006). Enterprise ABM.
- **Primary data sources:** Account intelligence fused from its own web/ad network, **third-party intent (notably Bombora)**, firmographics, technographics and account engagement history — plus a B2B advertising layer.
- **Claimed coverage / accuracy:** Full-funnel ABM (intelligence → targeting → advertising → measurement).
- **Independent accuracy:** No clean independent figure, but reviewers flag the core dependency: output quality is capped by *your* CRM hygiene — bad account hierarchies in, unreliable intelligence out.
- **Pricing:** Quote-based, enterprise. ~$24K/yr smallest, mid-market $43–65K, full ABM-advertising $100–200K+. Onboarding (~$29K) and add-on modules inflate the real number well past quote.
- **API surface:** Enterprise APIs + CRM/MAP integrations; an ABM advertising platform as much as a data tool.
- **EU/GDPR posture:** Company-level only — **no person-level de-anonymisation** (by design), which limits SDR personalisation but lowers PII exposure. Still leans on Bombora/third-party signal for compliance story.
- **Biggest weakness:** Garbage-in-garbage-out dependency on CRM quality, company-level-only identification (no "who"), and price that balloons with onboarding + modules.
- **WHAT WE LEARN:** Demandbase proves even a $65K incumbent is **only as good as the customer's underlying account data** — exactly the seam we exploit. If we supply *clean, hierarchy-correct, provenance-tracked* account data as the input layer, we make tools like this work better *or* replace their intelligence layer. Sell the foundation, not the dashboard. Sources: [MarketBetter](https://marketbetter.ai/blog/demandbase-review-2026/), [Vendr](https://www.vendr.com/marketplace/demandbase), [Salesmotion](https://salesmotion.io/blog/demandbase-pricing).

---

## Ocean.io

- **HQ / region:** Copenhagen, Denmark (founded 2017). EU-built.
- **Primary data sources:** A vectorised NLP model that reads company *websites*, embeds them mathematically, and returns ranked "lookalike" companies from its database — submit a customer URL, get similar firms. Account-discovery first, contact data second.
- **Claimed coverage / accuracy:** Lookalike search "with incredible accuracy"; GDPR-built, aimed at small EU teams with a defined ICP.
- **Independent accuracy:** Weak and the standout cautionary tale of the batch — 3.1/5 on G2, persistent data-quality complaints, and a Capterra reviewer reporting a **5% ICP match rate** vs 40–50% from rival tools. The contact data *underneath* the clever lookalike model is the failure point.
- **Pricing:** Credit-based; ~$59/mo Premium (annual), ~$109/mo Professional (annual). 1 credit per lookalike result, but costs compound when enriching the discovered accounts with contacts.
- **API surface:** Limited; primarily a self-serve web app for prospecting teams.
- **EU/GDPR posture:** Genuinely EU-built and GDPR-positioned — the right *posture*, undermined by the data quality.
- **Biggest weakness:** A great idea (vector lookalikes) sitting on a thin, error-prone European dataset — the model is only as good as the company graph beneath it, and theirs is weak.
- **WHAT WE LEARN:** **Vector/embedding lookalike search is a feature worth copying** and a strong wedge for ICP expansion. But Ocean.io is the proof that *the model is worthless without clean underlying data* — our primary-source company graph is exactly the asset that would make lookalike search actually land in the EU. Copy the feature, win on the foundation. Sources: [Prospeo](https://prospeo.io/s/oceanio-alternatives), [G2](https://www.g2.com/products/ocean-io/reviews), [EU-Startups](https://www.eu-startups.com/2022/01/copenhagen-based-ocean-io-picks-up-e6-million-and-sets-sights-on-stateside-expansion-of-its-ai-martech-platform/).

---

## UpLead

- **HQ / region:** USA. US-centric.
- **Primary data sources:** Own B2B database of 155M+ contacts with **real-time email verification at the point of lookup** (verify-on-reveal, not verify-in-storage), technographic filters across 16,000+ technologies, and basic Bombora intent on higher tiers.
- **Claimed coverage / accuracy:** Headline **95% email-accuracy guarantee** — credits refunded for bad data.
- **Independent accuracy:** Holds up better than most claims here — independent testing of 500 contacts showed ~96% deliverability / ~4.1% hard bounces, backing the 95% marketing. The verify-at-reveal model is why.
- **Pricing:** Transparent and published. Essentials $99/mo (170 credits; $74/mo annual), Plus $199/mo (400 credits; $149/mo annual), Professional $399/mo + custom. Credit = one revealed contact.
- **API surface:** REST API on the Professional plan for high-volume enrichment.
- **EU/GDPR posture:** Mixed/US-leaning. Notably hit a **$34,400 settlement with the California Privacy Protection Agency** (Delete Act registration failure, 2024) — a reminder that even "compliant" data vendors carry regulatory baggage. Weak EU story.
- **Biggest weakness:** US-centric coverage and depth; the 95% guarantee is real but applies to a database that thins out fast outside North America.
- **WHAT WE LEARN:** **Verify-at-the-moment-of-reveal + a real accuracy guarantee** is the single best trust mechanic in the enrichment batch — copy both. Beat UpLead on geography: the same verify-on-reveal discipline applied to *European* data (where they're weak and we're native) plus a published guarantee EU buyers can audit. Sources: [SyncGTM](https://syncgtm.com/blog/uplead-review), [Landbase](https://www.landbase.com/blog/uplead-pricing), [Prospeo](https://prospeo.io/s/uplead-email-finder).

---

## Adapt.io

- **HQ / region:** Coimbatore/Tamil Nadu, India (global workforce across NA/Asia/Europe).
- **Primary data sources:** Own B2B database (claims range 61M "high-quality" to 150M+ contacts / 30M companies, with marketing citing 250M+) surfaced via Lead Builder search, Prospector list-building, Email Finder, and a Chrome extension.
- **Claimed coverage / accuracy:** "Robust and highly accurate" 150M+ contact database.
- **Independent accuracy:** Inconsistent — a 2026 review notes contact accuracy "can vary, especially for phone numbers and emails," with some test batches clean and others 15%+ bounce. No verify-on-reveal discipline like UpLead.
- **Pricing:** Cheap, tiered, somewhat opaque. Free $0, Starter $49/mo (500 credits, 50 contacts/day), Basic $99/mo (1,000 email + 100 phone credits, CRM export). 20% annual discount. **Daily contact caps** are a hidden throttle reviewers flag as frustrating.
- **API surface:** API is **Custom-plan only**, with no published SLA/uptime data — effectively gated.
- **EU/GDPR posture:** Claims GDPR compliance with a removal process, but reviewers (and Cognism's vendor analysis) flag a lack of clarity. Weakest documented posture in the batch.
- **Biggest weakness:** Inconsistent accuracy + daily caps + gated API + murky GDPR = a budget database with no trust mechanic and no EU credibility.
- **WHAT WE LEARN:** Adapt.io is the **anti-pattern**: cheap data with no verification, no provenance, no published API, hand-wavy GDPR. It's the exact buyer that a transparent, EU-native, provenance-guaranteed platform converts on first comparison. Beat it simply by *showing your work*. Sources: [Prospeo](https://prospeo.io/s/adaptio-reviews), [BookYourData](https://www.bookyourdata.com/blog/adapt-io-pricing), [aishortcutlab](https://aishortcutlab.com/tools/adapt/review).

---

## What this batch teaches us

Three patterns repeat, and each points at the same opening. **First, almost nobody in this batch owns clean European company truth.** The enrichment tools (Clay, Surfe) are *routers* that rent the same dozen providers and launder their consent problems; the database tools (UpLead, Adapt.io, Datanyze) are US/India-centric and thin out across the EU; the intent tools (Bombora, 6sense, Demandbase) only ever resolve to an *account*, never a lawful person, and 19–50% of their "intent" is phantom. The one genuinely EU-native, provenance-first product — **Dropcontact** — deliberately sacrifices coverage to stay lawful and CNIL-audited, which is precisely the trade we're built to win by adding primary-source breadth *underneath* the same posture. **Second, the best trust mechanics are cheap to copy and rare:** verify-at-reveal (UpLead), contractual accuracy refunds (Datanyze, UpLead), and "don't bill for misses" (Clay 2026) — make all three auditable via per-field provenance and we out-trust the entire field. **Third, the most defensible assets are data flywheels, not features:** Bombora's exclusive co-op and 6sense's first-party de-anonymisation are the only real moats here — and a Nordic/EU consent co-op plus account-level site de-anonymisation, grounded in clean registry data, would replicate both lawfully. The throughline: copy their *features* (waterfall routing, lookalike vectors, intent scoring, CRM-point-of-context enrichment), but win on the *foundation* every one of them is missing — clean, lawful, provenance-tracked European data. Ocean.io is the cautionary proof: a brilliant lookalike model is worth nothing on a weak data graph. Our graph is the product; theirs is the gap.
