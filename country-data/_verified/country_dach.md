# DACH Business-Data Sourcing Inventory (Germany, Austria, Switzerland)

Verified June 2026 via official portals, opendata.swiss, data.gv.at, and Open Knowledge sources.
Focus: FREE / cheap / bulk acquisition of company register, directors+UBO, financial filings,
contact directories, vehicle data, and the right NER model. Scraping a paid registry is noted only
where it is the **only** path.

Cross-border anchors usable for all three: **BRIS** (Business Registers Interconnection System via
the European e-Justice Portal), **GLEIF** (free LEI golden-copy bulk, daily), and **OpenCorporates**
(aggregator; bulk under license). These supplement, never replace, the national registries below.

---

## 🇩🇪 GERMANY — confidence: VERIFIED

**Language:** German (`de`)

### (a) Company register
- **Official:** Handelsregister via the joint Registerportal der Länder — https://www.handelsregister.de/
  Free to search; **no official API and no official bulk dump**. Terms of use cap automated retrieval
  at **60 requests/hour** — exceeding it can trigger §§303a/b StGB (criminal) exposure. So the official
  portal is **scrape-only and rate-capped** — do NOT mass-scrape it.
- **BEST FREE BULK (recommended):** **OffeneRegister.de** (Open Knowledge Foundation Deutschland) —
  https://offeneregister.de/daten/ — full dump of **~5.3M companies** (2.3M active + 2.9M removed),
  with officers, related registrations and registered address. Formats: **JSON Lines (gzip)** and a
  **SQLite** database, matching the OpenCorporates "company" schema. License: **CC-BY 4.0**
  (attribute OpenCorporates). Note: the open dump is older (last broad refresh ~2019–2021) so treat as
  a **backbone**, not a live feed; refresh deltas via the API tools below.
- **FREE OSS TOOL:** `bundesAPI/handelsregister` — https://github.com/bundesAPI/handelsregister
  (Python; search by name/location/legal form/postcode). Respect the 60/hr cap.
- **Paid-but-cheap API alternatives** (only if you need live coverage of all ~4M+ active companies):
  OpenRegister (https://docs.openregister.de) and handelsregister.ai (https://handelsregister.ai/en) —
  REST, bulk export, ~per-call pricing.

### (b) Directors + UBO
- **Directors / officers:** included in OffeneRegister bulk (officer records) and in the live
  Handelsregister extracts (AD/Aktueller Abdruck — small fee per document on the portal).
- **Beneficial owners (UBO):** **Transparenzregister** — https://www.transparenzregister.de/
  **RESTRICTED since the 2022 CJEU ruling.** Public access now requires demonstrating a "berechtigtes
  Interesse" (legitimate interest) per entity; obliged entities/authorities have full access. Treat UBO
  as **case-by-case, not bulk**. A statutory reset/expansion is slated around 2027 — recheck.

### (c) Annual financial filings
- **Official, FREE, machine-readable:** Since Aug 2022 disclosures live in the **Unternehmensregister**
  — https://www.unternehmensregister.de/ (search free; full annual accounts download typically **~€1**).
  Filings are submitted **exclusively in XBRL** (Digitaler Finanzbericht; large/listed entities ESEF).
  As of **1 Jan 2025** XBRL submission is mandatory for affected entities → high machine-readability.
- **Bulk:** no official free bulk dump of all Jahresabschlüsse. Practical bulk paths: pay-per-doc
  harvest via Unternehmensregister, or third-party APIs (OpenRegister Bundesanzeiger API, handelsregister.ai).
  An Apify Bundesanzeiger crawler exists (~1.5M entities) as a scrape fallback.

### (d) Contact points (legal to use)
- **Das Telefonbuch** (https://www.dastelefonbuch.de), **Das Örtliche** (dasoertliche.de),
  **GelbeSeiten** (https://www.gelbeseiten.de, ~5M business entries), **GoYellow**. These are public B2B
  directories. Scraping **publicly available non-personal business contact data** is generally permissible;
  avoid harvesting personal data of natural persons (GDPR/UWG email-marketing rules — B2B cold email in
  DE is restricted, prefer phone/postal). Company-website imprint ("Impressum") is mandatory in DE → a
  rich, legal email/phone source per domain.

### (e) Vehicle registration data
- **Kraftfahrt-Bundesamt (KBA)** Zentrales Fahrzeugregister (ZFZR) —
  https://www.kba.de/EN/Themen_en/ZentraleRegister_en/ZFZR_en/ — **RESTRICTED BY LAW**
  (§36(6) StVG; sector-specific). Holder/vehicle lookups only for authorised bodies. **No open bulk.**
  Only **aggregate statistics** (new registrations, stock, by Kreis/brand) are openly published, plus
  **CoC/type-approval (Typgenehmigung) reference data**. Per-vehicle owner data is not obtainable openly.

### (f) NER model
- **spaCy:** `de_core_news_lg` — https://huggingface.co/spacy/de_core_news_lg (CPU, large vectors).
- **Transformer alternative (higher accuracy):** `flair/ner-german-large` on HuggingFace, or
  spaCy `de_dep_news_trf`.

---

## 🇦🇹 AUSTRIA — confidence: VERIFIED

**Language:** German (`de`)

### (a) Company register
- **Official:** Firmenbuch (Ministry of Justice). Free basic search via **JustizOnline** —
  https://justizonline.gv.at/jop/web/firmenbuchabfrage (no auth for basic metadata). Full extracts are
  paid via Verrechnungsstellen (billing agents, e.g. compass, KSV).
- **BEST FREE BULK (recommended):** **High Value Datasets (HVD) des Firmenbuchs** on
  **data.gv.at** (Open Government Data Austria) — published under the **EU Open Data Directive HVD**
  regulation. Catalog: search "High Value Datasets Firmenbuch" at https://www.data.gv.at/ (CKAN).
  Contains the EU-mandated free core fields for capital companies: **name, legal form, registered office,
  registration state, registration number** (+ HVD extensions). License: typically **CC-BY 4.0**. This is
  the open, bulk-friendly Austrian backbone.
- **Scrape fallback:** JustizOnline Firmenbuchabfrage (Apify scraper exists) for fields not in HVD.

### (b) Directors + UBO
- **Directors / officers (Funktionäre):** in full Firmenbuch extracts (paid per extract via billing agents);
  partially derivable from HVD + JustizOnline.
- **Beneficial owners (UBO):** **WiEReG** Register der wirtschaftlichen Eigentümer (BMF, via USP) —
  https://www.bmf.gv.at/en/topics/financial-sector/beneficial-owners-register-act/ — **RESTRICTED.**
  Post-CJEU + the **1 Oct 2025 amendment**: access on "legitimate interest" only (obliged entities,
  journalists, academics, counterparties), **€4 per entry**. Not bulk, not open.

### (c) Annual financial filings
- Filed to the **Firmenbuch**; **Jahresabschluss** documents are retrievable as paid extracts via the
  billing agents / JustizOnline (small per-document fee). No free open bulk of full accounts. HVD covers
  identity fields, not the financial statements themselves. For financials at scale, pay per document or
  use a commercial aggregator (compass.at).

### (d) Contact points (legal to use)
- **HEROLD** (https://www.herold.at — Austria's yellow/white pages, business + phone + address),
  **TelefonABC**, **firmenabc.at**. Public B2B directory scraping of non-personal company contact data
  generally permissible; same GDPR/ECG (e-commerce) email-marketing caveats as DE. Website Impressum
  is mandatory → legal per-domain contact source.

### (e) Vehicle registration data
- Registration is run via insurers (VVO) + Statistik Austria; **no public per-owner lookup**.
- **Open aggregate data:** **Statistik Austria** open data — Kfz-Bestand (stock) and Kfz-Zulassungen
  (new/used registrations): https://www.statistik.at/statistiken/tourismus-und-verkehr/fahrzeuge/ and
  the OGD portal https://data.statistik.gv.at/ (e.g. dataset `OGD_f0760ext_OD_PkwGZL_1`). CSV/SDMX,
  **CC-BY**. Aggregate only — no individual VIN/owner.

### (f) NER model
- Same as DE German: spaCy `de_core_news_lg`; transformer `flair/ner-german-large`.

---

## 🇨🇭 SWITZERLAND — confidence: VERIFIED

**Language:** German / French / Italian (multilingual; `de`+`fr`+`it`)

### (a) Company register
- **Official:** **Zefix** — Central Business Name Index of the Federal Commercial Registry Office (FCRO),
  aggregating all **26 cantonal registers**. Web: https://www.zefix.admin.ch/
  **FREE REST API:** base https://www.zefix.admin.ch/ZefixPublicREST/ (no key for public search;
  some endpoints register-on-request). Returns name, UID, legal form, address, purpose, officers,
  auditors, capital, links to SOGC publications.
- **BEST FREE BULK / OPEN DATA (recommended):**
  - **opendata.swiss** "Zefix – Zentraler Firmenindex" —
    https://opendata.swiss/en/dataset/zefix-zentraler-firmenindex — **daily-updated** core data of all
    active legal entities (name, seat, domicile). License: open (OPEN-BY-ASK-PERMITTED / CC-style).
  - **LINDAS Linked Data + SPARQL** — dataset https://register.ld.admin.ch/.well-known/dataset/foj-zefix ;
    SPARQL endpoint **https://lindas.admin.ch/query/** (queryable bulk, RDF). Ideal for programmatic
    full-universe pulls without scraping.

### (b) Directors + UBO
- **Directors / officers + auditors:** available **free** via the Zefix REST API and LINDAS per company.
- **Beneficial owners (UBO):** **No public UBO register exists in Switzerland** (as of mid-2026). A
  federal **transparency register / beneficial-ownership register law** has been adopted and is being
  introduced, but it will be **non-public** (authority access only). So UBO is not openly obtainable;
  derive control from shareholding disclosures in SOGC / cantonal filings where available.

### (c) Annual financial filings
- Switzerland has **no general public filing of annual accounts** for private companies (only listed
  issuers via SIX disclosure, and banks/insurers via FINMA). For most SMEs, financial statements are
  **not publicly available** — this is a structural gap, not a sourcing failure. Use SOGC
  (https://www.shab.ch/) for statutory publications (capital changes, liquidations) and SIX for listed.

### (d) Contact points (legal to use)
- **local.ch** (https://www.local.ch) and **search.ch / tel.search.ch** (https://search.ch/tel/) —
  both Swisscom Directories; Switzerland-wide phone+address, free.
- **search.ch tel API** — FREE key at https://search.ch/tel/api/getkey ; spec at
  https://search.ch/tel/api/help . Quota **~1000 requests/month**, max 20 results/request, Atom/XML.
  This is a **legal, official API** — preferred over scraping for CH contacts.
- **ZIP.ch** reverse lookup as supplement.

### (e) Vehicle registration data
- **ASTRA (Federal Roads Office)** MOFIS-derived vehicle data — **open standard datasets FREE** at
  **https://opendata.astra.admin.ch/ivzod** (IVZ open data; vehicle stock/characteristics). Richer
  fee-based datasets need a registered account (per-record fee). **No open per-owner lookup** (data
  protection), but vehicle-level/aggregate datasets are openly downloadable.
- **BFS (Federal Statistical Office):** new-registration + stock statistics —
  https://www.bfs.admin.ch/bfs/en/home/statistics/mobility-transport/...
- **opentransportdata.swiss** for mobility/traffic.

### (f) NER model
- **Multilingual is required (DE/FR/IT).** Use language-routed spaCy:
  `de_core_news_lg` + `fr_core_news_lg` + `it_core_news_lg`, OR a single multilingual transformer
  `xlm-roberta-large-finetuned-conll03` / `Babelscape/wikineural-multilingual-ner` (HuggingFace) so one
  model covers all three Swiss official languages.

---

## Cross-border / supplementary (all DACH)
- **GLEIF** — https://www.gleif.org/en/lei-data/gleif-golden-copy — free daily bulk LEI golden copy
  (legal name, address, registration authority, parent relationships). Excellent join key + ownership hints.
- **BRIS / European e-Justice Portal** — https://e-justice.europa.eu/ — cross-register search for DE/AT
  (EU members; CH not in BRIS).
- **OpenCorporates** — aggregator; bulk via data licence (free for some non-commercial).
- **OpenSanctions** — https://www.opensanctions.org/ — includes de_offeneregister; free non-commercial,
  licence for business use.

## Speed/bypass notes per market
- **DE Handelsregister:** never bulk-scrape (criminal-law exposure, 60/hr). Use OffeneRegister bulk +
  bundesAPI tool for deltas. WAF: low on OffeneRegister (static files) → max parallel download.
- **AT JustizOnline / data.gv.at:** HVD is plain CKAN/static → high parallelism. JustizOnline portal is
  JS-heavy → Screaming Frog/Sequentum or Playwright for the few non-HVD fields.
- **CH Zefix/LINDAS:** official REST + SPARQL → no bypass needed; throttle politely. search.ch tel API
  has a 1000/mo quota → rotate with local.ch scrape (light WAF) for volume.
- **Directories (Telefonbuch/GelbeSeiten/Herold/local.ch):** moderate anti-bot → curl_cffi / Botasaurus
  or Screaming Frog; confirm a cheap official API (search.ch) first to skip the scrape.
