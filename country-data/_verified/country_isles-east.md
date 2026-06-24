# European Business-Data Sourcing Inventory — Isles + Central/Eastern Europe

Countries: United Kingdom, Ireland, Poland, Czech Republic, Hungary
Compiled: 2026-06-24. All URLs below were verified live via web search/fetch (2024-2026 currency).

## Cross-border layer (applies to ALL five countries)

- **BRIS / European e-Justice "Find a company"** — free real-time search of every EU/EEA business register (incl. IE, PL, CZ, HU; UK left BRIS after Brexit). Single point of access, no fees. https://e-justice.europa.eu/topics/registers-business-insolvency-land/business-registers-search-company-eu/general-information-find-company_en — Good for cross-check / discovery, NOT for bulk (per-company lookups only).
- **GLEIF LEI Golden Copy** — free daily full dump + delta files of all Legal Entity Identifiers globally (covers larger/regulated entities in every country here). CSV/JSON/XML. https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy — best free cross-border key to join registries and de-dupe corporate groups. Use as the "cheap confirm" source to skip slow scrapes.
- **OpenCorporates** — aggregates these registers; API is now paid/restricted but useful as a fallback cross-reference.
- **Open Data Directive (EU) 2019/1024 + Implementing Reg. (EU) 2023/138** — designates company + ownership data as High-Value Datasets → drives the free bulk portals (IE CRO, PL dane.gov.pl, CZ dataor.justice.cz). UK has its own equivalent free-data regime.

---

## United Kingdom — confidence: VERIFIED

- **Company registry:** Companies House. Free public-data REST API (key required, no charge): https://developer.company-information.service.gov.uk/ . Free monthly **bulk snapshot** of all live companies (CSV, multi-part ZIP, updated within 5 working days of month-end): https://download.companieshouse.gov.uk/en_output.html
- **Access model:** API (free, register for key) **and** bulk-download (free, no key). ~5M+ companies, full coverage of live register.
- **Directors / UBO:** Officers via API. Beneficial owners = **People with Significant Control (PSC)**: free daily full bulk snapshot in JSON, overwritten before 10am GMT daily: https://download.companieshouse.gov.uk/en_pscdata.html (>25% shares/votes or significant influence). Also available per-company via API.
- **Financial filings:** Free **Accounts Data Product** — daily (last 60 days) + monthly (last 12 mo) + historic back to 2008, iXBRL/XBRL ZIPs (~75% of accounts filed electronically): https://download.companieshouse.gov.uk/en_accountsdata.html
- **Contacts (legal):** No statutory email/phone directory; registered office addresses come from the register. Use website-scrape + email-pattern + MX/SMTP verify. B2B directories (Yell, Thomson) usable with care for legitimate-interest B2B.
- **Vehicle registry:** **DVLA Vehicle Enquiry Service (VES) API** — free per-lookup by reg plate (make/model/colour/fuel/CO2/tax/MOT status): https://developer-portal.driver-vehicle-licensing.api.gov.uk/ (NOTE: new registrations temporarily paused for system upgrades). **DVSA MOT History API** — free, full MOT test history. Owner/keeper data is NOT public (restricted to those with reasonable cause).
- **NER model:** spaCy `en_core_web_trf` (transformer, best F1) or `en_core_web_lg`. English full pipeline incl. NER.
- **Bypass/tooling:** Government APIs are clean — no WAF on the API/bulk endpoints. Use plain HTTP fetch + key. Reserve Screaming Frog / Sequentum for company-website contact scraping. Highest-throughput market: bulk files + free API.

## Ireland — confidence: VERIFIED

- **Company registry:** Companies Registration Office (CRO). **NEW Open Data Portal** (launched 2024/25): daily snapshot of all current + dissolved companies, **bulk CSV download AND API**, CC-BY-4.0 licence: https://opendata.cro.ie/dataset/companies (mirrored on https://data.gov.ie/dataset/companies). Aligns with EU Open Data Directive HVD.
- **Access model:** open-data bulk-download (free, daily CSV ZIP) + API (basic data free; document retrieval pay-per-call for registered accounts).
- **Directors / UBO:** Officers via CRO data/CORE. UBO = **Register of Beneficial Ownership (RBO)** https://rbo.gov.ie/ — **public access RESTRICTED** since Nov-2022 CJEU ruling (legislated into Irish law June 2023). Only competent authorities, designated persons (AML), or legitimate-interest applicants (journalists/NGOs) can access. Not open/bulk.
- **Financial filings:** CRO Open Data Portal also publishes a **Financial Statements dataset** (machine-readable, free); fuller documents via CORE pay-per-call. https://opendata.cro.ie/
- **Contacts (legal):** registry addresses + website-scrape + email-pattern/MX. Irish B2B directories (goldenpages.ie) usable with care.
- **Vehicle registry:** **National Vehicle and Driver File (NVDF)**, Dept of Transport. Owner data NOT open — provided only to approved third parties under S.I. 287/2015 (Finance Act 1993 s.60(3)). Aggregate/statistical vehicle registration data IS open on data.gov.ie (TDM01/TDA01 datasets) — counts, not owners. https://datacatalogue.gov.ie/dataset/national-vehicle-and-driver-database
- **NER model:** Irish business text is English → spaCy `en_core_web_trf`/`en_core_web_lg`. (Irish-Gaeilge `ga` is tokenizer-only, rarely needed.)
- **Bypass/tooling:** Open-data ZIP + API, no WAF. Plain fetch. Use Screaming Frog/Sequentum only for company-site contact harvesting.

## Poland — confidence: VERIFIED

- **Company registry:** Two registers. (1) **KRS** (National Court Register, companies) — official **open REST API** (RESTful, full+current excerpt scope, GDPR-trimmed), free: https://prs.ms.gov.pl/krs/openApi (dataset card: https://dane.gov.pl/en/dataset/27606 ). (2) **CEIDG** (sole traders) — official data warehouse + API at https://dane.biznes.gov.pl . (3) **REGON/GUS BIR1** statistical register API (free, key required): https://api.stat.gov.pl/Home/RegonApi
- **Access model:** API per-entity for KRS (rate-limited, not designed for full bulk); REGON BIR for ID resolution; CEIDG warehouse for sole-trader bulk. No single free national bulk dump of KRS — combine the three. Note PKD 2025 industry-code migration in effect.
- **Directors / UBO:** Directors in KRS excerpt (via API). UBO = **CRBR** (Central Register of Beneficial Owners), free public search, **no registration/fee**, but **NO official bulk API**: https://crbr.podatki.gov.pl . Only covers KRS-registered entities (not CEIDG sole traders). Bulk only via scrape or paid third-party (Transparent Data, getregdata).
- **Financial filings:** **Repozytorium Dokumentów Finansowych (RDF)** — free search + download of KRS entities' financial statements (XML + PDF): https://ekrs.ms.gov.pl/rdf/rd/ (viewer: https://ekrs.ms.gov.pl/rdf/pd/search_df ). Per-company, free.
- **Contacts (legal):** KRS/CEIDG addresses; CEIDG includes some self-published contact data. Website-scrape + email-pattern/MX. Panorama Firm / PKT.pl directories with care.
- **Vehicle registry:** **CEPiK** (Central Register of Vehicles & Drivers). Owner/driver data restricted to authorities (police, courts, tax). Open API + statistical datasets on dane.gov.pl (dataset 1558): https://dane.gov.pl/pl/dataset/1558 — technical/registration stats, NOT owners.
- **NER model:** spaCy `pl_core_news_lg` (Polish full pipeline incl. NER). Alternatively HerBERT-based HF models for higher accuracy.
- **Bypass/tooling:** Official APIs clean (no WAF) — plain fetch with rate-limit respect. KRS API is per-record + throttled → for volume use REGON BIR to enumerate, then KRS API/RDF. CRBR needs Botasaurus/curl_cffi if scraping. Screaming Frog/Sequentum for company sites.

## Czech Republic — confidence: VERIFIED

- **Company registry:** **ARES** (Administrative Register of Economic Entities, Ministry of Finance) — aggregates Commercial Register, Trade Register, REGON-equivalent, VAT, insolvency. Free REST API + **open-data XML bulk dump** in the national catalogue: https://ares.gov.cz/ (open data: https://dataor.justice.cz/ ). ~2.8M+ entities, daily updates. Underlying public register also free at https://or.justice.cz/ (Obchodní rejstřík).
- **Access model:** API (free) + open-data bulk XML (free, full register) — one of the most open markets here.
- **Directors / UBO:** Directors/board in Commercial Register (ARES/justice.cz). UBO = **ESM (Evidence skutečných majitelů)** at https://esm.justice.cz — **public access ENDED 17 Dec 2025** (post-CJEU C-37/20; confirmed by Czech Supreme courts). Now only authorities, AML-obliged entities, and legitimate-interest applicants. Historic public scrapes may exist but live access is closed.
- **Financial filings:** **Sbírka listin** (Collection of Documents) on or.justice.cz — financial statements, articles, resolutions as free PDF downloads, per company, no account needed: https://or.justice.cz/
- **Contacts (legal):** registry addresses; Firmy.cz directory; website-scrape + email-pattern/MX.
- **Vehicle registry:** Central Register of Road Vehicles (Registr silničních vozidel). Owner/operator data restricted — extract only on request (CZK 100/request) via municipal offices or gov portal: https://portal.gov.cz/en/sluzby-vs/request-for-data-output-from-the-road-vehicle-register-S7198 . Not open/bulk.
- **NER model:** spaCy supports Czech; for production NER prefer `Czech-NER` / Slavic-BERT or **NameTag 3** (ÚFAL, multilingual incl. Czech, high accuracy) — https://arxiv.org/pdf/2506.05949 . spaCy `xx`/Czech pipeline as fallback.
- **Bypass/tooling:** ARES API + open XML dump are clean — plain fetch, no WAF. justice.cz PDFs scrapeable directly. Highest free-bulk completeness of the CEE three.

## Hungary — confidence: LIKELY (free basics confirmed; full bulk is paid-only)

- **Company registry:** **e-Cégjegyzék** (Company Information Service, Ministry of Justice) — free basic company data lookup, no registration: https://www.e-cegjegyzek.hu/ (basic info: https://www.e-cegjegyzek.hu/?ceginformacio ). **No official free bulk download or open API** for the full register; deeper extracts are charged. OPTEN free mobile app gives basic data of all operating companies.
- **Access model:** free per-company web lookup only. Bulk/structured access = **paid third parties**: OPTEN (https://www.opten.hu/?lang=en ), Bisnode/Dun & Bradstreet, or API resellers (e.g. https://companyapi.hu/ — data sourced from the Ministry's Company Information Service). Treat full-register bulk as a cost line, not free.
- **Directors / UBO:** Directors in company extract (paid for structured/bulk). UBO register exists (Hungarian BO register under AML) — public access limited post-CJEU; not an open bulk source.
- **Financial filings:** **e-Beszámoló** — free public download of all companies' annual financial statements (filing mandatory within 5 months of FY-end; since 1 Jan 2025 any party incl. competitors can trigger enforcement for non-filing): https://e-beszamolo.im.gov.hu/oldal/kezdolap . This is the single richest FREE Hungarian source — per-company PDF/XML.
- **Contacts (legal):** registry addresses; website-scrape + email-pattern/MX. Hungarian directories with care.
- **Vehicle registry:** Belügyminisztérium / Nyilvántartó (járműnyilvántartás). **JSZP** platform lets anyone query public vehicle data freely, but **owner/operator data is NOT available** (data-protection); explicitly no owner data for marketing/research: https://www.nyilvantarto.hu/hu/adatszolgaltatas_kozlekedesi . Not open for owners.
- **NER model:** **HuSpaCy** `hu_core_news_lg` (drop-in spaCy pipeline, NER F1 ~0.869) — https://huggingface.co/huspacy/hu_core_news_lg / https://huspacy.github.io/ . Best Hungarian option by far.
- **Bypass/tooling:** e-Beszámoló + e-Cégjegyzék are scrapeable (server-rendered) — curl_cffi/Botasaurus if rate-limited. For the company register itself, the economical path is a paid OPTEN/companyapi.hu feed for structure + free e-Beszámoló for financials, joined on cégjegyzékszám/adószám. This is the only market where a paid registry feed is effectively required for bulk.

---

## Method/throughput notes (platform-level)

- **Cheap-confirm-skip-scrape pattern:** Use GLEIF + the free open-data dumps (UK, IE, CZ) and free APIs (UK PSC, PL KRS/REGON, CZ ARES) as the authoritative spine; only fall back to website-scraping (Screaming Frog / Sequentum / Botasaurus / curl_cffi) for contact points (email/phone) that registries don't carry.
- **Per-market best tool:** UK/IE/CZ = bulk-file + API (no browser, max parallelism). PL = API enumeration (REGON→KRS→RDF), CRBR via stealth scrape. HU = paid feed for register structure + free e-Beszámoló scrape for financials.
- **WAF reality:** None of the official government API/open-data endpoints here use anti-bot WAFs — plain concurrent HTTP. WAF concern only arises on commercial directories and some company websites → that's where stealth tooling (Botasaurus/curl_cffi) and the licensed crawlers earn their keep.
- **UBO caveat (2025-2026):** the CJEU C-37/20 ruling has closed PUBLIC bulk UBO access in IE (RBO), CZ (ESM, from 17 Dec 2025), and tightened HU; PL CRBR is still public but no official bulk API; only UK PSC remains fully free + bulk. Plan UBO coverage around UK-strong / EU-restricted.
