# Country Data: Finland, France, Netherlands, Belgium, Austria, Italy, Spain, Poland

# --- Finland (FI) ---
FI:
  language: fi, sv
  currency: EUR
  companies: ~600K
  registries:
    - name: PRH (Patentti- ja rekisterihallitus)
      url: https://prh.fi
      api: https://avoindata.prh.fi
      data: company_name, business_id (Y-tunnus), legal_form, address, industry, status
      access: Open REST API (free)
      bulk: true
      method: curl_cffi
      refresh: weekly

    - name: Traficom (Vehicle Registry)
      url: https://traficom.fi
      data: vehicle_registration, make, model, year, owner_type
      access: Open API, per-vehicle lookup
      method: curl_cffi

  nlp:
    spacy_model: fi_core_news_lg
    org_number_pattern: '\d{7}[-]\d'
    title_patterns: [Toimitusjohtaja, Hallituksen puheenjohtaja, Talousjohtaja, Myyntijohtaja]

# --- France (FR) ---
FR:
  language: fr
  currency: EUR
  companies: ~10M
  registries:
    - name: SIRENE (INSEE)
      url: https://api.insee.fr
      data: company_name, SIREN/SIRET, NAF_code, legal_form, address, employee_range, founding_date
      access: Open REST API (free registration)
      bulk: true (weekly full download)
      method: curl_cffi
      refresh: weekly

    - name: Infogreffe
      url: https://infogreffe.fr
      data: company_financials, legal_notices, officers
      access: Web portal (some free, most paid)
      method: crawlee

    - name: Pappers (aggregator)
      url: https://pappers.fr
      data: company_profile, financials, officers, documents
      method: crawlee

  nlp:
    spacy_model: fr_core_news_lg
    org_number_pattern: '\d{3}\s?\d{3}\s?\d{3}|SIREN[:\s]*\d{9}'
    title_patterns: [Président, Directeur général, DG, Directeur financier, DAF, Directeur commercial, DRH]

# --- Netherlands (NL) ---
NL:
  language: nl
  currency: EUR
  companies: ~2.5M
  registries:
    - name: KVK (Kamer van Koophandel)
      url: https://kvk.nl
      api: https://api.kvk.nl
      data: company_name, KVK_number, address, SBI_code, legal_form, founding_date, status
      access: Open REST API + bulk download
      method: curl_cffi

    - name: RDW (Vehicle Registry)
      url: https://opendata.rdw.nl
      data: vehicle_registration, make, model, year, fuel_type, mileage
      access: Open data portal (Socrata API)
      bulk: true
      method: curl_cffi

  nlp:
    spacy_model: nl_core_news_lg
    org_number_pattern: '\b\d{8}\b|KvK[:\s]*\d{8}'
    title_patterns: [Directeur, Algemeen directeur, Financieel directeur, Commercieel directeur, HR-directeur]

# --- Belgium (BE) ---
BE:
  language: nl, fr, de
  currency: EUR
  companies: ~1.2M
  registries:
    - name: KBO/BCE (Kruispuntbank)
      url: https://kbopub.economie.fgov.be
      data: company_name, enterprise_number, address, NACE_code, legal_form, founding_date, status
      access: Open data download (CSV/ZIP)
      bulk: true (full monthly export)
      method: curl_cffi
      refresh: monthly

  nlp:
    spacy_model: nl_core_news_lg  # Flemish = Dutch model
    org_number_pattern: '\b\d{4}\.\d{3}\.\d{3}\b|\b\d{10}\b'

# --- Austria (AT) ---
AT:
  language: de
  currency: EUR
  companies: ~700K
  registries:
    - name: Firmenbuch (via Justiz)
      url: https://justizonline.gv.at
      data: company_name, FN_number, legal_form, address, managing_directors, capital
      access: Stateful portal (paid per extract)
      method: sequentum or browser-use
      waf: login-gated
      proxy_tier: Tor
      notes: No open API. Paid per company extract. Use Sequentum for batch processing.

  nlp:
    spacy_model: de_core_news_lg
    org_number_pattern: 'FN\s?\d{1,6}[a-z]?'
    title_patterns: [Geschäftsführer, Vorstand, Prokurist]

# --- Italy (IT) ---
IT:
  language: it
  currency: EUR
  companies: ~5M
  registries:
    - name: Registro Imprese (via InfoCamere)
      url: https://registroimprese.it
      data: company_name, REA_number, VAT (P.IVA), legal_form, address, directors, shareholders
      access: Paid per visura (company extract). Some data via aggregators.
      method: sequentum or browser-use
      waf: stateful portal
      proxy_tier: Tor
      notes: No open bulk API. Paid per lookup. Use Telemaco/InfoCamere portal.

    - name: Atoka (aggregator)
      url: https://atoka.io
      data: company_profile, financials, officers, related_companies
      method: browser-use

  nlp:
    spacy_model: it_core_news_lg
    org_number_pattern: '[A-Z]{2}\s?\d{6,10}|P\.IVA[:\s]*\d{11}'
    title_patterns: [Amministratore, Presidente, Direttore, CFO, Responsabile, Legale rappresentante]

# --- Spain (ES) ---
ES:
  language: es
  currency: EUR
  companies: ~3.3M
  registries:
    - name: Registro Mercantil
      url: https://rmc.es
      data: company_name, CIF/NIF, legal_form, address, directors, financials_basic
      access: Paid per extract. e-REG for digital extracts.
      method: sequentum
      waf: stateful portal
      notes: No open bulk API. Paid per lookup.

    - name: BOE (Boletín Oficial)
      url: https://boe.es
      data: legal_notices, company_registrations, insolvency
      access: Open web search
      method: curl_cffi

  nlp:
    spacy_model: es_core_news_lg
    org_number_pattern: '[A-Z]\d{7,8}|CIF[:\s]*[A-Z]\d{7,8}'
    title_patterns: [Presidente, Director general, Director financiero, Director comercial, Consejero delegado]

# --- Poland (PL) ---
PL:
  language: pl
  currency: PLN
  companies: ~2.5M (CEIDG) + ~600K (KRS)
  registries:
    - name: CEIDG (sole proprietorships)
      url: https://ceidg.gov.pl
      data: company_name, owner_name, NIP, REGON, address, PKD_codes, founding_date
      access: Open web portal + API
      method: crawlee

    - name: KRS (companies/partnerships)
      url: https://ekrs.ms.gov.pl
      data: company_name, KRS_number, NIP, legal_form, address, directors, financials
      access: Open web portal (stateful search)
      method: sequentum

  nlp:
    spacy_model: pl_core_news_lg
    org_number_pattern: 'NIP[:\s]*\d{10}|REGON[:\s]*\d{9,14}|KRS[:\s]*\d{10}'

# --- UK (United Kingdom) ---
UK:
  language: en
  currency: GBP
  companies: ~5M
  registries:
    - name: Companies House
      url: https://find-and-update.company-information.service.gov.uk
      api: https://api.company-information.service.gov.uk
      data: company_name, company_number, address, SIC_code, company_type, directors, PSCs, filing_history
      access: Open REST API (free API key)
      bulk: true (full register + daily snapshots)
      method: curl_cffi
      refresh: daily
      notes: Gold standard. Full register, directors, PSCs all free.

  nlp:
    spacy_model: en_core_web_lg
    org_number_pattern: '\b\d{8}\b|Company number[:\s]*\d{8}'
    title_patterns: [Director, Managing Director, CEO, CFO, Secretary, Chairman]

# --- Ireland (IE) ---
IE:
  language: en
  currency: EUR
  companies: ~250K
  registries:
    - name: CRO (Companies Registration Office)
      url: https://cro.ie
      data: company_name, company_number, address, NACE_code, company_type, directors, filing_history
      access: Open API + bulk download
      method: curl_cffi
      notes: Companies House equivalent for Ireland.

# --- Switzerland (CH) ---
CH:
  language: de, fr, it
  currency: CHF
  companies: ~650K
  registries:
    - name: ZEFIX (Zentraler Firmenindex)
      url: https://zefix.ch
      data: company_name, UID/CHE_number, legal_form, address, status, purpose
      access: Open web search + limited API
      method: crawlee
      notes: Free company search. Full extracts paid via canton registries.

# --- Czech Republic (CZ) ---
CZ:
  language: cs
  currency: CZK
  companies: ~500K
  registries:
    - name: Obchodní rejstřík (Justice.cz)
      url: https://or.justice.cz
      data: company_name, IČO, legal_form, address, directors, financials
      access: Open web portal
      method: crawlee
      notes: Free access, but stateful portal. No bulk API.

# --- Hungary (HU) ---
HU:
  language: hu
  currency: HUF
  companies: ~500K
  registries:
    - name: e-cégjegyzék
      url: https://e-cegjegyzek.gov.hu
      data: company_name, company_number, legal_form, address, directors, financials
      access: Stateful portal (wizard-based)
      method: sequentum or browser-use
      waf: stateful wizard
      notes: No open API. Multi-step wizard. Sequentum visual matching ideal.

# --- Portugal (PT) ---
PT:
  language: pt
  currency: EUR
  companies: ~1.3M
  registries:
    - name: RACIUS (via MJ)
      data: company_name, NIPC/NIF, legal_form, address, directors, financials_basic
      access: Paid per extract
      method: sequentum
      notes: No open bulk API. Paid per lookup.

# --- Iceland (IS) ---
IS:
  language: is
  currency: ISK
  companies: ~60K
  registries:
    - name: RSK (Skatturinn)
      url: https://rsk.is
      data: company_name, kennitala, legal_form, address, VAT_number
      access: Web portal (some API)
      method: crawlee
      notes: Small market, free access for basic data.
