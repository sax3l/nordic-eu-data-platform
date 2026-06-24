# Country Data: Finland, Iceland, Ireland, Switzerland, Portugal

# --- Finland (FI) ---
FI:
  language: fi, sv
  currency: EUR
  companies: ~600K
  registries:
    - name: PRH Patentti- ja rekisterihallitus
      url: https://prh.fi
      api: https://avoindata.prh.fi
      data: company_name, business_id (Y-tunnus 7 digits-hyphen-1 check digit), legal_form (Oy, Ay, Ky, etc.), address, industry, status, founding_date
      access: Open REST API (free, no auth)
      format: JSON
      bulk: true
      method: curl_cffi
      proxy_tier: none
      refresh: weekly

    - name: Suomen Asiakastieto (commercial)
      url: https://asiakastieto.fi
      data: company_profile, credit_rating, financials, board_members, ownership
      access: Paid (commercial)
      method: n/a (paid source)

    - name: Traficom Vehicle Registry
      url: https://traficom.fi
      api: https://trafi2.stat.fi (aggregated stats)
      data: vehicle_registration (rekisteritunnus), make, model, year, fuel_type, owner_type
      access: Open API, per-vehicle lookup
      method: curl_cffi
      refresh: daily

    - name: Finder.fi (aggregator)
      url: https://finder.fi
      data: company_profile, financials, contacts
      method: crawlee

  nlp:
    spacy_model: fi_core_news_lg
    gliner_fallback: true
    org_number_pattern: '\d{7}[-]\d'
    title_patterns:
      - Toimitusjohtaja, TJ, Hallituksen puheenjohtaja
      - Talousjohtaja, CFO, Myyntijohtaja
      - Markkinointijohtaja, Henkilöstöjohtaja, Tietohallintojohtaja
      - Kehitysjohtaja, Teknologiajohtaja, CTO
    phone_pattern: '(0\d{1,2}\s?\d{6,8}|\+358\s?\d{1,2}\s?\d{6,8})'

  vehicle:
    registration_pattern: '[A-Z]{2,3}[-]\d{1,3}'
    notes: Finnish plates format AAA-111. Traficom provides API access.

# --- Iceland (IS) ---
IS:
  language: is
  currency: ISK
  companies: ~60K
  registries:
    - name: RSK Skatturinn (Companies Registry)
      url: https://rsk.is
      data: company_name, kennitala (10 digits), legal_form (ehf, hf, sf, etc.), address, VAT_number, status
      access: Web portal + limited API
      method: crawlee
      proxy_tier: self_hosted
      refresh: monthly

    - name: Creditinfo Iceland
      url: https://creditinfo.is
      data: company_profile, credit_rating, financials
      access: Paid (commercial)
      method: n/a

  nlp:
    spacy_model: en_core_web_lg  # No Icelandic model — use English + GLiNER
    gliner_fallback: true
    org_number_pattern: '\b\d{6}[-]\d{4}\b|kennitala[:\s]*\d{10}'
    title_patterns:
      - Forstjóri, Framkvæmdastjóri, Stjórnarformaður
      - Fjármálastjóri, Sölustjóri, Markaðsstjóri
      - Tæknistjóri, Mannauðsstjóri
    notes: Smallest Nordic market. ~60K companies. English widely used in business.

# --- Ireland (IE) ---
IE:
  language: en, ga
  currency: EUR
  companies: ~250K
  registries:
    - name: CRO Companies Registration Office
      url: https://cro.ie
      api: https://core.cro.ie/api (limited)
      data: company_name, company_number (6 digits), address, NACE_code, company_type (LTD, DAC, CLG, etc.), status, incorporation_date, directors, charges/mortgages
      access: Open API + bulk data downloads
      format: JSON, XML
      bulk: true
      method: curl_cffi
      proxy_tier: none
      refresh: weekly

    - name: Solocheck (aggregator)
      url: https://solocheck.ie
      data: company_profile, directors, documents
      method: crawlee

  nlp:
    spacy_model: en_core_web_lg
    org_number_pattern: '\b\d{6}\b|Company Number[:\s]*\d{6}'

# --- Switzerland (CH) ---
CH:
  language: de, fr, it
  currency: CHF
  companies: ~650K
  registries:
    - name: ZEFIX Zentraler Firmenindex
      url: https://zefix.ch
      api: https://zefix.admin.ch/webservices (SOAP)
      data: company_name, UID/CHE_number (CHE-xxx.xxx.xxx), legal_form (AG, GmbH, etc.), registered_office, status, purpose
      access: Open web search + limited SOAP API
      method: crawlee + XML parser
      proxy_tier: self_hosted
      refresh: monthly

    - name: Moneyhouse (aggregator)
      url: https://moneyhouse.ch
      data: company_profile, directors, financials_basic
      method: crawlee

    - name: Swiss Register of Commerce (kantonal)
      data: full_register_extracts, directors, capital
      access: Paid per canton extract
      method: n/a (paid)
      notes: Full commercial register extracts are paid per canton.

  nlp:
    spacy_model: de_core_news_lg  # German primary, also fr/it
    org_number_pattern: 'CHE[-]\d{3}[.]\d{3}[.]\d{3}|UID[:\s]*CHE[-]\d{3}[.]\d{3}[.]\d{3}'
    title_patterns:
      - Geschäftsführer, Verwaltungsrat, VR-Präsident
      - Direktor, CFO, CEO, Leiter

# --- Portugal (PT) ---
PT:
  language: pt
  currency: EUR
  companies: ~1.3M
  registries:
    - name: RACIUS (Registo Comercial)
      url: https://racius.com (aggregator, easier access)
      data: company_name, NIPC/NIF (9 digits), legal_form (Lda, SA, etc.), address, CAE_code, status, founding_date
      access: Web portal (paid per extract from official registry, free from aggregators)
      method: crawlee (aggregators)
      notes: No open API from official registry. Use aggregators like racius.com, infoempresas.com.pt.

    - name: InfoEmpresas (aggregator)
      url: https://infoempresas.com.pt
      data: company_profile, financials_basic
      method: crawlee

  nlp:
    spacy_model: pt_core_news_lg
    org_number_pattern: '\b\d{9}\b|NIPC[:\s]*\d{9}|NIF[:\s]*\d{9}'
    title_patterns:
      - Presidente, Diretor, Diretor-Geral, Administrador
      - Diretor Financeiro, CFO, Diretor Comercial
      - Diretor de Marketing, Diretor de RH, Diretor de TI
