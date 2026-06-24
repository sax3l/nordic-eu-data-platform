# Country Data: UK + France + Netherlands (summary)

# --- United Kingdom ---
UK:
  language: en
  currency: GBP
  companies: ~5M
  registries:
    - name: Companies House
      url: https://find-and-update.company-information.service.gov.uk
      api_base: https://api.company-information.service.gov.uk
      data_available:
        - company_name, company_number (8 digits)
        - registered_office_address
        - SIC_code, company_type
        - directors, secretaries, PSCs (persons of significant control)
        - filing_history, annual_accounts
        - incorporation_date, status
      access: Open REST API (free, API key registration required)
      format: JSON
      bulk: true (full register downloadable)
      method: curl_cffi (API key from env)
      refresh: weekly
      notes: |
        Companies House is the gold standard for open company data.
        Full register, directors, PSCs all free.
        API key: free registration at developer.company-information.service.gov.uk.

# --- France ---
FR:
  language: fr
  currency: EUR
  companies: ~10M (including micro-enterprises)
  registries:
    - name: SIRENE (INSEE)
      url: https://api.insee.fr
      api_base: https://api.insee.fr/entreprises/sirene/V3
      data_available:
        - company_name, SIREN (9 digits), SIRET (14 digits)
        - NAF_code, legal_form
        - registered_address
        - employee_range, founding_date
        - status
      access: Open REST API (free, registration required)
      format: JSON
      bulk: true (full SIRENE database downloadable weekly)
      method: curl_cffi
      refresh: weekly
      notes: |
        SIRENE is the largest open company register in Europe (10M+ entities).
        Bulk download available weekly.
        API token from api.insee.fr (free registration).

    - name: Infogreffe
      url: https://infogreffe.fr
      data_available:
        - company_financials, legal_notices
        - officers, shareholders
      access: Web portal (some free, most paid)
      method: crawlee

    - name: Pappers (aggregator)
      url: https://pappers.fr
      data_available:
        - company_profile, financials, officers
        - legal_documents
      access: Web scraping (free tier)
      method: crawlee

# --- Netherlands ---
NL:
  language: nl
  currency: EUR
  companies: ~2.5M
  registries:
    - name: KVK (Kamer van Koophandel)
      url: https://kvk.nl
      api_base: https://api.kvk.nl
      data_available:
        - company_name, KVK_number (8 digits)
        - registered_address, city
        - SBI_code, legal_form
        - founding_date, status
      access: Open REST API (free, registration required) + bulk download
      format: JSON
      bulk: true
      method: curl_cffi
      notes: |
        KVK provides open API + bulk download.
        Company officers available but at cost.

    - name: RDW (Vehicle Registry)
      url: https://rdw.nl
      api_base: https://opendata.rdw.nl
      data_available:
        - vehicle_registration, VIN
        - make, model, year, fuel_type
        - mileage, registration_date
      access: Open data portal (Socrata API)
      format: JSON, CSV
      bulk: true (full vehicle register, anonymized)
      notes: |
        RDW is one of the best open vehicle registries in Europe.
        Full vehicle database downloadable.
        However: personal name data is NOT public (GDPR).
        Company-owned vehicle data available via KVK cross-reference.

# --- Other markets (summary) ---
FI:
  registry: PRH (Patentti- ja rekisterihallitus) — https://prh.fi
  api: Open API at https://avoindata.prh.fi
  bulk: true
  companies: ~600K
  notes: Finnish Business ID (Y-tunnus), full register open.

BE:
  registry: KBO/BCE (Kruispuntbank van Ondernemingen)
  url: https://kbopub.economie.fgov.be
  api: Open data download
  bulk: true
  companies: ~1.2M

AT:
  registry: Firmenbuch (via Justiz)
  url: https://justizonline.gv.at
  access: Portal-based, paid per extract
  method: browser-use or sequentum
  notes: No open API. Requires stateful portal navigation.

IT:
  registry: Registro Imprese (via InfoCamere)
  access: Paid per visura (company extract)
  method: sequentum or browser-use
  notes: No open API. Paid per lookup. Use aggregators.

ES:
  registry: Registro Mercantil
  access: Paid per extract
  method: sequentum
  notes: CIRCE for new registrations, but historical = paid.

PL:
  registry: CEIDG + KRS
  url: https://ceidg.gov.pl | https://ekrs.ms.gov.pl
  access: Open web portal, limited API
  method: crawlee (CEIDG) + sequentum (KRS)

CZ:
  registry: Obchodní rejstřík (via Justice.cz)
  url: https://or.justice.cz
  access: Open web portal
  method: crawlee

HU:
  registry: e-cégjegyzék
  url: https://e-cegjegyzek.gov.hu
  access: Portal-based, stateful wizard
  method: sequentum or browser-use

PT:
  registry: RACIUS
  access: Paid per extract
  method: sequentum

IE:
  registry: CRO (Companies Registration Office)
  url: https://cro.ie
  access: Open API + bulk download
  method: curl_cffi

IS:
  registry: Skatturinn (RSK)
  access: Web portal
  method: crawlee
  companies: ~60K

CH:
  registry: ZEFIX (Zentraler Firmenindex)
  url: https://zefix.ch
  access: Open web search, limited API
  method: crawlee
