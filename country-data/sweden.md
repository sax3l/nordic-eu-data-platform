# Country Data: Sweden (SE)
# Verified source inventory for Swedish company data
# Language: sv | Currency: SEK | Companies: ~1.2M

registries:
  - name: Bolagsverket (Swedish Companies Registration Office)
    url: https://bolagsverket.se
    api_base: https://api.bolagsverket.se/naringsliv/v1
    data_available:
      - company_name, legal_form, status
      - org_number (organisationsnummer, 10 digits)
      - registered_address, postal_code, city
      - board_members, CEO (verkställande direktör)
      - fiscal_year, annual_report_filed
      - incorporation_date
    access: Open REST API (free, no auth)
    format: JSON
    rate_limit: 60 requests/minute
    bulk: true  # Full company register downloadable
    waf: none
    method: curl_cffi (direct API)
    refresh: weekly
    notes: |
      Primary source for all Swedish companies.
      API provides basic company data + board members.
      For full annual reports: separate download via PDF.

  - name: Transportstyrelsen (Swedish Transport Agency)
    url: https://transportstyrelsen.se
    api_base: https://fordon-info.transportstyrelsen.se
    data_available:
      - vehicle_registration (registreringsnummer)
      - VIN (chassinummer)
      - make, model, year, fuel_type
      - owner_type (private/company)
      - status (active, deregistered)
    access: Per-vehicle lookup (no bulk API)
    format: HTML/JSON (parts)
    rate_limit: 30 requests/minute
    bulk: false
    waf: soft
    method: crawlee (Playwright)
    proxy_tier: self-hosted
    refresh: daily (incremental)

  - name: Skatteverket (Swedish Tax Agency)
    url: https://skatteverket.se
    data_available:
      - tax_registration, VAT_number
      - employer_registration
      - annual_tax_filings (limited public)
    access: Limited public API + PDF downloads
    format: PDF
    bulk: false
    method: unstructured (PDF parsing)

  - name: Allabolag.se (aggregator)
    url: https://allabolag.se
    data_available:
      - company_profile, revenue, employees
      - board_members, ownership
      - credit_rating
      - annual_reports (PDF)
    access: Web scraping
    format: HTML
    bulk: false
    waf: soft
    method: crawlee
    proxy_tier: self-hosted
    refresh: monthly

  - name: Merinfo.se (aggregator)
    url: https://merinfo.se
    data_available:
      - company_profile, contact_info
      - vehicle_ownership (company fleets)
      - person_info (limited)
    access: Web scraping
    format: HTML
    bulk: false
    waf: soft
    method: curl_cffi
    refresh: monthly

  - name: Ratsit.se (aggregator)
    url: https://ratsit.se
    data_available:
      - company_profile, board_members
      - person_info, income (public)
    access: Web scraping
    format: HTML
    bulk: false
    waf: soft
    method: curl_cffi

nlp:
  language: sv
  spacy_model: sv_core_news_lg
  gliner_fallback: true
  title_patterns:
    - VD, Verkställande direktör, vVD
    - Styrelseordförande, Styrelseledamot, Styrelsesuppleant
    - Ekonomichef, CFO, Ekonomiansvarig
    - Marknadschef, Försäljningschef, Säljchef
    - IT-chef, CIO, CTO
    - Personalchef, HR-chef
    - Produktionschef, Teknisk chef
    - Kvalitetschef, Inköpschef
  org_number_pattern: '\d{6}[-]\d{4}'
  phone_pattern: '(0\d{1,3}[-]\d{5,8}|\+46\s?\d{1,3}\s?\d{5,8})'
  email_pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

vehicle:
  registration_pattern: '[A-Z]{3}\s?\d{2}[A-Z0-9]'
  vin_pattern: '[A-HJ-NPR-Z0-9]{17}'
  registry: Transportstyrelsen
  notes: |
    Swedish plates: ABC 123 or ABC 12A format.
    Company-owned vehicles searchable via merinfo.se by org number.
    No bulk vehicle download — per-vehicle lookup only.
