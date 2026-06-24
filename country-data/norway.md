# Country Data: Norway (NO)
# Language: no | Currency: NOK | Companies: ~900K

registries:
  - name: Brønnøysundregistrene (Brreg)
    url: https://brreg.no
    api_base: https://data.brreg.no/enhetsregisteret/api
    data_available:
      - company_name, legal_form (AS, ASA, DA, etc.)
      - org_number (organisasjonsnummer, 9 digits)
      - registered_address, postal_code, city
      - industry_code (NACE)
      - status (active, inactive)
      - founding_date
      - number_of_employees
      - board_members, general_manager (daglig leder)
      - financial_statements (årsregnskap)
    access: Open REST API (free, no auth)
    format: JSON
    rate_limit: 1000 requests/hour
    bulk: true (full register downloadable)
    method: curl_cffi
    refresh: weekly
    notes: |
      Norway matches Denmark for open data quality.
      Full company register + board members via API.
      Financial statements available via separate endpoint.

  - name: Statens vegvesen (Vehicle Registry)
    url: https://vegvesen.no
    api_base: null
    data_available:
      - vehicle_registration
      - VIN
      - make, model, year, fuel_type
      - owner_info (limited)
    access: Per-vehicle lookup (API or web)
    method: crawlee
    refresh: daily

  - name: Proff Forvalt (aggregator)
    url: https://proff.no
    data_available:
      - company_profile, financial_ratings
      - board_members, ownership
      - credit_rating
    access: Web scraping
    method: curl_cffi

nlp:
  language: nb
  spacy_model: nb_core_news_lg
  title_patterns:
    - Daglig leder, Administrerende direktør, Adm. dir
    - Styreleder, Styreformann, Styremedlem
    - Økonomisjef, CFO, Regnskapssjef
    - Salgssjef, Markedsdirektør, Markedssjef
    - IT-sjef, CIO, CTO
    - HR-sjef, Personalsjef
  org_number_pattern: '\b\d{3}\s?\d{3}\s?\d{3}\b|Org\.\s*nr\.?\s*\d{9}'
