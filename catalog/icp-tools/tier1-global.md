# ICP tools — Tier 1 (global incumbents)

**Batch:** Apollo.io · ZoomInfo · Cognism · Lusha · Seamless.AI · Clearbit (Breeze Intelligence) · RocketReach · Hunter.io · LeadIQ · Kaspr
**Last refreshed:** 2026-06-24
**Compliance tier:** T5 (benchmark / feature-intel only — see [`docs/COMPLIANCE.md`](../../docs/COMPLIANCE.md)). We profile these for pricing/coverage/accuracy intelligence and design only ToS-permitted sampling of *our own* known accounts. We do **not** bulk-extract their databases.

## Why this catalog exists

Every profile below answers the same question from a builder's seat: *where does the data actually come from, what is the gap between the claimed accuracy and the measured accuracy, and where is the soft underbelly we can beat?* The recurring pattern across all ten is the same — a marketed accuracy number (91–98%) that collapses to 60–80% in independent testing, a credit-metered billing model that charges for misses as well as hits, and a US-centric database that thins out badly across the EU. That gap *is* the opening for a provenance-tracked, EU-first platform. This batch builds on the deeper Apollo/Cognism/LinkedIn teardown in [`docs/competitive/`](../../docs/competitive/).

A note on "accuracy": vendors quote **deliverability of emails they *did* return** (which can be 90%+) and call it "accuracy." The number a buyer actually feels is **coverage × validity** — how many of the contacts you searched for came back with a *correct* detail. That blended figure is what "INDEPENDENT real-world accuracy" reports below, and it is always far lower than the headline.

---

## 1. Apollo.io

- **HQ / region:** San Francisco, USA. ~70% US-weighted database; the default choice for US growth-stage SDR teams.
- **Primary data sources:** Public web + company sites (~35%), job-board/LinkedIn scraping (~25%), **contributor crowdsourcing** via the email-tracking Chrome extension (~20%), licensed lists (~15%), API partners (~5%). As of Dec 2025, Apollo defaults to **waterfall enrichment** — Apollo first, then third-party fallbacks — narrowing the difference between it and multi-source tools.
- **Claimed coverage / accuracy:** 275M+ contacts; "91–97% email accuracy."
- **Independent real-world accuracy:** ~65–80% email; deliverability clusters ~73% in third-party tests; phone 60–70% (algorithmic). Bounce rates of 15–35% are widely reported vs the ~5% industry norm — the root of its 2.9/5 Trustpilot vs 4.7/5 G2 split.
- **Pricing (real, incl. hidden credits):** Free ($0, 100 email credits/mo, 5 mobile, 250 emails/day cap); Basic ~$49, Professional ~$79, Organization ~$119 per user/mo. Email credits "unlimited" under fair-use; **mobile = 5–8 credits each, every CRM export = 1 export credit, credits do not roll over.** The cheap seat hides $10–20K/yr in credit overages for a 5-SDR team.
- **API surface:** Full REST (people/org search, match, enrich, bulk, sequences). Advanced API + higher rate limits gated to Organization tier — Professional throttles at enterprise volume.
- **EU/GDPR posture:** SOC 2 Type II; DPA available. Weakest of the batch on EU lawful-basis provenance — contributor-sourced data carries consent ambiguity.
- **Biggest weakness:** Billing surprises + bounce rates; international coverage drops to 60–65% in UK/EU and 40–50% APAC.
- **WHAT WE LEARN:** *Beat* — copy the all-in-one bundle and free tier that drove Apollo's PLG growth, but kill the overage trap and publish a flagged "verified vs candidate" field per contact. Apollo's own waterfall pivot proves single-source coverage is a dead end; we win by making provenance visible instead of laundering it.

## 2. ZoomInfo

- **HQ / region:** Vancouver, WA, USA. Enterprise standard; US-deep, EMEA-thin.
- **Primary data sources:** Web crawling at scale, the **contributory network** (users who connect email/calendar grant ZoomInfo their contacts), licensed B2B data, plus internal research teams and ML/NLP cross-referencing.
- **Claimed coverage / accuracy:** 100M+ companies / 260M+ professionals; multi-layer "verified" data.
- **Independent real-world accuracy:** ~80% email accuracy by ZoomInfo's own framing; EU coverage materially thinner outside the UK, with weak local firmographics.
- **Pricing (real):** Quote-only, annual, **3-seat minimum.** Professional from ~$14,995/yr (3 seats, 5,000 credits); Advanced ~$25–30K; Elite $40K+. **Median real contract ~$31,875/yr (Vendr, 1,313 deals); most teams land $30–60K.** Add-ons stack: seat overages $1.5–2.5K/user, credit overages $0.25–0.50, intent $5–15K/yr, **International Data Passport ~$10K/yr** just to unlock EU data.
- **API surface:** Robust enterprise REST + webhooks + native CRM/MAP connectors; gated to higher tiers and metered hard.
- **EU/GDPR posture:** Self-certified under EU-US Data Privacy Framework (post-Schrems II), TrustArc-validated, supports 8 European DNC lists, processes only business-contact data for EU subjects. Still places the controller burden squarely on the buyer.
- **Biggest weakness:** Cost + lock-in + the EU "passport" upsell; you pay enterprise money for ~80% email accuracy and second-rate European depth.
- **WHAT WE LEARN:** *Beat* — ZoomInfo's EU data is an expensive bolt-on to a US core. Our entire core *is* EU primary-source data, sold without a $10K passport. Match their intent/firmographic depth in-region and undercut the opaque $30K floor with transparent pricing.

## 3. Cognism

- **HQ / region:** London, UK. The EMEA compliance-first benchmark and the bar we must clear.
- **Primary data sources:** Public business registries (Companies House, Bolagsverket, etc. ~25%), press/announcements, company sites + LinkedIn, **proprietary human research**, news aggregation. **Diamond Data** = mobiles a human operator physically phone-verifies before publishing.
- **Claimed coverage / accuracy:** 400M+ contacts; "98% accuracy" — but that figure applies to **Diamond-verified phones only**, not the bulk DB.
- **Independent real-world accuracy:** ~90% email in EMEA (best in batch); Diamond phone ~87–98% but covers only a small verified slice (~2–3% of the DB); bulk data decays like everyone else's.
- **Pricing (real):** Quote-only. Procurement data: Standard ~$15K platform + ~$1.5K/user/yr; Pro ~$25K + ~$2.5K/user. "Unlimited" individual views on some tiers, but credit pools (~30–60K/yr) and **Diamond mobiles billed at 2–3× standard credits.**
- **API surface:** Enrichment + search API, but **narrower than Apollo/ZoomInfo** and a known limitation; built around the UI/CRM workflow, not developer-first.
- **EU/GDPR posture:** Strongest in batch — ISO 27001 + ISO 27701, GDPR-native, notified email + DNC screening. This is its primary moat and switching cost.
- **Biggest weakness:** The headline accuracy applies to a tiny verified subset; thin US/APAC phones; opaque "contact sales" pricing; no native outreach/sequencing.
- **WHAT WE LEARN:** *Beat* — match Cognism's compliance story (ISO 27701 + registry-sourced provenance) but expose it per-field and publish pricing. Cognism proves EU buyers pay a premium for "lawful + verified"; our edge is doing it transparently with a real API, since theirs is the weak point.

## 4. Lusha

- **HQ / region:** Tel Aviv, Israel. SMB-friendly, LinkedIn-native prospecting.
- **Primary data sources:** Community/contributor network (the Lusha extension), public web, licensed partners; emphasis on direct dials from its crowdsourced pool.
- **Claimed coverage / accuracy:** "98% email accuracy" / 85–86% phone.
- **Independent real-world accuracy:** A March-2026 test on 300 mid-market B2B contacts returned an email for only **31% of lookups** — though the emails it *did* return were ~89% deliverable. Independent blended email accuracy ~72–78%. Classic coverage-vs-validity gap.
- **Pricing (real, incl. credits):** Free (40 credits/mo, rollover to 80); Pro ~$49–70/user/mo (~7,200 credits/yr, 2 seats); Premium ~$300–400/mo (~40,800 credits/yr, 5 seats); 5+ users = custom. **Phone reveals quietly doubled from 5 → 10 credits in 2026** (5 via API) — the headline "1 credit = 1 email" hides the real phone cost.
- **API surface:** REST enrichment + bulk + person/company lookup; reasonable but credit-metered.
- **EU/GDPR posture:** GDPR, CCPA, SOC 2, **ISO 27701** across all tiers incl. Free — genuinely strong for an SMB tool.
- **Biggest weakness:** Low coverage (the 31% return) means you burn seats hunting; the 2026 phone-credit doubling erodes trust.
- **WHAT WE LEARN:** *Beat* — Lusha's credibility lever is ISO 27701 even on Free. Match that compliance floor, then crush it on coverage: a 31% return rate is the single most beatable number in this batch. Lead with "we return a contact for X% of your list," not a deliverability vanity metric.

## 5. Seamless.AI

- **HQ / region:** Columbus, OH, USA. "Real-time AI search engine for leads."
- **Primary data sources:** Live web crawling / AI search at query time rather than a static DB snapshot; aggregates public web + scraped signals on demand.
- **Claimed coverage / accuracy:** "98% email accuracy"; positions real-time search as fresher than databases.
- **Independent real-world accuracy:** Users report **20–30% bounce rates** (best case ~15%); email ~60–75%, **phone ~45–60%** — among the worst in batch. The real-time engine returns stale/personal/disconnected data and still charges for it.
- **Pricing (real):** Free (1,000 credits/user/yr). Pro/Enterprise unpublished, ~$79–150/user/mo, **annual-only, paid upfront, 12-month lock.** Fully-featured setups run 40–60% over base license. **Credits are deducted per *attempt*, including lookups that return nothing** — 20–40% of credits burn on dead results.
- **API surface:** API exists but secondary; the product is the UI + Chrome extension.
- **EU/GDPR posture:** Weak. US-centric, real-time scraping model with little EU provenance story; worst fit for European compliance buyers.
- **Biggest weakness:** **Reputation** — the worst cancellation/auto-renewal complaints in B2B sales tooling, plus accuracy at the bottom of the batch.
- **WHAT WE LEARN:** *Beat* — Seamless is the cautionary tale: charge-for-misses billing + lock-in contracts = a churn time-bomb. We win on contrast: pay only for *verified hits*, month-to-month, cancel anytime. Their billing model is a gift to anyone offering honest metering.

## 6. Clearbit (Breeze Intelligence)

- **HQ / region:** USA — acquired by HubSpot (late 2023), rebranded **Breeze Intelligence**. No longer a standalone product.
- **Primary data sources:** Web crawling, logo/firmographic enrichment heritage, IP-to-company reverse lookup, now fused into the HubSpot data graph.
- **Claimed coverage / accuracy:** Historically strong firmographic/technographic enrichment (less a contact-finder, more a record-enricher).
- **Independent real-world accuracy:** Best-in-class for *company* enrichment and form-shortening; never a primary email/phone discovery tool.
- **Pricing (real):** **No standalone purchase.** Requires a paid HubSpot seat. Basic contact/company enrichment is free with Starter+ (since Fall 2025); advanced (Buyer Intent, Smart Properties) consumes **HubSpot Credits — 3,000/mo on Pro, 5,000/mo on Enterprise, overage $10/1,000, no rollover.**
- **API surface:** **Legacy Clearbit Enrichment/Prospector/Logo APIs deprecated** post-acquisition (Logo API shut Dec 2024). Access is now through HubSpot's platform, not a clean public API.
- **EU/GDPR posture:** Inherits HubSpot's compliance program; US-anchored.
- **Biggest weakness:** Strategic capture — Clearbit is now bait to keep you inside HubSpot. Free tools (TAM Calculator, Connect, Visitor Report) were **killed April 30, 2024**; no exit, no standalone API.
- **WHAT WE LEARN:** *Copy* — Clearbit's reverse-IP "anonymous visitor → company" and frictionless form-enrichment was its killer feature; replicate it as a standalone, portable enrichment API. The captured-API vacuum it left behind (no clean standalone enrichment endpoint) is a concrete market gap we can fill.

## 7. RocketReach

- **HQ / region:** USA. Broad, shallow lookup utility — one of the largest raw profile counts.
- **Primary data sources:** Web aggregation across public profiles, company sites, social — heavily **algorithmic** (pattern-inferred) rather than verified.
- **Claimed coverage / accuracy:** 700M+ profiles; "85–90% accuracy."
- **Independent real-world accuracy:** Returned emails for ~78% of tested contacts at ~91% validity → **~71% effective**; weaker than verified-data rivals because it leans algorithmic (SalesIntel benchmarked 95% vs RocketReach 85–90%).
- **Pricing (real):** Free = 5 lookups/mo. Essentials ~$329/yr ($27/mo), Pro ~$829/yr ($69/mo), Ultimate ~$1,699–2,099/yr ($142/mo). **"Unlimited lookups" is a trap — exports cap at 1,200 / 3,600 / 20,000 per year by tier.**
- **API surface:** Solid REST (lookup, search, bulk) but **full API gated to Ultimate+** — a real barrier for developers on lower tiers.
- **EU/GDPR posture:** DPA available; US-centric, algorithmic sourcing makes EU lawful-basis provenance thin.
- **Biggest weakness:** Algorithmic-not-verified data and the export cap that contradicts the "unlimited" marketing.
- **WHAT WE LEARN:** *Beat* — "unlimited lookups, capped exports" is a dishonest framing buyers resent. We offer honest export economics. Also: RocketReach's 700M is breadth without verification — proof that raw count is a weak moat we can out-position with depth + provenance.

## 8. Hunter.io

- **HQ / region:** France (EU-based — rare in this batch). Focused email-finder/verifier, developer-loved.
- **Primary data sources:** Crawls public web pages and indexes **email patterns per domain** (no contributor scraping of private inboxes) — a comparatively clean, transparent sourcing model.
- **Claimed coverage / accuracy:** Domain/pattern-based discovery; confidence-scored results.
- **Independent real-world accuracy:** ~91% valid rate on standard corporate domains in real testing (8/10 domains in reviews) — strong *for B2B corporate email*, narrower scope (no phones, no deep firmographics).
- **Pricing (real):** Free (€0, 25 searches + 50 verifications/mo, 1 mailbox); Starter €34–49/mo (500 searches, 3 mailboxes); Growth €104–129/mo (5K); Scale €209–259/mo (10K+). **Transparent credit logic** — 1 search credit = 1 email found; 0.5 credit = 1 verification; bulk domain search = up to 10 emails/credit. Annual saves ~30%.
- **API surface:** **Best developer DX in batch** — clean documented REST (domain search, email finder, verifier) + an official **Hunter MCP Server (2025)** that lets Claude/ChatGPT/Gemini call it in natural language out of the box.
- **EU/GDPR posture:** EU-headquartered, transparent pattern-based sourcing — the most defensible provenance story among the US tools.
- **Biggest weakness:** Narrow scope — email-only. No phones, weak firmographics, not a full prospecting platform.
- **WHAT WE LEARN:** *Copy* — Hunter's transparent confidence-scored credit logic and **MCP-first API** are exactly the developer-trust posture we want. As a fellow EU company with clean sourcing, it's the closest philosophical ally and the model for our enrichment API's DX. Beat it by adding the breadth (phones, firmographics, registry data) it deliberately lacks.

## 9. LeadIQ

- **HQ / region:** USA (Santa Clara) with strong APAC/SG roots. Capture-and-sync workflow tool — sits in the browser, pushes to CRM/sequencer.
- **Primary data sources:** Aggregated third-party data partners vetted by an in-house Data Operations team, surfaced via a LinkedIn/Sales-Nav capture extension.
- **Claimed coverage / accuracy:** Positioned on workflow + email reliability rather than raw DB size.
- **Independent real-world accuracy:** Email generally well-rated (low bounce); **phone is the dominant complaint** — mobiles/direct-dials repeatedly reported as outdated or "garbage," especially outside core markets.
- **Pricing (real):** Free (1 user, 50 credits); Pro from ~$75–200/user/mo by tier/volume; Enterprise custom. **Phone lookups cost up to 10× an email credit; credits do not roll over** — slow months forfeit spend.
- **API surface:** Enrichment API + native sync to Salesforce/HubSpot/Outreach/Salesloft; workflow-centric rather than a raw-data API.
- **EU/GDPR posture:** Per-supplier GDPR/CCPA review + in-house data-ops vetting; reasonable but supplier-dependent (not first-party-sourced).
- **Biggest weakness:** Phone quality and the 10× phone-credit economics; data is only as good as the partners it resells.
- **WHAT WE LEARN:** *Copy + Beat* — LeadIQ's **capture-to-CRM workflow** is genuinely sticky; replicate that frictionless "find → verify → sync" loop. Beat it on phone accuracy (its admitted weak spot) using EU-verified mobile sourcing, and drop the punitive 10× phone-credit model.

## 10. Kaspr

- **HQ / region:** Paris, France — **owned by Cognism.** A LinkedIn Chrome-extension phone/email revealer riding Cognism's EU data network; the affordable on-ramp to Cognism-grade EMEA data.
- **Primary data sources:** Cognism's EU data network + community/contributor data, surfaced contextually on LinkedIn profiles.
- **Claimed coverage / accuracy:** GDPR-aligned EU contact data on-demand from LinkedIn.
- **Independent real-world accuracy:** Phone ~50–65% (EU numbers more reliable than US); email ~75–80%. Decent for the price, below parent Cognism's Diamond tier.
- **Pricing (real):** Free (5 phone + 5 email credits/mo); Starter ~$49/mo (1,200 credits); Business ~$79/mo (2,400); Organization ~$99/mo (4,800). **Credits expire monthly, no rollover; bulk extraction needs LinkedIn Sales Navigator.**
- **API surface:** Thin — the product is the extension; programmatic access is minimal vs the others.
- **EU/GDPR posture:** GDPR + CCPA aligned via Cognism lineage — strong for European prospecting, a deliberate selling point.
- **Biggest weakness:** Total **LinkedIn dependency** (no platform of its own), no buying signals, no real API, moderate phone accuracy, monthly credit burn.
- **WHAT WE LEARN:** *Beat* — Kaspr proves there's demand for *cheap, GDPR-clean, EU phone data* delivered in-workflow — but it's shackled to LinkedIn and has no API. We deliver the same EU-compliant contact data **source-agnostic and API-first**, freeing buyers from the LinkedIn-session dependency (which also keeps us clear of LinkedIn ToS risk, per our compliance posture).

---

## What this batch teaches us

Three structural weaknesses repeat across all ten, and each is a wedge for an EU-first, provenance-tracked platform. **First, the accuracy gap is universal and self-inflicted** — every vendor markets 91–98% by quoting deliverability of *returned* emails, while the figure buyers feel (coverage × validity) lands at 60–80%, and Lusha's 31% return rate shows how wide that chasm gets. The move is to publish the honest blended number and flag every field "verified vs candidate"; honesty here is differentiation, not a liability. **Second, credit metering is adversarial** — Seamless charges for misses, Apollo/Lusha/LeadIQ price phones at 5–10× and expire unused credits, RocketReach caps the "unlimited," and ZoomInfo gates EU data behind a $10K passport. Transparent, pay-for-verified-hits, roll-over or month-to-month billing directly attacks the incumbents' most-complained-about behavior. **Third, the EU is everyone's soft spot** — the US giants (Apollo, ZoomInfo, Seamless, RocketReach) thin out badly in Europe, and the genuinely EU-strong players are exactly the compliance-first ones (Cognism, Kaspr, Lusha's ISO 27701, Hunter's clean French sourcing). That maps perfectly onto our thesis: build coverage from EU primary sources, carry ISO 27701 + per-field GDPR provenance as a *visible* product feature, and ship a Hunter-grade developer API (MCP-first) that Cognism, Kaspr and the enrichment-captured Clearbit all lack. Beat the US tools on European depth, beat the EU tools on API + pricing transparency, and beat all of them on the one thing none of them will show: where each data point came from and that it's lawful.

---

*Sources (pricing/accuracy grounding, 2026): Cleanlist, Salesmotion, MarketBetter, Cognism blog, SyncGTM, Prospeo, Vendr, Apollo/Hunter/Kaspr official pricing, Derrick, Enrich.so, G2 — accessed 2026-06-24 via web search. Apollo/Cognism baseline figures cross-referenced against the deeper teardown in [`docs/competitive/`](../../docs/competitive/). All figures are third-party estimates; vendor list prices and credit costs change frequently.*
