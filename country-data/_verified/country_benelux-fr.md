# European Business-Data Sourcing Inventory — Benelux + France

Scope: Netherlands, Belgium, Luxembourg, France.
For each country: (a) full company register, (b) directors + UBO, (c) annual financial filings, (d) legal contact directories, (e) national vehicle registration data, (f) NER language model.
Verified via WebSearch/WebFetch June 2026. Confidence flags reflect what could actually be confirmed against official sources.

Cross-border anchors (use everywhere, all free):
- **BRIS** (Business Registers Interconnection System) via European e-Justice Portal — real-time cross-border company search, free, covers all EU + EEA limited-liability companies + branches + SE. https://e-justice.europa.eu/ (search: https://webgate.ec.europa.eu/e-justice/searchBris.do)
- **BORIS** = beneficial-ownership register interconnection — exists but access is now legitimate-interest-gated post-CJEU 2022 (C-37/20). Not bulk.
- **GLEIF LEI Golden Copy / Concatenated Files** — free daily bulk download of all LEI records (legal name, address, registration authority, parent relationships). https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy — excellent free cross-walk to orgnr/SIREN/KBO/RCS and corporate-group structure.
- **OpenCorporates** API — aggregates many EU registers; free tier limited, bulk requires licence. Use as fallback/reconciliation, not primary.

---

## NETHERLANDS (NL) — confidence: VERIFIED

**(a) Company register — KVK Handelsregister**
- KVK is the sole official register. Two free open-data products on the KVK Developer Portal (https://developers.kvk.nl/documentation):
  - **Open Dataset Basic Company Information** — FREE bulk download (ZIP of semicolon-separated CSV) + API. https://www.kvk.nl/en/ordering-products/kvk-business-register-open-data-set/ . CRITICAL CAVEAT: the bulk open dataset is **anonymised** — it deliberately EXCLUDES the KVK number and the organisation name, and only gives the first 2 digits of the postcode. Fields present: start date, active status, insolvency indicators, legal structure, postcode region, SBI (activity) codes, main activity, member state. Covers BV/NV only (no sole proprietorships, no employee counts). Good for population/statistics, useless for named-entity targeting on its own.
  - To get **named** companies + KVK numbers you need the **paid KVK Handelsregister API** (Zoeken / Basisprofiel / Vestigingsprofiel) — per-query pricing, requires contract + API key. This is the only legal route to names at scale from KVK.
- Practical free-name workaround: reconcile the anonymised open set / scrape with **GLEIF LEI** (free names+addresses for entities that have an LEI) and BRIS lookups.

**(b) Directors + UBO**
- Directors (bestuurders) are NOT in the free open dataset; available via the paid KVK Basisprofiel/uittreksel API or paid extract.
- **UBO register**: access RESTRICTED since 15/16 July 2025 (Dutch Amendment Act implementing CJEU C-37/20). No public/bulk access. Only competent authorities, obliged entities (banks/notaries under AMLD), and parties with legitimate interest. A "KVK Dataservice UBO extract" + UBO API for permitted users is announced but **not expected until Q2 2026**. Source: https://www.kvk.nl/en/ubo/about-the-ubo-register/

**(c) Annual financial filings**
- **KVK Open Dataset Financial Statements (Jaarrekeningen)** — bulk delivery = 5 downloads, on the developer portal. https://www.kvk.nl/en/ordering-products/kvk-financial-statements-open-data-set/ and https://developers.kvk.nl/documentation/open-dataset-jaarrekeningen-api . SBR/XBRL-based deposits. Free.

**(d) Contact directories (legal)**
- KVK data has limited contact info. Legal B2B directories: company websites (scrape own imprint pages), **De Telefoongids / Detelefoongids.nl**, KvK-linked business listings. Phone/email harvesting must respect GDPR + Telecommunicatiewet (B2B email allowed if relevant + opt-out). LEI records and company websites are the cleanest legal sources. Avoid consumer phone scraping.

**(e) Vehicle registration data — RDW (BEST IN EUROPE)**
- **RDW Open Data** — fully open, free, NO API key, bulk + Socrata SODA API. Portal: https://opendata.rdw.nl/ . Core dataset "Gekentekende_voertuigen" (m9d7-ebf2) = ALL registered vehicles' technical data from the Kentekenregister (Basisregistratie Voertuigen), in 5 linked sub-sets (general data, fuel/emissions, axles, bodywork, recalls). Owner personal data is NOT included (privacy), but plate→full-technical-spec is unrestricted and bulk. Client lib example: github.com/dovereem/rdw-api-client. This is the gold standard.

**(f) NER model**
- Language: Dutch. spaCy `nl_core_news_lg` (also _md/_sm) — POS+dep+NER. For higher accuracy: **RobBERT** (pdelobelle/robbert-v2-dutch-ner on HF) is SOTA Dutch BERT for token tagging. Multilingual zero-shot: GLiNER-X / gliner-multi. Recommended primary id: `nl_core_news_lg`.

---

## BELGIUM (BE) — confidence: VERIFIED

**(a) Company register — KBO / BCE / CBE (Crossroads Bank for Enterprises, FPS Economy)**
- **KBO Open Data** — FREE bulk download in CSV after free registration + email verification. Portal: https://economie.fgov.be/en/themes/enterprises/crossroads-bank-enterprises/services-everyone/public-data-available-reuse/cbe-open-data
- MAJOR UPGRADE: since **3 November 2025**, COMPLETE open-data files are made available DAILY (previously monthly, first Sunday). Plus daily update/delta files. Manual download via portal OR **SFTP server** (request access: kbo-bce-webservice@economie.fgov.be). No API key for file download.
- Fields: enterprise number, legal form, status, denominations, addresses, NACE activities, establishment units, contact info, codes. Open-source models/parsers: github.com/mdewilde/kbobce-models, github.com/aerodynamica/KBOdatabase, github.com/Fedict/lod-cbe.

**(b) Directors + UBO**
- The KBO public-search page shows **functions/directors** (zaakvoerder/bestuurder) per enterprise, but the bulk OPEN DATA files restrict natural-person director data for GDPR (personal data may not be reused for direct marketing; shareholder data is not held by CBE at all). To get directors at scale you scrape the KBO Public Search (kbopub.economie.fgov.be) per enterprise number — legal but rate-limited.
- **UBO register** (operated by FPS Finance / Treasury) — access RESTRICTED post-CJEU; legitimate-interest model. Not bulk/open.

**(c) Annual financial filings — NBB Central Balance Sheet Office (Centrale Balanscentrale)**
- BEST-IN-CLASS free filings. NBB collects annual accounts of most Belgian companies.
- **Web services API**: register at https://developer.cbso.nbb.be — each day NBB produces datasets of references, PDF images, **XBRL** and **JSON** documents; retrieve by CBE number, current + historical. https://www.nbb.be/en/central-balance-sheet-office/consultation/web-services
- XBRL available since 2/4/2007; **CSV** files for all XBRL filings since 4/4/2022. "Authentic Data Daily Extract" + "Authentic Data Query" services. Individual PDF consultation is free; structured/bulk web services may have per-document or subscription terms — confirm pricing on signup.

**(d) Contact directories (legal)**
- KBO contact fields (phone/email/web where the company supplied them) are in open data BUT must NOT be reused for direct marketing (FPS Economy reuse condition). Legal directories: company websites, **Goldenpages / Pages d'Or (goldenpages.be)**. B2B outreach under GDPR legitimate-interest + opt-out.

**(e) Vehicle registration data — DIV (Direction Immatriculation Véhicules, FPS Mobility)**
- DIV registers cars/motorbikes/trailers >750kg. **No public open-data bulk of the registration register; owner data NOT public.** Statistics/parc data available via Statbel and FPS Mobility aggregates, but not per-plate→owner. Treat plate-level vehicle data as NOT openly available. Confidence on "no open bulk": likely.

**(f) NER model**
- Languages: Dutch (Flanders) + French (Wallonia) + some German. Use BOTH `nl_core_news_lg` and `fr_core_news_lg`, route by detected language, or a multilingual model. Recommended primary id: `xx_ent_wiki_sm` for mixed text, or language-route nl/fr large pipelines; RobBERT (NL) + camembert-ner (FR) for higher accuracy.

---

## LUXEMBOURG (LU) — confidence: LIKELY

**(a) Company register — RCS (Registre de Commerce et des Sociétés), operated by LBR (Luxembourg Business Registers)**
- Portal: https://www.lbr.lu/ . **Basic search is FREE**; you can view company number, legal form, status and DOWNLOAD many filed documents (statutes, annual accounts) at NO cost. Certified extracts carry a fee.
- **No confirmed official free BULK download or open public API of the full RCS company list.** A third-party blog claims an "LBR open data REST API (no auth for basic reads)" — this could NOT be confirmed on the official LBR site (the open-data page is behind a login), so treat as UNCERTAIN. Practical route: per-company free document retrieval + scraping the free RCS search. LBR launched a redesigned public portal 25 Aug 2025 and announced data-quality reforms (28 Jan 2026).
- data.public.lu (national open-data portal, 2,688 datasets) — has some company-adjacent datasets but RCS full-register bulk not confirmed there.

**(b) Directors + UBO**
- Directors/managers visible on the free RCS extract per company. UBO via **RBE (Registre des Bénéficiaires Effectifs)**, LBR-operated. RBE access RESTRICTED following CJEU Nov 2022 + Luxembourg Jan 2025 reform — only "authorised persons" with legitimate interest. Not bulk/open. https://www.lbr.lu/

**(c) Annual financial filings**
- Filed with RCS, **publicly accessible and downloadable free of charge** (annual accounts due within 7 months of FY end). Validated/structured via the **eCDF** platform (electronic Central Balance Sheet Data Filing, standardised chart of accounts PCN). https://guichet.public.lu/en/entreprises/gestion-juridique-comptabilite/registre-commerce/depots-publications/depot-comptes-annuels.html . No confirmed bulk API — retrieve per company.

**(d) Contact directories (legal)**
- Editus.lu (the national B2B/B2C directory) + company websites. GDPR applies. Small market — website scraping + RCS is usually enough.

**(e) Vehicle registration data — SNCA (Société Nationale de Circulation Automobile)**
- SNCA handles registration on behalf of the Ministry of Transport. **Open data**: "Parc Automobile du Luxembourg" on data.public.lu — https://data.public.lu/en/datasets/parc-automobile-du-luxembourg/ — monthly export of all vehicles (aggregate/technical fleet data; note the dataset's freshness has historically lagged, earliest exports ~2017 — verify current month). No per-owner data. Confidence: likely (dataset exists; currency to verify).

**(f) NER model**
- Languages: French + German + Luxembourgish (+ English). RCS filings are mostly FR/DE. Use `fr_core_news_lg` + `de_core_news_lg`, route by language; multilingual GLiNER-X for Luxembourgish (no strong dedicated spaCy LB pipeline). Recommended primary id: `fr_core_news_lg`.

---

## FRANCE (FR) — confidence: VERIFIED

France has the richest FREE open-data ecosystem of the four.

**(a) Company register — INSEE SIRENE + INPI RNE**
- **SIRENE (INSEE)** — the spine: every legal unit (SIREN) + establishment (SIRET). FREE OPEN BULK on data.gouv.fr: 5 downloadable stock files (active + ceased legal units, their establishments, succession links) + daily delta. https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret . Updated daily 00:00–03:00. **Parquet** format now offered (since June 2025); **CSV will be discontinued 1 Jan 2027** → plan for Parquet. API: API Sirene (free, account on portail-api.insee.fr). NAF/APE 2025 revision codes provided in advance from 16 Dec 2025.
- **API Recherche d'Entreprises** (free, NO auth) — https://recherche-entreprises.api.gouv.fr/docs/ — search by name/SIREN/SIRET/address/NAF/manager; synthesises RNE + SIRENE; returns establishments, managers, financials. Rate limit 7 req/s/IP, 30 req/s/ASN. Front-end: https://annuaire-entreprises.data.gouv.fr/

**(b) Directors + UBO — INPI RNE (Registre National des Entreprises)**
- **INPI RNE** centralises all company legal data; FREE access via API + **SFTP** bulk (account at data.inpi.fr → "Mes accès API / SFTP"). https://data.inpi.fr/content/editorial/Acces_API_Entreprises . Formats JSON/PDF, daily updates. Includes legal identity, legal form, capital, **représentants/dirigeants** (directors), establishments.
- **UBO (bénéficiaires effectifs)**: held in INPI RNE's registre des bénéficiaires effectifs. Post-CJEU, public access narrowed; press/civil-society/legitimate-interest access exists. Directors are freely bulk-available; full UBO bulk is access-gated — confirm current INPI access conditions per use case.

**(c) Annual financial filings — INPI RNE "Actes et bilans"**
- Non-confidential **annual accounts/balance sheets deposited since 1 Jan 2017** + acts/articles since 1993, FREE via INPI (API "Actes et bilans" + SFTP). https://entreprise.api.gouv.fr/catalogue/inpi/rne/actes_bilans . Note many SMEs opt for confidentiality (comptes confidentiels) → not all accounts public.

**(d) Contact directories (legal)**
- SIRENE/RNE give address + activity, limited phone/email. Legal directories: **PagesJaunes (pagesjaunes.fr)**, **Societe.com / Pappers.fr** (Pappers has a freemium API reusing SIRENE+RNE — handy aggregation), company websites. GDPR + French CNIL B2B rules (prospecting B2B allowed with relevance + opt-out).

**(e) Vehicle registration data — SIV (Système d'Immatriculation des Véhicules, Min. Interior / ANTS / France Titres)**
- Per-plate technical lookup exists via commercial APIs, but **owner personal data is NOT publicly accessible** (privacy). Free **HistoVec** (service-public.gouv.fr/particuliers/vosdroits/R52957) gives full vehicle history but only to the current owner. Open aggregate data: vehicle-fleet statistics on data.gouv.fr (immatriculations). No open per-owner bulk. Confidence: verified (that owner data is closed).

**(f) NER model**
- Language: French. spaCy `fr_core_news_lg` (also _md/_sm). Higher accuracy: **Jean-Baptiste/camembert-ner** (HF, widely used; WikiNER-trained so Wikipedia-biased) or **cmarkea/distilcamembert-base-ner** (faster). Multilingual zero-shot: GLiNER-X. Recommended primary id: `fr_core_news_lg`, upgrade to `Jean-Baptiste/camembert-ner` for PERSON/ORG extraction quality.

---

## Pipeline / orchestration notes (max-speed, self-adapting)
- **Prefer bulk over scrape**: SIRENE (FR), KBO (BE, now daily full), RDW (NL vehicles), GLEIF (cross-border) are all free clean bulk — load once, refresh on delta. These need zero anti-bot handling and run at full disk/network speed in parallel.
- **API-confirms-scrape pattern**: use free APIs (FR recherche-entreprises, NBB CBSO web service, KVK paid API) to confirm/enrich a record so the slow per-page scrape (KBO public search for directors, LBR document fetch) can be skipped when the API already has the field.
- **Anti-bot / WAF**: official open-data portals (data.gouv.fr, opendata.rdw.nl, fgov.be downloads, INPI SFTP) have NO bot defence → run high concurrency. Scrape-only surfaces (KBO public search kbopub, LBR RCS search, PagesJaunes/Editus) need polite rate limits + the user's licensed tools (Sequentum / Screaming Frog for site maps / UiPath for portal logins). Sense per-target: if a free bulk or API exists, NEVER scrape.
- **NER routing**: detect language per document (BE/LU are multilingual) and route to nl/fr/de large spaCy pipelines, or run one multilingual GLiNER-X pass and reconcile.
- **UBO reality (all four + EU-wide)**: post-CJEU C-37/20, no country offers open/bulk UBO anymore. Budget for legitimate-interest access or restrict UBO to directors-from-register + GLEIF parent relationships.
