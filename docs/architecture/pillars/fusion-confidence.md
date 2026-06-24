# Architecture: Cross-Source / Cross-Border Data Fusion + Confidence Layer

**Component:** `fusion-confidence`
**Role in platform:** The trust engine. Every other component (the 85+ scrapers, Screaming Frog crawls, Sequentum/UiPath/Ranorex jobs, registry pulls, cheap-API confirms) emits *claims*. This layer turns a stream of noisy, contradictory, multi-language claims into **one canonical record per real-world entity, with a defensible confidence number and full provenance on every field.**
**Last updated:** 2026-06-24
**Builds on:** `WEB_EXTRACTION_NER_PIPELINE.md` (extraction + validation primitives), `architecture_patterns_reference.md` (fan-out/dedup patterns), `COMPETITIVE_ANALYSIS_APOLLO_COGNISM_LINKEDIN_2026.md` (the honesty gap we exploit), `OPEN_SOURCE_TOOLS_CATALOG.md` (RapidFuzz, dedupe, jellyfish).

---

## 0. Why this layer is the moat

The competitive analysis is blunt: **Apollo claims 97% email accuracy and delivers 65-70%. Cognism's 98% applies to 2.3% of its database.** Both inflate. Both expose a single opaque "verified" badge that conflates "the mail server didn't reject" with "this human reads this inbox."

Our wedge is **calibrated honesty**: we never emit a number we cannot defend. A field that says `confidence: 0.83` must mean that, historically, fields scored 0.83 are correct ~83% of the time (calibration, measured against ground truth, re-checked quarterly). We ship the *evidence* (which sources said what, when) alongside the number. This is simultaneously the EU compliance story (provenance = Art. 14 + lawful-basis auditability) and the sales story ("honest about accuracy" per the competitive doc's GTM recommendation).

The fusion layer also raises **speed**, not just trust. Goal #7 from the platform spec: *combine sources so a cheap API confirms a scrape and the slow scrape is skipped.* The fusion layer is where that decision is made — see §6 (Skip-the-scrape arbitration).

---

## 1. Canonical Entity Model (20 countries)

Six entity types. Each has a stable internal surrogate key (`*_uid`, a UUIDv7 so keys are time-sortable) plus one or more **natural keys** from source registries. We never overload one ID scheme as the primary key because schemes are jurisdiction-specific and none is global.

### 1.1 Company

```
company:
  company_uid            : uuid          # internal surrogate, immutable
  lei                    : char(20)?     # GLEIF Legal Entity Identifier — THE cross-border key
  reg_ids                : RegId[]        # one per registry the entity appears in
  primary_country        : iso3166_2      # SE, NO, DK, FI, DE, FR, GB, NL, ...
  legal_name             : text
  legal_name_normalized  : text           # post §3.3 normalization
  legal_form             : enum           # AB, ASA, A/S, Oy, GmbH, SA, SARL, Ltd, PLC, BV, ...
  status                 : enum           # active, dissolved, merged, bankrupt
  vat_id                 : text?          # EU VIES key, cross-border-ish
  domains                : Website[]
  registered_address     : Address
  sni_nace               : text?          # industry code (SNI=SE, NACE=EU)
  size_band              : enum?          # employees + turnover buckets
  parent_company_uid     : uuid?          # corporate hierarchy edge
  _provenance            : FieldProvenance  # see §7
```

`RegId` is the polymorphic national-ID carrier. **This is the heart of cross-border keying.**

```
RegId:
  scheme   : enum   # SE_ORGNR | NO_ORGNR | DK_CVR | FI_YTUNNUS | GB_CRN |
                    # DE_HRB | DE_HRA | FR_SIREN | FR_SIRET | NL_KVK |
                    # IE_CRO | BE_KBO | AT_FB | CH_UID | ES_NIF | IT_CF |
                    # PL_KRS | PT_NIPC | LU_RCS | IS_KENNITALA
  value    : text   # raw, as issued
  value_norm : text # checksum-validated, canonical format (see table)
  issuer   : text   # Bolagsverket, Brønnøysund, CVR, PRH, Companies House, ...
  verified_at : timestamptz
```

**National ID scheme table** (the 20-country keying spec):

| Country | Scheme | Format / checksum | Free source |
|---|---|---|---|
| Sweden | SE_ORGNR | 10 digit, Luhn (last digit) | Bolagsverket iXBRL bulk + API |
| Norway | NO_ORGNR | 9 digit, mod-11 | Brønnøysund (brreg) open API |
| Denmark | DK_CVR | 8 digit, mod-11 | CVR / Virk open API |
| Finland | FI_YTUNNUS | 7 digit + check | PRH/YTJ open API |
| Iceland | IS_KENNITALA | 10 digit, mod-11 | RSK |
| UK | GB_CRN | 8 char (2 alpha + 6 num regional) | Companies House free API |
| Germany | DE_HRB/HRA | court prefix + number (no global checksum) | Handelsregister / OpenCorporates |
| France | FR_SIREN/SIRET | SIREN 9 (Luhn), SIRET=SIREN+5 | INSEE SIRENE open data |
| Netherlands | NL_KVK | 8 digit | KvK API (freemium) |
| Belgium | BE_KBO | 10 digit, mod-97 | KBO/BCE open data |
| Ireland | IE_CRO | up to 6 digit | CRO |
| Austria | AT_FB | "FN" + number + check letter | Firmenbuch |
| Switzerland | CH_UID | CHE + 9 digit + mod-11 | UID register / Zefix |
| Spain | ES_NIF | letter + 7 num + control | Registro Mercantil |
| Italy | IT_CF/PIVA | 11 digit VAT / 16 char CF | Registro Imprese |
| Poland | PL_KRS/NIP | KRS 10 digit / NIP mod-11 | KRS / GUS REGON |
| Portugal | PT_NIPC | 9 digit, mod-11 | RNPC |
| Luxembourg | LU_RCS | "B" + number | LBR |
| **Cross-border** | **LEI** | 20 char ISO 17442, mod-97-10 | **GLEIF Golden Copy (free, daily)** |
| **EU VAT** | VAT | country prefix + body | VIES validation service |

**Keying strategy.** Within a country, the national reg-id (checksum-validated, canonicalized) is the deterministic merge key — two claims with the same `SE_ORGNR` after Luhn validation are the same company, period. **Across borders**, LEI is the bridge: GLEIF's Golden Copy maps `LEI ↔ national reg-id` for ~2.5M entities and is free/daily. Where LEI is absent (most SMEs), cross-border links fall back to probabilistic resolution (§3) over `legal_name_normalized + registered_address + domain + VAT`. VAT/VIES gives a second cross-border anchor for EU entities.

### 1.2 Person, Role, Contact-Point, Website, Vehicle

```
person:
  person_uid          : uuid
  full_name           : text
  full_name_normalized: text     # diacritic-folded, see §3.2
  given / family      : text
  linkedin_urn        : text?     # stable LinkedIn member key when resolvable
  national_person_id  : text?     # only where lawful (e.g. NOT SE personnummer for marketing)
  _provenance         : FieldProvenance

role:                            # the time-bounded edge person↔company
  role_uid     : uuid
  person_uid   : uuid
  company_uid  : uuid
  title_raw    : text
  title_norm   : enum            # CEO, CFO, VP_SALES, BESLUTSFATTARE, ...
  seniority    : enum            # c_level, vp, director, manager, ic
  valid_from / valid_to : date?  # supports freshness/decay (§4)
  is_current   : bool

contact_point:                   # email OR phone, polymorphic
  cp_uid       : uuid
  owner_uid    : uuid            # person_uid or company_uid
  kind         : enum            # email | phone_mobile | phone_direct | phone_switchboard
  value_raw    : text
  value_e164   : text?           # phones, libphonenumber-normalized
  value_email  : text?           # lowercased, IDN-normalized
  validation   : ValidationResult # §3.4 / §3.5
  _provenance  : FieldProvenance

website:
  site_uid     : uuid
  url_canonical: text            # scheme+host normalized, www stripped, lowercased
  etld_plus_one: text            # registrable domain (publicsuffix list)
  liveness     : LivenessResult  # §3.6
  cms / tech   : text[]          # from Screaming Frog / Wappalyzer pass

vehicle:                         # Nordic vehicle registries + Blocket/merinfo
  vehicle_uid  : uuid
  vin          : char(17)?       # global key, ISO 3779 check digit
  reg_plate    : text?           # national plate (country-scoped)
  plate_country: iso3166_2
  make/model/year : text
  owner_uid    : uuid?           # company_uid or person_uid (lawful-basis gated)
  _provenance  : FieldProvenance
```

Vehicle keying: **VIN is the global natural key** (17-char, position-9 check digit validates); national plate is country-scoped and mutable (plates get reassigned), so plate is a *weak* key resolved only within `(plate, plate_country, observed_window)`.

---

## 2. Pipeline shape

```
                      claims (many sources, async)
  scrapers ─┐
  ScreamingFrog ─┤
  Sequentum ─┤    ┌────────────┐   ┌──────────────┐   ┌───────────────┐
  UiPath ────┼──▶ │  INGEST &  │──▶│   BLOCKING   │──▶│   PAIRWISE    │
  Ranorex ───┤    │ NORMALIZE  │   │ (cheap keys) │   │  SCORING      │
  registries ┤    │  (§3.1-3.3)│   │   (§3.1)     │   │ (RapidFuzz +  │
  cheap APIs ┘    └────────────┘   └──────────────┘   │  Splink) §3   │
                                                       └──────┬────────┘
                                                              ▼
   ┌────────────┐   ┌───────────────┐   ┌──────────────┐   ┌────────────┐
   │  OUTPUT    │◀──│  CONFIDENCE   │◀──│  FIELD-LEVEL │◀──│  CLUSTER /  │
   │  schema +  │   │  SCORING      │   │  FUSION      │   │  RESOLVE    │
   │  API (§8)  │   │ (agreement,   │   │ (pick value  │   │ (connected  │
   └────────────┘   │  validation,  │   │  per field,  │   │  components,│
                    │  freshness)§5 │   │  §5.4)       │   │  transitive)│
                    └───────────────┘   └──────────────┘   └────────────┘
                            │
                            ▼  feedback: skip-the-scrape arbitration (§6)
                    back to orchestrator
```

---

## 3. Entity resolution at scale

### 3.1 Blocking (so we never do N² comparisons)

Comparing every claim to every claim is O(N²) — fatal at 10M+ entities. **Blocking** generates cheap candidate keys; only claims sharing a block are scored. We use *multiple* blocking keys (union of candidates) so a typo in one field doesn't lose the match:

```python
def blocking_keys(rec):
    keys = set()
    # 1. Deterministic registry key — exact, highest precision
    for rid in rec.reg_ids:
        if rid.value_norm:
            keys.add(f"reg:{rid.scheme}:{rid.value_norm}")
    if rec.lei:
        keys.add(f"lei:{rec.lei}")
    # 2. Domain (registrable) — strong B2B signal
    if rec.etld_plus_one:
        keys.add(f"dom:{rec.etld_plus_one}")
    # 3. Phonetic name + country — survives spelling/diacritic noise
    if rec.legal_name_normalized:
        import jellyfish
        sort_token = " ".join(sorted(rec.legal_name_normalized.split())[:3])
        keys.add(f"nm:{rec.primary_country}:{jellyfish.metaphone(sort_token)}")
    # 4. name-prefix + postcode — geographic block
    if rec.postcode:
        keys.add(f"geo:{rec.primary_country}:{rec.postcode[:3]}:{rec.legal_name_normalized[:5]}")
    return keys
```

Blocking keys are stored in a `blocking` table (`block_key, entity_uid`); resolution joins on `block_key`. Typical block size after multi-key union: 2-50 records — comparisons drop from O(N²) to ~O(N·k).

### 3.2 Diacritics, transliteration, multi-language

Nordic + DE/FR names are diacritic-heavy and the *same* entity appears folded or not (`Malmö` vs `Malmo`, `Ångström` vs `Angstrom`, `Müller` vs `Mueller`, `Citroën` vs `Citroen`). We compute **both** a fold and language-aware expansions, and match on whichever scores higher:

```python
import unicodedata

# language-specific expansions (NOT plain ASCII fold — German ä→ae, not a)
EXPANSIONS = {
    "de": {"ä":"ae","ö":"oe","ü":"ue","ß":"ss"},
    "sv": {"å":"a","ä":"a","ö":"o"},      # Swedish sort-folding
    "nb": {"æ":"ae","ø":"o","å":"a"},     # Norwegian
    "da": {"æ":"ae","ø":"o","å":"a"},
    "fi": {"ä":"a","ö":"o"},
    "fr": {},                              # rely on NFKD fold
}

def normalize_name(s, lang=None):
    s = s.lower().strip()
    variants = {s}
    if lang in EXPANSIONS:
        v = s
        for k, r in EXPANSIONS[lang].items():
            v = v.replace(k, r)
        variants.add(v)
    # ASCII fold via NFKD (drops combining marks): ö→o, é→e
    fold = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    variants.add(fold)
    return variants  # match succeeds if ANY pair of variants matches
```

For non-Latin inbound (rare in our 20 markets but happens via global LinkedIn data) we transliterate with `unidecode` before folding. Phonetic keys (Metaphone/NYSIIS via `jellyfish`) give a final safety net for spelling drift.

### 3.3 Company-name normalization per jurisdiction

Legal-form suffixes are noise for matching but **must be preserved** in the canonical record (they're legally meaningful). We strip them *for comparison*, keep them *for storage*:

```python
LEGAL_FORMS = {
    "SE": ["ab", "handelsbolag", "hb", "kb", "ekonomisk förening", "ek för"],
    "NO": ["as", "asa", "ans", "da", "enk"],
    "DK": ["a/s", "aps", "ivs", "p/s", "k/s"],
    "FI": ["oy", "oyj", "ky", "ay", "osk"],
    "DE": ["gmbh", "ag", "kg", "ohg", "gbr", "ug", "gmbh & co. kg", "e.k.", "se"],
    "FR": ["sa", "sas", "sarl", "sasu", "eurl", "sci", "snc"],
    "GB": ["ltd", "limited", "plc", "llp", "cic"],
    "NL": ["bv", "nv", "vof", "cv"],
    "BE": ["nv", "sa", "bvba", "srl", "sprl"],
    "ES": ["sa", "sl", "slu", "sociedad limitada", "sociedad anonima"],
    "IT": ["srl", "spa", "snc", "sas", "srls"],
    # ... PL, PT, IE, AT, CH, LU, IS
}

def strip_legal_form(name, country):
    n = " " + normalize_for_match(name) + " "
    for form in sorted(LEGAL_FORMS.get(country, []), key=len, reverse=True):
        n = n.replace(f" {form} ", " ")
    return " ".join(n.split())
```

We also normalize `&`/`and`/`och`/`und`/`et`, drop generic tokens (`group`, `holding`, `international`) into a low-weight bucket rather than dropping them entirely.

### 3.4 Pairwise probabilistic matching (RapidFuzz + Splink)

Two-stage scoring inside each block. **Stage A — RapidFuzz** for fast deterministic-ish filtering (it's C-backed, ~µs/comparison per `OPEN_SOURCE_TOOLS_CATALOG.md`):

```python
from rapidfuzz import fuzz

def cheap_pair_score(a, b):
    name = fuzz.token_sort_ratio(a.name_match, b.name_match) / 100
    return {
        "name": name,
        "domain_exact": 1.0 if a.etld_plus_one == b.etld_plus_one else 0.0,
        "country_exact": 1.0 if a.primary_country == b.primary_country else 0.0,
        "postcode_exact": 1.0 if a.postcode == b.postcode else 0.0,
    }
```

**Stage B — Splink** (probabilistic, Fellegi-Sunter model) for the records RapidFuzz leaves ambiguous (0.55 < name < 0.92). Splink learns **m-probabilities** (P(field agrees | true match)) and **u-probabilities** (P(field agrees | non-match)) via EM, producing a calibrated `match_weight` and `match_probability` — not a hand-waved heuristic. We prefer Splink over `dedupe` at this scale because it pushes computation into the SQL backend (DuckDB/Spark) and trains without per-record labeling. Comparison columns: normalized name (Jaro-Winkler levels), domain, postcode, VAT, address tokens.

Deterministic short-circuit: **if reg-ids match (checksum-valid) OR LEI matches → match_probability = 1.0**, skip Splink. Registry identity beats any fuzzy score.

### 3.5 Clustering / transitive resolution

Pairwise matches above threshold (τ ≈ 0.92, tuned per entity type against ground truth) become edges in a graph. We take **connected components** as entity clusters — but guard against "merge-everything" chains (A~B, B~C, A≁C) by running a graph cohesion check (Splink's `cluster_pairwise_predictions` with `cluster_threshold`, or break low-cohesion clusters). Each cluster collapses to one `*_uid`; member claims keep their source pointer for provenance.

### 3.6 Field-level validation primitives (reused from extraction pipeline)

These feed both resolution and confidence:

- **Email** — syntax (RFC 5322) → MX lookup (free DNS, async, ~92% catch) → disposable/role-account flags (`abuse@`, `info@` downweighted, not dropped) → optional SMTP RCPT probe (slow, rate-limited; premium tier only). Output `ValidationResult{status, confidence, method, checked_at}`.
- **Phone** — `libphonenumber` parse with **per-country region hint** (critical: `+46` SE, `+47` NO, `+45` DK, `+358` FI, `+49` DE, `+33` FR, `+44` GB...); `is_valid_number` + `number_type` (mobile vs fixed-line vs VoIP). 98% syntactic. Carrier/HLR lookup is paid → premium only.
- **Website** — canonicalize URL (publicsuffix eTLD+1), HEAD request for liveness, follow ≤3 redirects, record final status + cert validity. Dead sites strongly downweight a company's other fields (a dead domain often means dissolved entity).

---

## 4. Freshness & decay

B2B data decays **22-30%/year** (competitive doc: 15-20% *quarterly* on unverified records). A record we verified 14 months ago is, statistically, mostly wrong. The fusion layer therefore treats **time as a first-class confidence input** and schedules re-verification.

### 4.1 Per-field last-verified timestamps

Every field carries `verified_at` and `source`. Freshness multiplier uses **field-specific half-lives** (a registered company name barely decays; a person's direct dial decays fast):

```python
import math
HALF_LIFE_DAYS = {
    "legal_name": 1825,     # 5y — very stable
    "reg_id":     3650,     # ~never changes
    "registered_address": 730,
    "role.title": 270,      # job changes ≈ 9 month half-life
    "role.is_current": 180,
    "email":      400,      # ~22%/yr
    "phone_direct": 300,
    "phone_mobile": 500,
    "website.liveness": 30,
    "vehicle.owner": 365,
}
def freshness(field, verified_at, now):
    age = (now - verified_at).days
    hl = HALF_LIFE_DAYS.get(field, 365)
    return 0.5 ** (age / hl)        # 1.0 fresh → 0.5 at one half-life → decays
```

### 4.2 Re-verification scheduling

A priority queue re-checks fields when `freshness < 0.6` **and** the field matters (high-seniority roles, customer-flagged records re-checked sooner). Cheap re-checks first (registry diff, MX re-ping) before expensive ones (re-scrape, SMTP). This is a cron-driven sweep, sized so the whole estate cycles within one half-life of its fastest-decaying field.

### 4.3 Change detection (cheap, before re-scrape)

- **Wayback CDX API** — query the snapshot index for a domain; if no new capture since last check, the page likely didn't change → skip re-scrape.
- **Sitemap diff** — fetch `sitemap.xml`, diff `<lastmod>` against stored; only re-crawl changed URLs (Screaming Frog list mode).
- **Registry delta feeds** — Bolagsverket/brreg/CVR/Companies House publish daily change files; ingest deltas instead of full re-pull. A status change (active→dissolved) instantly invalidates dependent fields.
- **HTTP `ETag`/`Last-Modified`** — conditional GET; `304 Not Modified` = free skip.

Change detection is itself a confidence input: a field on a page that demonstrably hasn't changed retains higher freshness than its raw age implies.

---

## 5. Multi-source agreement scoring

This is the core differentiator. **N independent methods agreeing raises confidence multiplicatively**, weighted by each source's measured reliability. It generalizes the existing `sannolikhet_kontakt_pct` model (single contact-probability percentage) to a **per-field, multi-source, calibrated** model.

### 5.1 Source reliability weights (measured, not guessed)

Each source has a learned reliability `r_s ∈ (0,1)` = its historical precision against ground truth, **per field type and per country** (a scraper great at SE company names may be poor at DE phones). Stored in a `source_reliability` table, refreshed from the calibration feedback loop (§5.5):

```
source_reliability(source_id, field_type, country) -> r_s
# examples:
#   bolagsverket / legal_name / SE      -> 0.99  (authoritative registry)
#   companies_house / legal_name / GB   -> 0.99
#   gleif / lei_mapping / *             -> 0.99
#   website_scrape / email / SE         -> 0.74
#   linkedin_search / role.title / *    -> 0.88
#   email_pattern_inference / email / * -> 0.55  (guessed first.last@)
#   merinfo_scrape / vehicle.owner / SE -> 0.85
#   cheap_api_confirm / email / *       -> 0.90
```

Authoritative registries get r≈0.99 and effectively *anchor* a field. Inference/guessing gets r≈0.5-0.6.

### 5.2 Bayesian agreement fusion

For a field with claims from sources S each asserting value `v`, we combine in log-odds (numerically stable, naturally multiplicative). Each agreeing source contributes evidence weight `log(r_s / (1 - r_s))`; disagreeing sources contribute negative evidence:

```python
import math

def fuse_field(claims, reliability, freshness_fn, now):
    """
    claims: list of {value, source_id, field_type, country, verified_at}
    Returns: (best_value, confidence_0_1, evidence[])
    """
    # group claims by candidate value (after normalization)
    from collections import defaultdict
    buckets = defaultdict(list)
    for c in claims:
        buckets[normalize_value(c.value, c.field_type)].append(c)

    scored = []
    for value, group in buckets.items():
        logodds = math.log(0.05 / 0.95)   # prior: a random guessed value is unlikely
        evidence = []
        for c in group:
            r = reliability.get((c.source_id, c.field_type, c.country), 0.6)
            r = min(max(r, 0.01), 0.99)
            f = freshness_fn(c.field_type, c.verified_at, now)
            # freshness scales the evidence weight toward the neutral prior
            w = f * math.log(r / (1 - r))
            logodds += w
            evidence.append({"source": c.source_id, "r": r, "fresh": round(f,2), "w": round(w,2)})
        # penalty: subtract evidence from sources backing OTHER values (disagreement)
        for other_value, other_group in buckets.items():
            if other_value == value:
                continue
            for c in other_group:
                r = reliability.get((c.source_id, c.field_type, c.country), 0.6)
                f = freshness_fn(c.field_type, c.verified_at, now)
                logodds -= 0.5 * f * math.log(r / (1 - r))   # half-weight contradiction
        prob = 1 / (1 + math.exp(-logodds))
        scored.append((value, prob, evidence))

    scored.sort(key=lambda x: x[1], reverse=True)
    best_value, raw_conf, evidence = scored[0]
    return best_value, calibrate(raw_conf, claims[0].field_type), evidence
```

**Why log-odds:** two independent r=0.75 sources agreeing yield combined ≈0.90 — agreement compounds. A single r=0.55 guessed email stays low. A registry (r=0.99) single-handedly anchors. This is exactly the "cheap API confirms a scrape" effect — two cheap medium-reliability signals agreeing beat one expensive signal alone.

### 5.3 Validation as a source

Email MX/SMTP, phone `libphonenumber`, website liveness are injected as **pseudo-sources** with their own reliability. A scraped email that *also* passes MX gets a second agreeing signal; one that fails MX gets a strong contradiction → confidence collapses. This is how we avoid Apollo's catch-all false-positive trap: a catch-all MX "pass" is weighted lower (`r≈0.6`) than an SMTP RCPT confirm (`r≈0.9`), and the badge surfaces *which* check passed, not a binary "verified."

### 5.4 Field-level fusion → record assembly

Each canonical field independently picks its best value + confidence. The **record-level** `confidence` is a weighted aggregate (key fields — name, primary contact — weighted higher) but we *never collapse to one number only*: the API exposes per-field confidence so consumers gate on the field they care about.

### 5.5 Calibration (the honesty guarantee)

`calibrate()` maps raw fused probabilities to **empirically observed correctness** via isotonic regression fit against a ground-truth set (registry-confirmed fields, customer bounce/answer feedback, manual QA samples). Re-fit quarterly. We publish reliability diagrams. **This is what lets us truthfully say 0.83 means 83%** — the claim Apollo/Cognism cannot make.

---

## 6. Skip-the-scrape arbitration (speed via fusion)

Platform goal #7. Before the orchestrator dispatches an expensive method (Sequentum browser job, Ranorex, Playwright SPA render), it asks the fusion layer:

```python
def need_expensive_fetch(entity_uid, field, target_conf=0.85):
    cur = current_confidence(entity_uid, field)
    if cur >= target_conf and freshness_ok(entity_uid, field):
        return False                      # already trustworthy → SKIP, save time+cost
    cheap = available_cheap_confirms(entity_uid, field)   # registry, cached API
    projected = simulate_fuse(entity_uid, field, cheap)
    if projected >= target_conf:
        return "cheap_only"               # run cheap confirm, skip the slow scrape
    return "full"                         # confidence gap too large → full method
```

A cheap API confirm that pushes a scraped value over τ means the slow scrape is **never run** — directly serving "raise coverage AND raise speed." The fusion layer is thus also the platform's cost/throughput governor.

---

## 7. GDPR / compliance by design (the EU moat)

Per the competitive analysis, Cognism's defensible moat is GDPR posture, and DE/FR are stricter. We bake compliance into the *schema*, so it's enforced, not bolted on.

### 7.1 Field-level provenance (every value, always)

```
FieldProvenance:                  # attached to EVERY canonical field
  value          : any
  source_id      : text           # which scraper/registry/API
  source_url     : text?          # exact page, for audit
  collected_at   : timestamptz
  method         : enum           # registry_api | scrape | inference | api_confirm
  lawful_basis   : enum           # legitimate_interest | consent | contract | legal_obligation | public_register
  lia_ref        : text?          # Legitimate Interest Assessment doc id
  jurisdiction   : iso3166_2
```

Provenance is *non-optional*. A field with no lawful basis cannot be emitted — the output API filters it. This is the auditability Apollo lacks.

### 7.2 Lawful-basis tagging per country

- **Public registries** (Bolagsverket, brreg, Companies House, INSEE) → `public_register` / `legal_obligation` — strongest basis, B2B firmographics flow freely.
- **B2B contact data** (work email, direct dial, role) → `legitimate_interest`, backed by a documented **LIA** referenced in `lia_ref`. This is the Art. 6(1)(f) path Cognism publishes.
- **DE/FR stricter handling:** Germany (UWG + GDPR) and France (CNIL) require tighter LIA scoping and faster suppression. We carry per-country policy flags; DE/FR personal contact fields default to a shorter re-consent/suppression window and are excluded from certain bulk exports unless the consumer attests B2B purpose.
- **Personal/sensitive national IDs** (SE personnummer, etc.) are **never** stored for marketing — schema forbids it for `person.national_person_id` outside lawful contexts.

### 7.3 Art. 14 notification plumbing

When personal data is collected *not from the data subject* (our case — scraping/registries), Art. 14 requires notification. We generate a notification obligation per `person_uid` on first ingest of personal data, queue a notification (or rely on a published privacy notice + first-contact disclosure), and timestamp it. The provenance trail makes "where did you get my data" answerable in one query.

### 7.4 DNC / suppression per country

Per-country suppression lists (DE Robinsonliste, FR Bloctel, SE NIX, etc.) are loaded as **hard filters** in the output layer. A `cp_uid` matching a national DNC for its country is flagged `suppressed=true` and withheld from contactable exports while remaining in the graph for resolution. Suppression check is keyed on normalized phone (E.164) and email.

### 7.5 Right-to-erasure

`person_uid` (and dependent `role`, `contact_point`) support tombstoning: erasure writes a `redaction` record, purges values, but keeps the surrogate key + a hash to prevent re-ingestion (re-scraping an erased person re-matches the tombstone and is dropped). Erasure propagates to derived exports via the provenance graph.

---

## 8. Output schema + API contract

The canonical, consumer-facing record. **Every field is `{value, confidence, last_verified, sources[], lawful_basis}`** — not a bare value. This shape *is* the honesty contract.

```jsonc
// GET /v1/companies/{company_uid}
{
  "company_uid": "018f...uuidv7",
  "record_confidence": 0.91,           // calibrated, weighted aggregate
  "primary_country": "SE",
  "lei": { "value": "5493001...", "confidence": 0.99,
           "last_verified": "2026-06-20T08:00:00Z",
           "sources": ["gleif"], "lawful_basis": "public_register" },
  "reg_ids": [
    { "scheme": "SE_ORGNR", "value": "5560360793", "checksum_valid": true,
      "confidence": 0.99, "issuer": "bolagsverket",
      "last_verified": "2026-06-23T02:00:00Z" }
  ],
  "legal_name": { "value": "Volvo Personvagnar AB", "confidence": 0.99,
                  "sources": ["bolagsverket", "website_scrape", "gleif"],
                  "agreement": 3, "last_verified": "2026-06-23T02:00:00Z",
                  "lawful_basis": "public_register" },
  "domains": [ { "value": "volvocars.com", "liveness": "200",
                 "confidence": 0.97, "last_verified": "2026-06-24T01:00:00Z" } ],
  "size_band": { "value": "5000+", "confidence": 0.82, "sources": ["bolagsverket"] },
  "_meta": { "freshness_min": 0.71, "fields_suppressed": 0,
             "needs_reverify": ["size_band"] }
}

// GET /v1/people/{person_uid}?include=contact_points
{
  "person_uid": "018f...",
  "record_confidence": 0.78,
  "full_name": { "value": "Anna Lindström", "confidence": 0.93,
                 "sources": ["linkedin_search","website_scrape"], "agreement": 2 },
  "current_role": {
    "company_uid": "018f...", "title_norm": "CFO", "confidence": 0.86,
    "is_current": true, "valid_from": "2024-03-01",
    "sources": ["linkedin_search","press_release"],
    "lawful_basis": "legitimate_interest", "lia_ref": "LIA-2026-014"
  },
  "contact_points": [
    { "kind": "email", "value": "anna.lindstrom@acme.se", "confidence": 0.88,
      "validation": { "syntax": true, "mx": true, "smtp": "catch_all", "disposable": false },
      "sources": ["website_scrape","cheap_api_confirm"], "agreement": 2,
      "method_badge": "mx_confirmed_not_smtp",   // honest: we say WHAT passed
      "last_verified": "2026-06-22T00:00:00Z",
      "lawful_basis": "legitimate_interest", "suppressed": false },
    { "kind": "phone_mobile", "value_e164": "+46701234567", "confidence": 0.74,
      "validation": { "valid": true, "type": "mobile", "region": "SE" },
      "sources": ["merinfo_scrape"], "agreement": 1 }
  ]
}
```

**API contract rules consumed by the rest of the platform:**

1. **No bare values.** Consumers must read `.value` + `.confidence`. Encourages confidence-gated use.
2. **Confidence is calibrated** (§5.5) — `0.8` is a probability, usable for expected-value math (e.g. campaign ROI).
3. **`sources[]` + `lawful_basis` always present** — provenance and compliance are queryable, not hidden.
4. **`method_badge`** spells out *which* validation passed (vs Apollo's opaque "verified") — the honesty signal.
5. **Suppressed fields** are withheld from `?contactable=true` views automatically.
6. **`needs_reverify[]`** lets consumers trigger or wait for refresh.
7. **Bulk/stream endpoints** (`POST /v1/resolve` for entity-resolution-on-submit, `GET /v1/changes?since=` for CDC) mirror the same envelope.

Internally the canonical store is columnar (one row per `*_uid`, JSONB provenance sidecar) in the platform's existing warehouse, with the resolution graph (`blocking`, `pair_scores`, `clusters`) in DuckDB/Spark for Splink. The API is a thin read model over the canonical store + suppression filter.

---

## 9. Why this beats Apollo/Cognism

| Dimension | Apollo / Cognism | This layer |
|---|---|---|
| Confidence number | inflated, opaque, binary "verified" | **calibrated** (0.83 = 83%), per-field |
| Evidence | hidden | `sources[]`, `agreement`, `method_badge` exposed |
| Cross-border keying | inconsistent | LEI + national reg-id + VAT, checksum-validated |
| Freshness | "weekly" claim, no per-field | per-field half-life decay + re-verify scheduling |
| Compliance | bolted on (Cognism) / weak (Apollo) | **schema-enforced** lawful_basis + provenance + DNC + erasure |
| Catch-all emails | counted as "verified" | `smtp:catch_all` surfaced, downweighted |
| Speed | scrape everything | **skip-the-scrape** arbitration via fusion |

The fusion layer makes *honesty mechanical*: you cannot emit a number you cannot defend, you cannot emit a field without provenance, and agreement across many cheap sources is what earns confidence — which is also what makes the platform fast and cheap.
