# ICP tools — EU / regional & email-finder batch

> Profiles of 12 ICP / sales-intelligence tools that crowd the European and email-finding niche: the EU firmographic + visitor-ID players (Dealfront, Vainu, Albacross), the US human-verified set (SalesIntel, Lead411), and the email-finder cluster (Wiza, Findymail, Prospeo, Anymailfinder, Skrapp, Snov.io, GetProspect).
>
> **Scope & compliance.** This is **T5 benchmark/feature intelligence only** (see [`docs/COMPLIANCE.md`](../../docs/COMPLIANCE.md)). We profile these tools for feature/pricing/coverage gaps and design *legitimate* benchmarking — running a small, ToS-permitted sample of **our own** known accounts through their free/trial tier to measure their accuracy vs ours. We do **not** bulk-extract their databases. Builds on the incumbent teardown at [`docs/competitive/`](../../docs/competitive/) (Apollo / Cognism / LinkedIn Sales Navigator).
>
> **Why these 12.** The big three (Apollo, Cognism, LinkedIn) own the headline market. This batch owns the *flanks* we actually compete in: Nordic/registry-grounded firmographics, GDPR-native EU positioning, and the cheap email-finder long tail that any SMB reaches for first. Their weaknesses map almost perfectly onto our moat — provenance-tracked, registry-first, lawful EU data.
>
> Last researched: 2026-06-24. Pricing/accuracy figures are cited and change fast — re-verify before quoting.

---

## A note on the numbers

Two patterns recur across this whole batch and you must read every profile through them:

1. **"Accuracy" is almost always *search success*, not *deliverability*.** A tool reporting "92% accuracy" usually means "we returned *an* email 92% of the time" — independent bounce-tested benchmarks routinely halve that. The honest cross-tool benchmark (5,000 same Sales-Navigator contacts) put *verified* match rates from **16.9% (Prospeo) to 77.5% (Anymailfinder)** — a 4.5× spread on identical input ([Anymailfinder benchmark](https://anymailfinder.com/blog/best-email-finder-tools-2025); [Prospeo benchmark](https://prospeo.io/s/best-email-finder-tools-2026)).
2. **The G2 ↔ Trustpilot gap is the tell.** Vainu is 4.6/5 on G2 and **2.1/5 on Trustpilot**; the pattern repeats everywhere. G2 captures incentivised/onboarding reviews; Trustpilot captures churned users hit by data rot and billing surprises.

---

## 1. Dealfront (Echobot + Leadfeeder)

- **HQ/region:** Karlsruhe/Helsinki (Germany + Finland). The 2022 merger of **Echobot** (DE firmographics/intent) + **Leadfeeder** (FI visitor ID) + Minttel. EU-native by design.
- **Primary data sources:** EU **trade registers**, public web crawlers, and **IP-to-company** resolution for website visitor ID. Every data point ships with source traceability — this is their pitch.
- **Claimed coverage / accuracy:** ~**26M** EU companies (+ ~8.5M rest-of-world) and 400M+ contacts across modules; "best-in-class" EU firmographics. Visitor-ID match rate claimed in the 30–40% of business traffic band.
- **Independent reality:** Visitor-ID resolution **~60–80%** for corporate-office IPs but only **20–40% of total B2B traffic** is identifiable at all — and GDPR cookie-consent shrinks the EU-traffic pool further than US tools admit ([SyncGTM](https://syncgtm.com/blog/leadfeeder-review)). US contact depth is thin.
- **Pricing (real):** Leadfeeder module **$99–1,199/mo** (by identified-companies tier); Platform from **$399/mo**; Target/Connect/Datacare/Promote are **custom-quoted, no public price** — that opacity *is* the hidden cost. Free Leadfeeder tier: 100 IDs/mo, 7-day retention ([SyncGTM](https://syncgtm.com/blog/dealfront-review)).
- **API surface:** Leadfeeder **read-only Web Visitors API** (bundled), plus JS site-tracking API. No rich firmographic write/enrich API at the cheap tier.
- **EU/GDPR posture:** **Strongest in the batch.** German-based, EU-only hosting, per-record source traceability, register-grounded. This is the one genuinely credible "GDPR-native" story here.
- **Biggest weakness:** Modular pricing opacity + weak non-EU coverage + the structural ceiling that GDPR consent caps how much EU traffic is even identifiable.
- **WHAT WE LEARN:** **Beat them on their own turf with transparency.** Their register-first + source-traceability story is exactly ours — but their pricing is "contact sales" maze. Publish per-field provenance *and* published prices and we out-honest the only competitor whose honesty is the pitch.

## 2. Vainu

- **HQ/region:** Helsinki, Finland. The Nordic firmographic specialist.
- **Primary data sources:** Direct **registry partnerships** — Bolagsverket (SE), PRH (FI), Brønnøysund (NO), Virk (DK), plus NL. ~700 data fields/company, real-time registry sync. Decision-maker data in FI/SE is **manually, human-verified**.
- **Claimed coverage / accuracy:** **5M+** Nordic companies, **9M+** Nordic contacts, 300+ API fields; positions as "most comprehensive Nordic database."
- **Independent reality:** Genuinely strong *inside* the Nordics (registry-grounded firmographics beat any scraper). **Outside Scandinavia + Benelux it collapses** — reviewers call the global data "yellow pages quality," Trustpilot notes data "sometimes totally off." **4.6/5 G2 vs 2.1/5 Trustpilot** ([Prospeo](https://prospeo.io/s/vainu-reviews); [SyncGTM](https://syncgtm.com/blog/vainu-review)).
- **Pricing (real):** Prospecting from **€3,500/yr** (~€292/mo); CRM from **€4,200/yr**; Global from **€12,000/yr**. No meaningful free tier.
- **API surface:** Strong **REST API**, 300+ fields, real-time company data — genuinely their best asset and the reason they're embedded in many Nordic CRMs.
- **EU/GDPR posture:** Good in FI/SE (human-verified, GDPR-collected decision-makers); thinner provenance elsewhere.
- **Biggest weakness:** **Pure geographic trap** — verified contact data exists *only* for FI/SE; no verified emails/direct-dials at all, so customers bolt on a second tool. Global = afterthought.
- **WHAT WE LEARN:** **This is our closest direct rival and our clearest opening.** Vainu proves registry-grounding wins the Nordics — then stops at the border and at firmographics. We extend the *same* registry rigor across the full EU **and** add the verified contact layer Vainu refuses to build, in one provenance-tracked product.

## 3. Albacross

- **HQ/region:** Stockholm, Sweden (founded ~2015). Website visitor-ID + ABM.
- **Primary data sources:** **IP-to-company** mapping over European registry data; **Bombora** integration for off-site intent. Company-level, not person-level.
- **Claimed coverage / accuracy:** 11,000+ customers; "strong European company data"; GDPR + CCPA compliant by architecture.
- **Independent reality:** Solid EU IP→company resolution and a clean dashboard, but accuracy **drops sharply outside the EU** and it is **company-level only** — no individual emails/phones ([SyncGTM](https://syncgtm.com/blog/albacross-review); [Warmly](https://www.warmly.ai/p/blog/albacross-pricing)).
- **Pricing (real):** Three published tiers, ~**€59/€149/€375 per mo** (annual); contact-data/API "Growth" tier is custom — real spend lands **$1k–15k+/yr**. Annual contracts only.
- **API surface:** API access gated to the higher/custom "Growth" tier.
- **EU/GDPR posture:** GDPR/CCPA-compliant, consent tracking built in; Swedish base. Reasonable but the data is company-level so less PII exposure to begin with.
- **Biggest weakness:** **Company-level ceiling** — tells you *which firm* visited, never *who*. Buyers must pair it with a contact-data tool, so it's a feature, not a platform.
- **WHAT WE LEARN:** Visitor-ID is a **lead-generating surface that funnels into enrichment** — the part Albacross can't do. If our platform resolves the visiting company *and* the buying-committee contacts (lawfully, registry-anchored), we collapse two purchases into one. Copy the clean single-purpose UX; beat the company-level dead-end.

## 4. SalesIntel

- **HQ/region:** USA (Virginia). Human-verified contact specialist.
- **Primary data sources:** **Human research team** re-verifies contacts on a rolling **~90-day** cycle (people actually call/email-check), supplemented by machine data and partner feeds. US-centric.
- **Claimed coverage / accuracy:** ~95% accuracy claim; **97% email deliverability** in case studies — the strongest verification story among the US set.
- **Independent reality:** Human re-verification genuinely helps deliverability, but the "**unlimited**" plan hides a **contractual ceiling of 3,000 companies/contacts per month** and **10 Research-on-Demand credits/user/month** ([LeadHaste](https://leadhaste.com/blog/salesintel-pricing-2026)). EU coverage is weak.
- **Pricing (real):** Per-seat "unlimited" framing, but Vendr's 20 real transactions show a **median ~$17,599/yr**, range **$8,670–$41,380** ([Vendr](https://www.vendr.com/marketplace/salesintel)). API enrichment is a higher-tier add-on.
- **API surface:** Enrichment API available only on higher tiers (add-on).
- **EU/GDPR posture:** Claims GDPR/CCPA alignment but US-first; EU is not the focus and provenance is weaker than the EU-native players.
- **Biggest weakness:** "Unlimited" is **marketing fiction** — hard monthly caps + thin EU data + premium price.
- **WHAT WE LEARN:** Human verification is the most *defensible* accuracy moat in the batch — but it doesn't scale and it's US-bound. We get the same trust signal **cheaply and at scale** by anchoring to authoritative EU registers (the verification is the *source*, not a call-centre), and we never write "unlimited" over a hidden cap — that breeds the Trustpilot backlash.

## 5. Lead411

- **HQ/region:** USA (Colorado). Verified data + bundled intent for SMB outbound.
- **Primary data sources:** Verified emails/direct-dials + **Bombora** intent bundled in; growth-trigger alerts (new hires, funding, IPOs, exec changes). Single-source (no waterfall fallback).
- **Claimed coverage / accuracy:** US email accuracy **~80–85%**, direct-dial **~60–70%** — and refreshingly, Lead411's own figures are close to independent ones.
- **Independent reality:** Honest accuracy, best-value **Bombora bundle** on the market, but **US-centric with thin international coverage** and only one intent signal type ([SyncGTM](https://syncgtm.com/blog/lead411-review)).
- **Pricing (real):** **Spark $75/user/mo** (annual; $99 m2m) = 200 exports/mo; **Ignite ~$3,000/yr** ≈ 833 exports/mo; **Blaze** removes export caps + full API. Credits roll over but cap at **2× monthly** (max ~400 banked).
- **API surface:** Lead-Enrichment REST API; full API + custom workflows on the top **Blaze** tier.
- **EU/GDPR posture:** US-first; minimal EU/GDPR story — effectively a non-starter for compliant EU outbound.
- **Biggest weakness:** **One signal (Bombora topic intent) + one geography (US).** No EU depth, no signal diversity.
- **WHAT WE LEARN:** **Bundling intent into the data subscription is a strong SMB hook** — buyers love one bill. Copy the bundle, but make the *intent EU-native and multi-signal* (registry events, job postings, funding, web changes) rather than a single licensed US topic feed.

## 6. Wiza

- **HQ/region:** Canada/USA. A **LinkedIn Sales Navigator scraper + verifier**, not a database.
- **Primary data sources:** Extracts contacts from **your** Sales Navigator searches/lists, then finds + verifies emails in real time. No proprietary database — it rides LinkedIn.
- **Claimed coverage / accuracy:** "Most accurate B2B prospecting tool"; verified-email deliverability genuinely **~90–95%**, phone **~55–65%**.
- **Independent reality:** Email accuracy is real and strong; but it's **LinkedIn-only** (can't enrich conference lists, inbound forms, partner data) and depends on a **paid Sales Navigator seat** ([SyncGTM](https://syncgtm.com/blog/wiza-review); [Prospeo](https://prospeo.io/s/wiza-email-finder)).
- **Pricing (real):** From **$83/mo** (Email) / **$166/mo** (Email+Phone); PAYG **$0.35/email, $1.50/phone**. **True cost $265–315/mo** once the required Sales Nav seat is added. Credits **expire monthly** (use-it-or-lose-it); 30k/yr export + 10k/mo credit ceilings. Some annual users lost API access mid-contract on a terms change.
- **API surface:** API only on the top tier — and historically unstable (terms changed on existing subscribers).
- **EU/GDPR posture:** Weak/structural problem — it operates on **LinkedIn data via your logged-in seat**, exactly the tier our compliance doc keeps off-by-default. Not a model we can or should emulate.
- **Biggest weakness:** **Total LinkedIn dependence** + hidden Sales-Nav cost + expiring credits + an account-ban risk it imports from LinkedIn ToS.
- **WHAT WE LEARN:** Mostly a **what-not-to-do.** Their accuracy is good but the whole model is parasitic on LinkedIn and exposes the buyer to ToS/ban risk. Our pitch writes itself: *"the verified emails Wiza gives you — without needing a LinkedIn seat, a scraper, or the ban risk,"* sourced from lawful primary data.

## 7. Findymail

- **HQ/region:** France (EU). Email finder built for cold-outbound deliverability.
- **Primary data sources:** Email find + verify with strong **catch-all handling**; LinkedIn + domain inputs. Verified-only billing.
- **Claimed coverage / accuracy:** Guarantees **<5% bounce** (credit refund if exceeded). Independent: Dropcontact saw **1.1% hard bounce / 20k tests**; Clay 90% data quality, 84% EU coverage; cross-tool benchmark **~75% verified find rate** — top-of-class ([SyncGTM](https://syncgtm.com/blog/findymail-review); [Prospeo benchmark](https://prospeo.io/s/best-email-finder-tools-2026)).
- **Independent reality:** One of only two tools (with Anymailfinder) that consistently top *bounce-tested* benchmarks. Trade-off: enrichment rate ~40% (it returns *fewer but cleaner* — by design).
- **Pricing (real):** **$49 / $99 / $249/mo** (1k / 5k / 15k credits); **1 credit = 1 email, 10 = 1 phone**; **only charged for verified results**. Yearly ≈ 17% off. ≤10 users below Enterprise.
- **API surface:** Email-Finder, Email-Verifier, Lead-Finder **REST APIs** on **all paid plans** + webhooks — developer-friendly.
- **EU/GDPR posture:** French/EU-based; **no EU/APAC phone** (explicitly cites GDPR). Email-only EU posture is conservative-by-design.
- **Biggest weakness:** **Coverage/find-rate is deliberately low** (~40% enrichment) and it's **email-only** — no firmographics, no real database to prospect *from*.
- **WHAT WE LEARN:** **Verified-only billing + a public bounce guarantee is the single most-loved feature in this whole batch** (4.9/5 G2). It directly attacks Apollo's billing-surprise reputation. We should adopt "**you only pay for what's verified, with a published bounce SLA**" as a headline commitment — it's cheap to offer when your data is genuinely clean.

## 8. Prospeo

- **HQ/region:** France (EU). LinkedIn-extension email + phone finder.
- **Primary data sources:** **Single** enrichment source (no waterfall); 280M+ profiles / 143M verified emails claimed; Chrome extension sits inside LinkedIn.
- **Claimed coverage / accuracy:** Claims **98%**; 40k+ users.
- **Independent reality:** **The cautionary tale of the batch.** Single-lookup hit ~68%, but **bulk Sales-Nav match as low as 4.5–16.9%** while still burning credits — the **lowest verified rate** in the 5,000-contact benchmark ([Prospeo's own benchmark](https://prospeo.io/s/best-email-finder-tools-2026); [EmailWarmup](https://emailwarmup.com/blog/email-deliverability-tools/prospeo-review/)). Verification is conservative-accurate but *coverage* is the killer.
- **Pricing (real):** Free (75/mo), **$39 / $99 / $199 / $369** (1k / 5k / 20k / 50k credits) ≈ **$0.039→$0.007/credit**. The trap: **bulk burns credits regardless of match**, and support/refunds are unreliable.
- **API surface:** Email-finder + data-enrichment REST API; clean docs.
- **EU/GDPR posture:** French/EU base; single-source so provenance is shallow.
- **Biggest weakness:** **Single source + charge-on-miss in bulk** = catastrophic credit waste on real prospect lists, despite a slick single-lookup demo.
- **WHAT WE LEARN:** The gap between **demo accuracy and bulk reality** is the most exploitable weakness in the category. Lead every benchmark and case study with a **bulk, list-level match rate on a realistic list**, never the cherry-picked single lookup — and never charge on a miss. Prospeo's pain is our positioning.

## 9. Anymailfinder

- **HQ/region:** UK/EU. Pay-per-verified email finder.
- **Primary data sources:** Live find + verify by name/domain; returns only **Valid** (billed), with Risky/Not-Found free.
- **Claimed coverage / accuracy:** "97%+ on Valid" — and unusually, *credible*: independent 5,000-contact benchmark found **86.4% find rate at 0.9% false-positive — highest find rate of any standalone finder** ([Anymailfinder benchmark](https://anymailfinder.com/blog/best-email-finder-tools-2025); [SyncGTM](https://syncgtm.com/blog/anymail-finder-review-2026)).
- **Independent reality:** Genuinely best-in-class on the *combination* of find rate + low false-positive. Weaknesses: **no outreach features**, coverage **patchy outside US/UK**.
- **Pricing (real):** **$29–199/mo** (400 → 10,000 credits); **credits consumed only on Valid results** — Risky/Not-Found cost nothing. Clean, honest model.
- **API surface:** REST API, **no rate limits**, verified-only billing identical to app, 99.95% uptime, sync (2–5s) + webhook bulk — among the best APIs in the batch.
- **EU/GDPR posture:** UK/EU-leaning; business-email focus. Reasonable but US/UK-weighted coverage.
- **Biggest weakness:** **Just a finder** — no database to prospect from, no firmographics, no outreach; coverage thins outside US/UK.
- **WHAT WE LEARN:** Anymailfinder + Findymail prove the **honest-billing + high-accuracy finder is a *commodity* now** — we should *not* try to out-finder them on email-only. Instead, **embed verified-only finding as one lawful layer inside a full registry-grounded platform** (firmographics + contacts + intent), so the buyer gets the finder *and* everything around it.

## 10. Skrapp.io

- **HQ/region:** EU. LinkedIn email finder + 200M-contact database.
- **Primary data sources:** **200M+ contacts / 40M+ companies** database + LinkedIn Chrome extension; real-time verification.
- **Claimed coverage / accuracy:** **85% find / 97% verification** claimed.
- **Independent reality:** **Claim vs reality gap is severe** — independent benchmarks show **42–48% valid emails**, not 92%; the "92%" measures *search success*, not deliverability ([Prospeo](https://prospeo.io/s/skrapp-email-finder); [ZeroBounce](https://www.zerobounce.net/skrapp-io-review)). Mid-pack at best.
- **Pricing (real):** Free 50 credits; paid from **$30/mo**; **only Valid/Catch-all billed**, unused credits **roll over** (better than Wiza/Prospeo).
- **API surface:** REST API + CSV export + Chrome extension.
- **EU/GDPR posture:** Claims GDPR compliance, "publicly available business contact info only" — but the LinkedIn-extension scraping path is the same ToS-risk grey zone as GetProspect/Wiza.
- **Biggest weakness:** **Email-only + inflated accuracy claim** that collapses under bounce testing (~45% real).
- **WHAT WE LEARN:** Skrapp is the median of the cheap cluster — its credit roll-over is the one fair touch worth copying. Everything else (inflated "find=accuracy" claim, LinkedIn-extension risk) is the commodity trap. **Don't price-fight the bottom; differentiate on lawful provenance and a real verified rate.**

## 11. Snov.io

- **HQ/region:** Ukraine/USA. All-in-one finder + verifier + drip campaigns.
- **Primary data sources:** **500M+ contact** database, 15 search filters; finder + verifier + outreach in one.
- **Claimed coverage / accuracy:** **98%** marketed.
- **Independent reality:** Users report **~75–80%**, and the cross-tool benchmark put verified find rate at a brutal **~20.1%** on 5,000 Sales-Nav contacts — far below claim ([Prospeo](https://prospeo.io/s/snov-io-email-finder); benchmark above). The all-in-one convenience is the real draw, not the data.
- **Pricing (real):** **$29.25 / $74.25/mo** (1k / 5k credits, annual) + custom Ultra. **The credit trap: find and verify draw from the *same* pool**, so effective cost per *verified* email ≈ **2× headline**.
- **API surface:** REST API from the Starter plan; well-documented — good for custom workflows.
- **EU/GDPR posture:** Claims GDPR compliance on all plans; non-EU HQ, so provenance/notification story is thinner than the EU-native players.
- **Biggest weakness:** **Double-charging** (find + verify same credit pool) + low real find rate + cluttered UI at scale.
- **WHAT WE LEARN:** The **all-in-one bundle (data + verify + sequences) is what keeps Snov sticky despite mediocre data** — convenience beats accuracy for SMBs. But the double-credit model is resented. We can win the same SMB by bundling finder+verify+intent **without charging twice for one contact**, on cleaner EU data.

## 12. GetProspect

- **HQ/region:** EU (hosted DigitalOcean Amsterdam). LinkedIn email finder + lightweight CRM.
- **Primary data sources:** 200M-contact database + LinkedIn extension; built-in cold-email sender + light CRM + Sheets add-on.
- **Claimed coverage / accuracy:** **95%+** claimed, credits-back guarantee.
- **Independent reality:** **Three separate benchmarks all land 62–65% real accuracy** — i.e. a **~35–38% invalid rate** that will torch sender reputation on a 1k-email send. Worse: **multiple 2025–26 G2 reviewers report LinkedIn account restrictions/bans** from the Chrome extension's detectable scraping ([Prospeo](https://prospeo.io/s/getprospect-email-finder); [LeadsForge](https://www.leadsforge.ai/blog/getprospect-review)).
- **Pricing (real):** Free 50 valid/mo; **Starter $34/mo** (1k), **Agency $99/mo** (20k); **only valid emails billed**; every feature on every tier (only credit volume differs). Annual ≈ 30% off.
- **API surface:** REST API on paid plans; full feature parity across tiers is a genuinely nice model.
- **EU/GDPR posture:** **Amsterdam-hosted, "GDPR by default"** — decent infra story, but undermined by the LinkedIn-scraping ban risk it exposes users to.
- **Biggest weakness:** **62–65% real accuracy + active LinkedIn-ban risk** for the user. The compliance posture is hosting-deep, not provenance-deep.
- **WHAT WE LEARN:** GetProspect shows that **"GDPR-compliant hosting" is not the same as compliant *data*** — and buyers are starting to notice the ban risk. Our differentiator is provenance at the *field* level (source + lawful basis + last-verified), which neither hosting location nor a Chrome extension can fake. And we never put the customer's LinkedIn account at risk to deliver a result.

---

## What this batch teaches us

This batch is the **flank** of the sales-intelligence market — and it is softer than the Apollo/Cognism core. Three structural lessons:

**1. Provenance is an open lane, and only Dealfront and Vainu even attempt it.** The EU-native players (Dealfront, Vainu, Albacross) win precisely where they ground data in **official registers** — and lose the moment they leave the EU or stop at firmographics. None of them ships true *per-field* provenance (source + lawful basis + last-verified timestamp) across *both* firmographics *and* contacts, EU-wide. That is exactly the moat [`docs/COMPLIANCE.md`](../../docs/COMPLIANCE.md) describes, and it is currently **unoccupied**.

**2. The email-finder cluster has commoditised accuracy — but not honesty or integration.** Findymail and Anymailfinder already win the bounce-tested benchmarks (~75–86% verified) with the batch's most-loved feature: **verified-only billing + a published bounce SLA**. We do not out-finder them on email; we **absorb that honest-billing model as one lawful layer** of a full platform (firmographics + contacts + visitor-ID + intent), so the buyer stops juggling 3–4 subscriptions. Meanwhile the cheap tier (Prospeo, Skrapp, Snov, GetProspect) is riddled with the three weaknesses we attack directly: **inflated "find = accuracy" claims** (real rates 16–65% vs claimed 95–98%), **charge-on-miss / double-charge credit traps**, and **LinkedIn-scraping ban risk imported onto the customer**.

**3. "Unlimited" and "GDPR-compliant" are the two most abused words in the category.** SalesIntel's "unlimited" hides a 3,000/mo cap; GetProspect's "GDPR-compliant" is hosting-deep while exposing users to LinkedIn bans; Snov double-charges one contact. Every one of these is a trust wound visible in the **G2-vs-Trustpilot gap**. The winning move is almost embarrassingly simple: **publish the prices, publish the real bulk match rate, charge only for verified results, never write a cap you don't mean, and tag every personal-data field with where it came from and that it's lawful.** Compliance here is not a tax — it is the product, and this batch proves nobody is actually selling it yet.
