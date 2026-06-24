# DACH Data-Source Inventory — Adversarial Verification
Date: 2026-06-24
Scope: Germany, Austria, Switzerland. Verified registry names, URLs, "free bulk" claims, API existence, vehicle registries.

## VERDICT: mostly-solid

The inventory is well-researched and largely accurate. Registry names, portal URLs, paid-API vendors, vehicle-registry restrictions, NER models, and the search.ch tel API are all real and correctly described. No fully hallucinated registries found. The most important real-world defect is a **staleness misrepresentation of OffeneRegister.de** (the headline German "free bulk" source), plus a few overstated/imprecise claims (XBRL mandate, WiEReG fee). These are correctable, not fatal.

---

## GERMANY

### CONFIRMED correct
- **Handelsregister.de**: no API/dump, 60 req/hr cap, §§303a/b StGB criminal exposure above that. The bundesAPI/handelsregister tool README itself states this verbatim. CORRECT.
- **bundesAPI/handelsregister** (github.com/bundesAPI/handelsregister): real, Python, queries the official portal, "work in progress", carries the 60/hr + StGB warning. CORRECT. (Caveat: not very actively maintained, no releases — fine as described.)
- **Transparenzregister** restricted since 22 Nov 2022 CJEU ruling, legitimate-interest case-by-case, not bulk. CORRECT. (The "statutory reset ~2027" is a reasonable reference to EU AMLR/6th directive timelines — defensible.)
- **KBA ZFZR vehicle registry**: restricted by law, no open per-owner bulk, only aggregate statistics + type-approval reference data open. CORRECT. The inventory cites §36(6) StVG; the access regime spans §§35/36/37/39 StVG and is explicitly excluded from Open Data under §12a EGovG. Substantively correct (the single-paragraph citation is slightly narrow but not wrong).
- **Paid live APIs** openregister.de and handelsregister.ai: both real, both offer live/daily Handelsregister API. CORRECT.
- **NER model** spacy/de_core_news_lg on HF: real model card, MIT, NER F=0.849. CORRECT.

### DEFECT 1 (significant) — OffeneRegister.de is STALE, not "continuously updated"
The inventory implies a live ~5.3M-company free bulk. Reality:
- The bulk dump (de_companies_ocdata*.jsonl / openregister.db.gz at daten.offeneregister.de) was collected **June 2017–Jan 2019 and has NOT been refreshed since ~2019-02-01** (confirmed via OpenSanctions de_offeneregister: "Last change 2019-02-01", update frequency "not automated").
- The "~5.3M total (2.3M active + 2.9M removed)" figure is real but reflects 2017–2019 state, so the "active" subset is unreliable today.
- **Correction**: keep OffeneRegister as the best FREE static bulk, but label it clearly as a ~2019 snapshot. For current data you MUST use the (paid) live APIs or the bundesAPI delta tool. The inventory's own coverage line is fine; the implied freshness is the problem.

### DEFECT 2 (moderate) — XBRL "mandatory from 1 Jan 2025" is overstated/imprecise
- The "XBRL mandatory from 1 Jan 2025" claim conflates a **sector-specific** BaFin mandate (insurers/occupational pension funds) with a general all-company requirement. There is no blanket "all companies must file in XBRL from 1 Jan 2025" rule at the Unternehmensregister.
- "submitted exclusively in XBRL (Digitaler Finanzbericht)" is also imprecise: the **Digitaler Finanzbericht** is primarily a procedure for transmitting closing data to **banks** (credit assessment), not the singular mandatory register-filing format. Unternehmensregister/Bundesanzeiger accept XBRL (HGB/IFRS/US-GAAP taxonomies) but the framing here overstates exclusivity/universality.
- The rest (free search, pay-per-doc ~small fee, no free official bulk, ESEF for listed) is fine.

### Minor
- "individual extracts ~small fee" — correct (Handelsregister AD/CD extracts are low-cost, often free chargeable-document basis since 1 Aug 2022 reform; portal search is free).

---

## AUSTRIA

### CONFIRMED correct
- **Firmenbuch via JustizOnline**, free basic search at justizonline.gv.at/jop/web/firmenbuchabfrage. CORRECT.
- **HVD (High Value Datasets) des Firmenbuchs on data.gv.at**: real, EU Open Data Directive (Reg. EU 2023/138 Annex 5), free, **core identity fields only** — directors/Funktionäre and financial statements require authenticated/paid access via Verrechnungsstellen (compass, KSV). The inventory's "HVD = identity fields only" is CORRECT and well-judged. (One vendor blurb claims HVD includes "documents and financial statements" but the authoritative reading and Kyckr confirm free public access is limited fields; full director/financial data is paid.)
- **WiEReG** (BMF via USP), restricted post-CJEU, 1 Oct 2025 amendment, legitimate-interest, not bulk. CORRECT.
- Contact sources (HEROLD/herold.at, firmenabc.at, TelefonABC, ECG Impressum) — plausible and real.
- NER model reuse (de_core_news_lg) — fine.

### DEFECT 3 (minor) — WiEReG fee "€4/entry"
- Multiple sources put the **public extract ("öffentlicher Auszug") at €3**, not €4. (One Kyckr blog says €4; the more common/official-aligned figure is €3, possibly €3 net vs €4 with surcharge/VAT, or different extract type.)
- **Correction**: state "~€3 per public extract" (or "€3–4") rather than a hard €4.

---

## SWITZERLAND

### CONFIRMED correct (strongest country in the inventory)
- **Zefix (FCRO), 26 cantonal registers**, free ZefixPublicREST API (no key for public search), opendata.swiss daily core data, LINDAS SPARQL endpoint (lindas.admin.ch/query, dataset register.ld.admin.ch foj-zefix). All CORRECT and live.
- **Zefix officers/auditors via API**: the public register data does expose executives/directors/authorised signatories and (for GmbH/Sàrl) the public member list; AG shareholders are not disclosed. The inventory's "directors/officers + auditors FREE via Zefix REST API/LINDAS" is substantially CORRECT. (Minor nuance: full structured API use may require requesting a free key/account by emailing zefix@bj.admin.ch; "no key for public search" is true for basic search but heavy programmatic use is account-gated.)
- **No public UBO register (mid-2026)**: CORRECT and impressively current. LETA (Legal Entities Transparency Act / Bundesgesetz über die Transparenz juristischer Personen) adopted **26 Sep 2025**, register will be **NON-public** (authority/intermediary access only), in force **H2 2026**, implementing ordinance (LETO) in consultation. The inventory's "adopted but will be non-public" is exactly right.
- **Financial filings**: no general public filing of SME accounts; only SIX-listed issuers and FINMA-supervised banks/insurers publish; use SHAB/SOGC (shab.ch) for statutory publications. CORRECT.
- **search.ch / tel.search.ch API**: FREE key via search.ch/tel/api/getkey, **1000 requests/month** quota (max 20 results/req), Atom/XML format. ALL CONFIRMED verbatim against search.ch terms. Excellent. (Note: ToS prohibit "automated bulk requests to create/update address databases" — the bypassNotes suggestion to "rotate with local.ch scrape for volume" is a ToS/legal grey area, flag as caution not a factual error.)
- **ASTRA IVZ open data**: FREE at **opendata.astra.admin.ch/ivzod** (vehicle stock/characteristics), richer fee-based datasets need a registered account, no open per-owner lookup. CORRECT. (The old ivz-opendata.ch host was retired 31 Mar 2025 and redirects to the /ivzod path the inventory already uses — good.)
- Multilingual NER guidance (de+fr+it routing or xlm-roberta / wikineural) — sound.

### No defects found for Switzerland beyond the minor Zefix key nuance.

---

## SUMMARY OF CORRECTIONS
1. **DE / OffeneRegister freshness** (significant): bulk is a ~2019 snapshot, NOT continuously updated. Relabel as static historical dump; current data needs paid APIs / bundesAPI deltas.
2. **DE / XBRL mandate** (moderate): "mandatory from 1 Jan 2025" is sector-specific (insurers/pension funds), not all-company; Digitaler Finanzbericht is a bank-transmission procedure, not the universal mandatory register-filing format.
3. **AT / WiEReG fee** (minor): public extract is ~€3, not €4.
4. **CH / Zefix key** (very minor nuance): basic search keyless, but sustained programmatic API access is account-gated (free, email request).

## NO HALLUCINATIONS
Every named registry, portal, tool, and API exists as described. No invented sources.

## MISSED SOURCES (optional additions)
- **DE**: Bundesanzeiger.de (distinct front-end to the same filings as Unternehmensregister) and **GLEIF LEI** (free global bulk, good DE/AT/CH coverage for legal-entity identity + parent relationships).
- **DE/AT/CH**: **OpenCorporates** and **EU Business Registers Interconnection System (BRIS)** / e-Justice portal for cross-border lookups.
- **AT**: **Statistik Austria OGD** already cited for vehicles; **compass.at** correctly noted for financials.
- **CH**: **opendata.swiss** also hosts other FCRO/BFS datasets; **moneyhouse.ch** as a CH aggregator (paid).
These are enhancements, not gaps that undermine the inventory.
