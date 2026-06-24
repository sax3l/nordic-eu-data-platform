# Country Data: Denmark (DK)
# Language: da | Currency: DKK | Companies: ~700K

registries:
  - name: CVR (Centrale Virksomhedsregister)
    url: https://datacvr.virk.dk
    api_base: https://cvrapi.dk/api (unofficial, faster)
    data_available:
      - company_name, legal_form (ApS, A/S, IVS, etc.)
      - CVR_number (8 digits)
      - registered_address, postal_code, city
      - industry_code (branchekode)
      - status (active, inactive)
      - founding_date
      - employees_range
      - email, phone (if registered)
    access: Open REST API (free, no auth)
    format: JSON
    rate_limit: 100 requests/hour (official), unlimited (cvrapi.dk)
    bulk: true (full CVR register downloadable)
    method: curl_cffi (direct API)
    refresh: weekly
    notes: |
      Denmark has possibly the BEST open company data in Europe.
      Full register downloadable. cvrapi.dk provides faster access.
      Also available via Elasticsearch endpoint.

  - name: Virk Data
    url: https://datacvr.virk.dk/data
    api_base: https://datacvr.virk.dk/api
    data_available:
      - full_company_record
      - ownership (reelle ejere)
      - financial_statements (årsrapport)
      - branch_offices
    access: Open API + Elasticsearch
    format: JSON
    bulk: true
    method: curl_cffi

  - name: CVR Elasticsearch
    url: https://datacvr.virk.dk/data/elastic
    data_available:
      - full_bulk_export (all companies at once)
    access: Elasticsearch endpoint (free)
    format: JSON (bulk)
    notes: |
      Can dump entire company register in one query.
      Use for weekly full refresh.

nlp:
  language: da
  spacy_model: da_core_news_lg
  title_patterns:
    - Direktør, Adm. direktør, Administrerende direktør
    - Bestyrelsesformand, Bestyrelsesmedlem
    - Økonomichef, CFO, Økonomidirektør
    - Salgschef, Salgsdirektør, Marketingchef
    - IT-chef, CIO, CTO
    - HR-chef, Personalechef
  org_number_pattern: '\b\d{8}\b|CVR[:\s]*\d{8}'
