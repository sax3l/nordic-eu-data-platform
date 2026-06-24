# Nordic Business-Data Sourcing Inventory (SE / NO / DK / FI / IS)

Verified June 2026. Sources confirmed live via WebSearch/WebFetch (2024-2026 currency).
For each country: (a) full company register, (b) directors + UBO, (c) annual financial filings,
(d) legal contact directories, (e) national vehicle registration data, (f) NER language model.

Cross-border helpers usable everywhere: **BRIS / e-Justice Business Registers**
(https://e-justice.europa.eu, EU+EEA interconnection — Iceland/Norway participate as EEA),
**OpenCorporates** (https://opencorporates.com, bulk via licence), **GLEIF/LEI**
(https://www.gleif.org/en/lei-data/gleif-concatenated-file — free global daily bulk, good for
group structure + cross-border matching).

Scandinavian NER shortcut: **NbAiLab/nbailab-base-ner-scandi** (HuggingFace) covers
Swedish + Norwegian + Danish + (some) Faroese/Icelandic in ONE model — ideal for a single
Nordic pipeline; per-language models listed below give best accuracy.

---

## SWEDEN (SE) — confidence: VERIFIED

- **Company registry:** Bolagsverket (https://bolagsverket.se/apierochoppnadata).
  Since 3 Feb 2025 the "valuable datasets" (värdefulla datamängder) — Bolagsverket + SCB —
  are **FREE, no contract**. (EU Open Data Directive high-value datasets.)
- **Registry access:**
  - BULK-DOWNLOAD (free): `bolagsverket_bulkfil.zip` + `scb_bulkfil.zip` (basic company data,
    zip→.txt) at https://bolagsverket.se/apierochoppnadata/nedladdningsbarafiler.2517.html
  - API (free): "API för värdefulla datamängder" + "Hämta företagsinformation" API v4.4
    (released 23 Apr 2025) https://bolagsverket.se/apierochoppnadata/vardefulladatamangder/
  - Coverage: ~1.8M legal entities. Supplement turnover/employees from Bolagsverket annual
    reports (see below) or the existing local `allabolag__companies` (1.86M, Fabric).
- **Directors + UBO:** Beneficial owner register ("verklig huvudman") at Bolagsverket since 2017
  (https://bolagsverket.se/en/omoss/flerverksamheter/omverklighuvudman.2539.html). Directors/board
  come from the company-information API. UBO lookups historically per-company (post-2022 CJEU ruling
  tightened public bulk access; available to obliged entities / legitimate interest).
- **Annual financial filings:** Digital iXBRL annual reports — **FREE weekly bulk**, coverage 2020→,
  zip→iXBRL. From financial years starting after 31 Dec 2025 iXBRL becomes MANDATORY for all AB
  (>1M digital reports/yr already). Part of valuable datasets.
  https://bolagsverket.se/apierochoppnadata/hamtaforetagsinformation/nedladdningsbarafiler.2517.html
- **Contact directories (legal):** allabolag.se, hitta.se, eniro.se, ratsit.se, merinfo.se,
  bolagsfakta.se, proff.se. All COMMERCIAL (not authorities) → ToS forbid productizing; B2B
  switchboard numbers / org-level contacts are lower-risk; scraping personal name+email+phone
  carries GDPR risk. Use curl_cffi / Botasaurus for WAF (per local FRIA_METODER_KATALOG).
- **Vehicle registration:** Transportstyrelsen Vägtrafikregistret.
  - Open API portal (PDM, free, limited datasets): https://tsopendata.portal.azure-api.net/
  - BULK by-vehicle/owner: paid file delivery to secure FTP ("Köp adressuppgifter eller fordonsdata").
  - Reseller APIs: biluppgifter.se (apidocs.biluppgifter.se), merinfo (owner→fleet).
- **NER model:** `KB/bert-base-swedish-cased-ner` (National Library of Sweden) — best Swedish NER.
  spaCy: `sv_core_news_lg`. Nordic combo: `NbAiLab/nbailab-base-ner-scandi`.

## NORWAY (NO) — confidence: VERIFIED

- **Company registry:** Brønnøysundregistrene — Enhetsregisteret (CCR) + Foretaksregisteret.
  Base: `https://data.brreg.no/enhetsregisteret/api`. Licence NLOD 2.0, FREE.
- **Registry access (open, no key):**
  - Full bulk download, rebuilt nightly ~05:00:
    - Entities: `/api/enheter/lastned` (JSON), `/lastned/csv`, `/lastned/regneark` (xlsx)
    - Sub-entities: `/api/underenheter/lastned` (+csv/regneark)
  - Search/single lookup + incremental updates supported.
  - data.norge.no dataset pages mirror these.
- **Directors + UBO:**
  - Roles bulk: `/api/roller/totalbestand` (zipped JSON) — board/directors per entity, FREE.
  - With personal ID numbers: `/autorisert-api/roller/totalbestand` — requires **Maskinporten** auth.
  - UBO ("reelle rettighetshavere") register run by Brønnøysund — phased public access.
- **Annual financial filings:** Regnskapsregisteret (annual accounts) via Brønnøysund;
  accounts/key figures available; some figures exposed through the API / Forvalt-type resellers.
- **Contact directories (legal):** proff.no, gulesider.no, 1881.no, purehelp.no. Commercial ToS.
  Org-level B2B contacts lower-risk; personal data GDPR-sensitive.
- **Vehicle registration:** Statens vegvesen — **Autosys Kjøretøy API**
  (https://autosys-kjoretoy-api.atlas.vegvesen.no/). Technical single-lookup API: anyone can apply
  for an API key, max 50,000 calls/key/day, returns full technical data but **NO owner info**.
  Reg-nr/chassis treated as personal data → legal-basis requirement; bulk owner data NOT open.
  Traffic/road open data: https://dataut.vegvesen.no (separate, not vehicle-owner).
- **NER model:** `NbAiLab/nb-bert-base-ner` (Bokmål) / `NbAiLab/nbailab-base-ner-scandi`.
  spaCy: `nb_core_news_lg`.

## DENMARK (DK) — confidence: VERIFIED

- **Company registry:** CVR (Det Centrale Virksomhedsregister), Erhvervsstyrelsen.
  Public UI: https://datacvr.virk.dk (free, full English, annual reports inline, no account).
  ~2.2M companies, ~1.7M participants (owners/directors/board), ~2.8M production units.
- **Registry access:**
  - REST/UI free for single lookups (rate-limited).
  - BULK = **system-til-system Elasticsearch** access, base `http://distribution.virk.dk/cvr-permanent`.
    FREE but requires registration: email **cvrselvbetjening@erst.dk**, sign a data-conditions
    declaration; then full-dump + scroll API for >3000 results.
    Catalog: https://data.virk.dk/datakatalog/erhvervsstyrelsen/system-til-system-adgang-til-cvr-data
  - One of the world's most open registries; mature OSS clients exist (gronlund/cvrdata etc.).
- **Directors + UBO:** "Deltagere" (participants) = owners/directors/board included in CVR bulk.
  Reelle ejere (UBO) register part of CVR/Erhvervsstyrelsen data.
- **Annual financial filings:** Regnskaber published via CVR/Erhvervsstyrelsen — downloadable
  (XBRL + PDF) per company, also via the system-til-system distribution. Free.
- **Contact directories (legal):** proff.dk, krak.dk, degulesider.dk, virk.dk. CVR itself already
  carries official phone/email where filed. Commercial directories' ToS apply; GDPR for persons.
- **Vehicle registration:** Motorregister (DMR), Motorstyrelsen / SKAT.
  - Public single lookup free (no login): https://motorregister.skat.dk ("Vis køretøj").
  - **DMR B2B Web Service Gateway** (SOAP, cert auth) for authorised parties — sample client
    github.com/skat/dmr-b2b-ws-sample-client-java. ~400 tables.
  - Statistics Denmark (dst.dk) publishes aggregate car-register statistics (monthly).
  - No fully-open bulk owner file; per-vehicle/B2B is the path.
- **NER model:** `da_core_news_lg` (spaCy) or **DaCy large** (centre-for-humanities-computing/DaCy,
  XLM-R/Danish-BERT, SOTA) / `Maltehb/danish-bert-botxo`. Nordic combo: nbailab-base-ner-scandi.

## FINLAND (FI) — confidence: VERIFIED

- **Company registry:** PRH (Patentti- ja rekisterihallitus) Trade Register + YTJ
  (Business Information System, joint PRH/Vero). Open data: https://avoindata.prh.fi/en.
  FREE; attribution required ("mention the original source"). Updated daily.
- **Registry access:**
  - Open data API v3: base `https://avoindata.prh.fi/opendata-ytj-api/v3/` (Swagger/`/schema?lang=en`).
    Services: `ytj` (companies), `krek` (registered notifications), `xbrl` (financial statements).
  - BULK: all valid Trade Register companies as a single compressed JSON file (free, daily).
  - Mirror dataset: https://avoindata.suomi.fi/data/en_GB/dataset/prh-avoin-data
  - Limits: ~300 queries/min total (shared). Excludes private traders (toiminimi) for some sets;
    NO phone/email in company details.
- **Directors + UBO:** Board/representatives via PRH register. Beneficial owners (edunsaajat)
  filed to PRH; public access restricted post-CJEU (legitimate-interest / obliged entities).
- **Annual financial filings:** PRH `xbrl` open-data service — but ONLY iXBRL-filed statements
  (subset). Older/PDF statements ordered per-company. Free for the iXBRL set.
- **Contact directories (legal):** fonecta.fi, finder.fi, suomenyrityshaku.fi, asiakastieto.fi
  (paid). YTJ has no contact fields → enrich elsewhere. GDPR for persons.
- **Vehicle registration:** Traficom open vehicle data — **fully open CSV bulk**.
  Dataset "Open data for vehicles" (ajoneuvojen-avoin-data):
  https://www.avoindata.fi/data/en_GB/dataset/ajoneuvojen-avoin-data — latest material 30.9.2025,
  ~5,255,047 rows, ZIP-CSV (ISO8859-1), 930MB unpacked / ~202MB zipped. Licence **CC BY 4.0**.
  Registration + approval + technical data; NO personal owner (anonymised). Also tieto.traficom.fi.
- **NER model:** `TurkuNLP/bert-base-finnish-cased-v1` (FinBERT) fine-tuned for NER, or
  spaCy `fi_core_news_lg`. (FinBERT outperforms multilingual BERT on Finnish.)

## ICELAND (IS) — confidence: LIKELY (registry partly scrape-only; no open bulk/API confirmed)

- **Company registry:** Fyrirtækjaskrá, run by Skatturinn (Iceland Revenue & Customs).
  Search UI: https://www.skatturinn.is/fyrirtaekjaskra/leit/ (company register + annual-accounts
  register + VAT register). Free basic search, no account; **no open API / bulk download confirmed**
  → effectively scrape-only for systematic collection. Cross-border: e-Justice/BRIS (EEA) +
  RSK kennitala (national ID) as the join key.
- **Directors + UBO:** Raunverulegir eigendur (UBO) register, Act 82/2019, at Skatturinn.
  Beneficial owner of a company **is viewable by looking the company up in fyrirtækjaskrá**
  (https://www.skatturinn.is/fyrirtaekjaskra/raunverulegir-eigendur/) — i.e. web lookup, no public
  open-data feed. Directors via the same company record.
- **Annual financial filings:** Ársreikningaskrá (Annual Accounts Register), Skatturinn.
  Filing deadline 31 Aug for prior year; covers hf./ehf./cooperatives etc. Annual accounts
  obtainable in **electronic form at no cost** ("data from the annual accounts register" →
  shopping cart) https://old.rsk.is/fyrirtaekjaskra/arsreikningaskra/upplysingar-ur-arsreikningaskra/
  — per-document retrieval, not a bulk feed.
- **Contact directories (legal):** ja.is (national phone/business directory), 1819.is. Commercial.
  GDPR-equivalent (Icelandic Data Protection Act + EEA GDPR) applies to persons.
- **Vehicle registration:** Samgöngustofa (Icelandic Transport Authority) — Ökutækjaskrá.
  Lookup via island.is / Samgöngustofa; no confirmed open bulk owner data → treat as
  lookup/scrape + agreement-gated. (UNCERTAIN — needs Samgöngustofa confirmation.)
- **NER model:** No dedicated high-quality Icelandic NER in spaCy. Use HuggingFace
  Icelandic models (e.g. `mideind/IceBERT`-based NER, m3hrdadfi/icelandic-ner-bert variants) or
  the multilingual `nbailab-base-ner-scandi` as fallback. spaCy multilingual `xx_ent_wiki_sm` as
  last resort.

---

### Access-model summary

| Country | Companies bulk | UBO/directors | Financials bulk | Vehicle (owner) | Cost |
|--------|----------------|---------------|-----------------|-----------------|------|
| SE | API + bulkfil (free) | UBO register; directors API | iXBRL weekly (free) | Paid FTP / open subset | Free reg-core |
| NO | lastned JSON/CSV (free) | roller/totalbestand (free); PID=Maskinporten | Regnskapsregisteret | No open owner; tech API key | Free |
| DK | Elasticsearch S2S (free, register email) | participants + reelle ejere in bulk | XBRL/PDF (free) | DMR B2B (cert) / public lookup | Free |
| FI | all-companies JSON (free) | board; edunsaajat restricted | iXBRL subset (free) | Full CC-BY CSV (anonymised) | Free |
| IS | scrape-only (no API) | UBO via web lookup | per-doc free download | lookup/agreement | Free-ish |

### Caveats
- UBO public bulk access across SE/FI/DK/NO tightened after the Nov-2022 CJEU ruling
  (C-37/20, C-601/20): expect legitimate-interest gating for person-level UBO at scale.
- "Free registry core" everywhere; person-level contact/email/phone is the GDPR-sensitive layer —
  prefer official switchboard/registered contacts; treat directory scraping per-ToS.
- Iceland is the weakest for automation: no open API/bulk → Screaming Frog / Sequentum / Botasaurus
  scrape of skatturinn.is + ja.is is the practical path; verify robots/ToS.
