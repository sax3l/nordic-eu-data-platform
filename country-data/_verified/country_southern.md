# Southern Europe Business-Data Sourcing Inventory — Italy, Spain, Portugal

Generated 2026-06-24. Scope: free/cheap, preferably bulk acquisition of (a) company register,
(b) directors + UBO, (c) annual financial filings, (d) legal contact directories, (e) national
vehicle registration data, (f) the right NER language model. Every registry name / portal / API
below was confirmed via web search/fetch in June 2026. Confidence is marked per country.

> Hard reality for all three: unlike SE/NO/DK/FI/FR/UK, the Southern-Europe **commercial**
> registries are **NOT** open-bulk. Registro Imprese (IT), Registro Mercantil (ES) and Registo
> Comercial (PT) are all **pay-per-document**. The open layer is the **official gazette** (BORME
> in ES via BOE open-data API; Diário da República in PT; Movimprese statistics in IT) plus
> **GLEIF/LEI** and **BRIS / e-Justice** cross-border. Plan the pipeline around: gazette feed
> for events (incorporations/changes) + paid visura/nota only on the targets you actually need +
> third-party directories (eInforma / Informa D&B / Axesor / Racius) for contact enrichment.

---

## ITALY (IT)

**Language:** Italian. **Confidence: verified.**

### (a) Company register
- **Registro Imprese** (official, run by **InfoCamere** for the Chambers of Commerce; ~6M+ entities).
  Free public search at https://www.registroimprese.it/ (English mirror https://italianbusinessregister.it/en/).
  **Free fields without login:** company name, registered office, **PEC** (certified email), main
  activity, status. Everything richer (visura, shareholders, officers, balance sheets) is **paid**.
- **Access model: scrape-only for the free fields / paid for the rest.** No free bulk API.
  - Paid bulk: **Telemaco** (contract platform — flat fee + per-document) and the
    InfoCamere "estrazione elenchi" (list extraction: Addresses-only or Extended, filter by
    location / ATECO / legal form) — paid, delivered by email. Portal:
    https://accessoallebanchedati.registroimprese.it/abdo/?lang=en
  - **Movimprese** (Unioncamere/InfoCamere) = **free open statistics** on company birth/death
    (aggregate, not entity-level).
  - Some **regional Chambers** publish CC-BY 4.0 open data (e.g. https://opendata.marche.camcom.it/).
- **Cross-border free fallback:** **BRIS / e-Justice** business-register search; **OpenCorporates**
  register #120 (https://opencorporates.com/registers/120); **GLEIF/LEI** golden copy for the
  LEI-holding subset.

### (b) Directors + UBO
- **Directors/shareholders:** inside the paid **Visura Ordinaria** (≈€6–€12 incl. XBRL balance).
- **UBO (titolare effettivo):** register went live 2023-10-09 but **public consultation is
  SUSPENDED** (Council of State orders 17 May 2024 + 15 Oct 2024, referral to CJEU).
  **D.Lgs. 210/2025** (in force 2026-01-09) replaced open access with a "relevant and differentiated
  legal interest" / tiered-access model. **Net: UBO is NOT freely retrievable now.** Only path is
  to **reconstruct ownership from shareholder data in the Visura**.

### (c) Annual financial filings
- **Bilanci in XBRL** filed since 2010. Per-company PDF+XBRL ≈ **€6–€12** via registroimprese.it /
  Telemaco. No free bulk. XBRL is machine-readable once purchased.

### (d) Contact points (legal directories)
- **PEC** (certified email) is the gold contact datapoint — **free** on the registroimprese.it
  record. Bulk PEC also available via **INI-PEC** (https://www.inipec.gov.it/, the national
  PEC index — searchable by company/professional).
- Third-party B2B (phones/emails): InfobelPRO, paid directories. Use the PEC-first strategy.

### (e) Vehicle registration data — **OPEN, this one is good**
- **PRA** (Pubblico Registro Automobilistico) run by **ACI**; per-plate visura is paid (Visurenet).
- **OPEN bulk fleet data:** **ACI Open Data** (level-5/LOD) https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/open-data/
  + **Annuario Statistico** (yearly). Fleet (parco veicolare) published ~May for prior year; market
    (immatricolazioni) ~July.
- **MIT open data** "Parco Circolante dei Veicoli" — downloadable open-format, per region/municipality:
  https://dati.mit.gov.it/catalog/dataset/dataset-parco-circolante-dei-veicoli (from the national
  vehicle archive of the Motorizzazione). **No per-owner data** (owner lookup stays paid via PRA).

### (f) NER model
- **spaCy `it_core_news_lg`** (https://huggingface.co/spacy/it_core_news_lg) — CNN, ~0.91 NER F.
  Transformer upgrade: `it_core_news_trf` (slower, GPU). HF alt: `Davlan/xlm-roberta-base-ner-hrl`
  or Italian BERT (`dbmdz/bert-base-italian-xxl-cased`) fine-tuned for NER.

### Bypass / tooling notes
- registroimprese.it free search is lightly protected; **Screaming Frog / Sequentum / curl_cffi**
  fine at low concurrency. Bulk = pay Telemaco, do NOT hammer. PEC harvest via INI-PEC is the
  high-ROI free move. For paid visure, automate the Telemaco account with **UiPath/Ranorex** to
  pull only targeted org IDs.

---

## SPAIN (ES)

**Language:** Spanish (Castilian). **Confidence: verified.**

### (a) Company register
- **Registro Mercantil** — Central (RMC, Madrid, name reservations + national index) + **52
  provincial registries** holding the detailed records. Run by **CORPME** (Colegio de Registradores).
  Search at https://sede.registradores.org/site/mercantil (select "Publicidad Mercantil"); basic
  notes **< €5** per company by card. **Pay-per-document; no free entity-level bulk.**
- **OPEN layer = BORME** (Boletín Oficial del Registro Mercantil), the official gazette:
  - **BOE open-data API (CONFIRMED):** `GET https://www.boe.es/datosabiertos/api/borme/sumario/{YYYYMMDD}`
    returns the daily summary in **XML/JSON**. Portal: https://www.boe.es/datosabiertos/.
    Free legal-authority electronic edition since Jan 2009 at https://www.boe.es/diario_borme/.
  - **datos.gob.es** catalogues the BORME dataset:
    https://datos.gob.es/en/catalogo/ea0040819-boletin-oficial-del-registro-mercantil-borme
    (Section I registered acts 2009→, Section II legal notices 2001→).
  - BORME gives **events** (incorporations, director changes, capital, dissolutions) — parse the
    daily XML to build/maintain a company + officer timeline for free. This is the spine of any
    Spanish pipeline.
- **CORPME OpenData portal** https://opendata.registradores.org/ exists but is **WAF-protected**
  (returned an anti-bot "request rejected" page on automated fetch) — treat as scrape-hostile.
- **Cross-border free fallback:** BRIS/e-Justice; OpenCorporates; **GLEIF/LEI**.

### (b) Directors + UBO
- **Directors (administradores):** appear in **BORME** appointment/cessation acts (free, parseable)
  and in the paid Registro Mercantil nota.
- **UBO (titularidad real):** CORPME runs **"Consulta de Titularidades Reales"**
  (https://sede.registradores.org/.../consulta-de-titularidades-reales/) — **paid, access-controlled**,
  not open bulk. Free reconstruction: combine BORME ownership/capital acts where present.

### (c) Annual financial filings
- **Cuentas anuales** deposited at the provincial Registro Mercantil; retrievable per-company for a
  small fee via sede.registradores.org. New annual-accounts models approved 26 May 2025 (Law 11/2023
  amendments). **No free bulk;** quarterly RM extract + daily BORME are the only open feeds.

### (d) Contact points (legal directories)
- **eInforma** (Informa D&B) https://www.einforma.com/ — NIF, phones, managers; **5 free reports**
  on registration. **Axesor** https://www.axesor.es/ — company phone/CIF/address pages (indexable).
  **QDQ** — free business listings, large directory. **Páginas Amarillas** — now paid.
- Legal-to-use: prefer eInforma/Axesor public company pages and the **INE/DIRCE**-derived directories;
  combine with BORME-derived officer names.

### (e) Vehicle registration data
- **DGT** (Dirección General de Tráfico) is the authority.
  - **OPEN monthly microdata:** "Microdatos de parque de vehículos (mensual)"
    https://www.dgt.es/menusecundario/dgt-en-cifras/.../Microdatos-de-parque-de-vehiculos-mensual/
    — vehicle type, fuel, registration year, displacement, etc. (vehicle-level, **anonymised — no owner**).
  - **MATRABA** census (matriculaciones/transferencias/bajas): **tightened from 2025-02-01** —
    no longer full chassis info, and access now requires a **legitimate-interest request**.
  - **NAP** (National Access Point) https://nap.dgt.es/ — traffic/mobility datasets.
  - datos.gob.es DGT tag: https://datos.gob.es/en/catalogo?tags=DGT.
  - Owner-level lookup = **not open** (legitimate-interest gated).

### (f) NER model
- **spaCy `es_core_news_lg`** (https://spacy.io/models/es) — ~0.90 NER F. Upgrade: `es_core_news_trf`
  (RoBERTa-BNE based, GPU). HF alt: `PlanTL-GOB-ES/roberta-large-bne-capitel-ner` (strong Spanish NER),
  or `mrm8488/bert-spanish-cased-finetuned-ner`.

### Bypass / tooling notes
- **Do NOT scrape opendata.registradores.org / sede.registradores.org with a naive crawler** — WAF
  rejects bots. Use the **BOE open-data BORME API (clean, free, XML/JSON)** for the registry spine.
  For per-company notes, drive the sede checkout with **UiPath/Ranorex** (logged-in, low volume).
  Axesor/eInforma public pages: **Screaming Frog** list-mode or curl_cffi at modest concurrency.

---

## PORTUGAL (PT)

**Language:** Portuguese (European). **Confidence: likely** (registry is real & confirmed; the
open-data surface is thin — best free path is the MJ publications search + DRE gazette feed).

### (a) Company register
- **Registo Comercial**, run by **IRN / Conservatórias do Registo Comercial**; companies keyed by
  **NIPC** (= NIF for legal persons, issued by **RNPC**). Official services via gov.pt /
  Portal da Empresa / Empresa Online. **Pay-per-certificate; no public API, no free bulk.**
- **OPEN-ish free layer:**
  - **MJ Publications / Portal da Justiça** https://publicacoes.mj.pt/Pesquisa.aspx — **free** search
    of mandatory company publications by name or NIF/NIPC. Returns Date, NIF/NIPC, Entity name,
    Municipality, Activity (HTML; **no full address; not bulk-downloadable**). This is the closest
    free registry-event source.
  - **Diário da República (DRE)** https://dre.pt — official gazette with an **open-data feed** of
    notices including incorporations/dissolutions (Portugal open-data initiative). Gazette events,
    not the underlying registry record.
  - **dados.gov.pt** — national open-data portal; **IMT/IRN have not published company datasets**
    there (confirmed: IRN/IMT orgs have ~no dataservices on the portal).
- **Cross-border free fallback:** BRIS/e-Justice (PT page); **OpenCorporates** register #208
  (https://opencorporates.com/registers/208); **GLEIF/LEI**. Open Knowledge index historically
  rated PT company-register openness low (not bulk/openly-licensed).

### (b) Directors + UBO
- **Directors (gerentes/administradores) & shareholders (sócios):** in the paid certidão / via
  Racius/Informa. Some appointment acts surface in MJ publications.
- **UBO: RCBE** (Registo Central do Beneficiário Efetivo), run by IRN. **Not open bulk**; access is
  controlled. Reconstruct from shareholder data where available.

### (c) Annual financial filings
- **IES (Informação Empresarial Simplificada)** — single annual filing (tax+accounting+statistical),
  due 15th day of the 7th month after year-end (≈15 July for calendar-year cos). DL 8/2007.
  **The IES data is legally public**, but there is **no free bulk portal**; per-company financials
  are obtained via paid providers (**Racius** ~960k companies; **Informa D&B / eInforma.pt**).
  Proof/consultation of one's own IES via gov.pt. **Banco de Portugal BPLIM** (microdata research lab,
  https://bplim.bportugal.pt/datasets) offers firm-level datasets to **accredited researchers** (not
  open, but a legitimate cheap/free route for research use).

### (d) Contact points (legal directories)
- **Racius** https://www.racius.com/ — 960k+ PT companies: acts, financials, balance sheets (freemium).
- **eInforma.pt** https://www.einforma.pt/ (Informa D&B) — NIF, contacts, shareholders, managers;
  **5 free reports** on registration; free monthly sector evolution.
- **Informa D&B directory** https://diretorio.informadb.pt/ — public company info, updated daily.
- These are the practical legal contact-enrichment sources (phones/emails) for PT.

### (e) Vehicle registration data
- **IMT** (Instituto da Mobilidade e dos Transportes) = authority for **registo automóvel** /
  matrícula; services at gov.pt / imtonline.pt. **No open vehicle dataset on dados.gov.pt**
  (confirmed: IMT has no dataservices published there). IMT does offer a **European homologation
  records consultation** online. **Owner/registration data = not open**; per-vehicle lookups go
  through IMT services. Fleet aggregates appear in **ACAP / INE** statistics rather than IMT open data.
- **Net: PT vehicle data is the weakest of the three — no open bulk; treat as gated/manual.**

### (f) NER model
- **spaCy `pt_core_news_lg`** (https://huggingface.co/spacy/pt_core_news_lg, https://spacy.io/models/pt)
  — note these are **Brazilian-Portuguese** trained; works on European PT but watch domain drift.
  Upgrade: `pt_core_news_trf`. European-PT-aware HF alts: `Davlan/xlm-roberta-base-ner-hrl`,
  `lfcc/bert-portuguese-ner`, or `neuralmind/bert-base-portuguese-cased` (BERTimbau) fine-tuned for NER.

### Bypass / tooling notes
- **publicacoes.mj.pt** is a classic ASP.NET WebForms search (VIEWSTATE) — scriptable with
  **Sequentum / UiPath** (handle the postback) or Screaming Frog won't suffice (form POST). DRE has
  a clean open feed — prefer it for gazette events. Racius/eInforma public pages: curl_cffi /
  Screaming Frog list-mode, low concurrency.

---

## Cross-border free spine (all three)
- **BRIS** (Business Registers Interconnection System) via **European e-Justice Portal** — unified
  free company search across IT/ES/PT (and EU). Good for de-duplication and cross-checking.
- **OpenCorporates** — free company data, registers #120 (IT), ES provincial, #208 (PT).
- **GLEIF / LEI** golden copy (Level 1 + Level 2 "who-owns-whom") — free bulk download; covers the
  LEI-holding subset (larger/financial entities) with verified parent relationships → great for UBO
  hints where the national UBO registers are gated.
- **VIES** (EU VAT validation) — free per-VAT validation (IT partita IVA, ES NIF-IVA, PT NIF) to
  confirm active status; not bulk but cheap confirmation that lets a slow scrape be skipped.

## One-line strategy per country
- **IT:** PEC/INI-PEC (free) + Movimprese stats (free) + ACI/MIT vehicle open data (free) →
  targeted Telemaco visure (paid) for officers/UBO-reconstruction/XBRL.
- **ES:** BOE BORME open-data API (free XML/JSON spine for companies+officers events) + DGT vehicle
  microdata (free) → targeted sede.registradores notes (cheap) for accounts/UBO.
- **PT:** MJ publicacoes + DRE gazette feed (free events) + Racius/eInforma (freemium contacts) →
  paid certidão / IES for financials; vehicle data essentially gated.
