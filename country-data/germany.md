# Country Data: Germany (DE)
# Verified source inventory for German company data
# Language: de | Currency: EUR | Companies: ~3.5M

registries:
  - name: Handelsregister (Commercial Register)
    url: https://handelsregister.de
    api_base: null  # No open API — portal-based lookup
    data_available:
      - company_name, legal_form (GmbH, AG, OHG, KG, etc.)
      - HR_number (Handelsregisternummer)
      - registered_address, registered_capital
      - managing_directors (Geschäftsführer)
      - procuration (Prokura)
      - incorporation_date, amendments
    access: Stateful web portal (login required for details)
    format: HTML, PDF (Handelsregisterauszug)
    rate_limit: 30 searches/day (per IP, stricter with login)
    bulk: false
    waf: CF + login-gated
    method: sequentum or browser-use + cloakbrowser
    proxy_tier: residential/Tor
    refresh: monthly
    notes: |
      THE hardest market. No open API. Stateful portal with search→result→detail flow.
      Sequentum visual matching is the reliable approach.
      Consider Unternehmensregister as alternative aggregator.

  - name: Unternehmensregister (Company Register)
    url: https://unternehmensregister.de
    data_available:
      - annual_financial_statements (Jahresabschluss)
      - company_name, HR_number
      - management_board_members
    access: Web portal (free search, paid documents)
    format: HTML (search), PDF (documents)
    bulk: false
    method: crawlee (search) + unstructured (PDF)
    notes: |
      Bundesanzeiger is the parent platform.
      Financial statements are the key data here.

  - name: Bundesanzeiger (Federal Gazette)
    url: https://bundesanzeiger.de
    data_available:
      - annual_financial_statements (full)
      - company_announcements
      - insolvency_notices
    access: Web portal, some free, some paid
    method: sequentum

  - name: GENESIS-Online (Federal Statistical Office)
    url: https://www-genesis.destatis.de
    data_available:
      - company_statistics_by_industry
      - employee_statistics
      - revenue_statistics (aggregated, not per-company)
    access: Open API

  - name: GLEIF (Global LEI — cross-border)
    url: https://api.gleif.org/api/v1/lei-records
    data_available:
      - LEI_number
      - company_name, legal_form
      - registered_address, country
      - parent_company (direct and ultimate)
    access: Open REST API (free, no auth)
    bulk: true (full LEI dataset downloadable)
    notes: |
      Key for cross-border company linking.
      German companies with LEI = about 50,000 (larger/mid-size).
      Use LEI as golden key to link DE company to same company in other markets.

  - name: Northdata (aggregator)
    url: https://northdata.de
    data_available:
      - company_profile, financials, officers
      - related_companies, shareholdings
    access: Freemium web portal
    method: browser-use

nlp:
  language: de
  spacy_model: de_core_news_lg
  title_patterns:
    - Geschäftsführer, Geschäftsführerin, GF
    - Vorstand, Vorstandsvorsitzender, Vorstandsmitglied
    - Aufsichtsrat, Aufsichtsratsvorsitzender
    - Prokurist, Prokuristin
    - Leiter, Abteilungsleiter, Bereichsleiter
    - Personalleiter, Vertriebsleiter, Marketingleiter
  org_number_pattern: '(HR[B|A]\s?\d{1,6}|HRA\s?\d{1,6}|HRB\s?\d{1,6})'
  phone_pattern: '(\+49\s?\d{1,4}\s?\d{3,10}|\d{4,5}\s?\d{4,8})'

vehicle:
  registration_pattern: '[A-Z]{1,3}-[A-Z]{1,2}\s?\d{1,4}'
  registry: Kraftfahrt-Bundesamt (KBA)
  notes: |
    German vehicle data NOT publicly available per vehicle — EU GDPR ruling 2023.
    Aggregated statistics only from KBA.
    Vehicle data for Germany: very limited for this platform.
