# Splink — Probabilistic Record Linkage at Scale

> **Repo:** https://github.com/moj-analytical-services/splink | **Stars:** ~1.5K | **Language:** Python | **License:** MIT

The UK Ministry of Justice's open-source entity resolution engine. Uses probabilistic Fellegi-Sunter models to deduplicate and link records across datasets with imperfect matching. Built on Spark/DuckDB for scale. The platform's cross-border fusion engine.

## What it solves

Entity resolution is the hardest part of multi-source data fusion. The same company appears in 3 registries with slightly different names, addresses, and IDs. Giovanni Rossi and Gianni Rossi might be the same person. Splink handles this with probabilistic models — not just fuzzy string matching, but statistical inference over blocking rules.

## Install

```bash
pip install splink
```

## Core Pattern: Company Dedup Across Registries

```python
import splink.comparison_library as cl
from splink import DuckDBAPI, Linker, SettingsCreator

db_api = DuckDBAPI()

# Load companies from 3 registries
df = db_api.read_csv("merged_companies.csv")

settings = SettingsCreator(
    link_type="dedupe_only",
    blocking_rules=[
        "l.company_name = r.company_name",           # Exact name match (fast block)
        "l.org_number = r.org_number",               # Same org ID (fast block)
        "l.postal_code = r.postal_code",             # Same area (loose block)
    ],
    comparisons=[
        cl.ExactMatch("org_number").configure(term_frequency_adjustments=True),
        cl.LevenshteinAtThresholds("company_name", [1, 2, 5]),  # 1-5 char edit distance
        cl.ExactMatch("city").configure(term_frequency_adjustments=True),
        cl.JaccardAtThresholds("address", [0.7, 0.8, 0.9]),
        cl.ExactMatch("country"),
    ],
)

linker = Linker(df, settings, db_api=db_api)
linker.training.estimate_probability_two_random_records_match()
linker.training.estimate_u_using_random_sampling()

result = linker.inference.predict()
clusters = result.as_pandas_dataframe()
# clusters: cluster_id, company_id, match_probability, matched_name, ...
```

## Blocking Rules Strategy (for Speed)

Blocking rules determine which record pairs are compared. Without them, every record compared to every other = O(n²). Good blocking → O(n log n).

```
# Level 1: Exact ID match (fastest, catches official registry merges)
"l.org_number = r.org_number"

# Level 2: Normalized name match (catches spelling/abbreviation variants)
"l.name_clean = r.name_clean"  # name_clean = lower(strip_punct(name))

# Level 3: Name first-char + postal code (catches relocated companies)
"substr(l.company_name, 1, 1) = substr(r.company_name, 1, 1) AND l.postal_code = r.postal_code"

# Level 4: Phonetic + country (catches international branches)
"l.name_soundex = r.name_soundex AND l.country = r.country"
```

## Cross-Border Fusion Pattern

```python
# Field-level comparisons for cross-border company matching
settings = SettingsCreator(
    link_type="link_only",  # Link across datasets, not dedup within
    comparisons=[
        cl.ExactMatch("lei_number"),  # GLEIF/LEI = golden key across borders
        cl.ExactMatch("tax_id"),      # VAT number
        cl.LevenshteinAtThresholds("legal_name", [1, 3, 5]),
        cl.JaroWinklerAtThresholds("legal_name", [0.85, 0.90, 0.95]),
        cl.ExactMatch("country").configure(term_frequency_adjustments=True),
        cl.ExactMatch("city"),
        cl.ExactMatch("postal_code"),
    ],
    blocking_rules=[
        "l.lei_number = r.lei_number",
        "l.tax_id = r.tax_id",
        "l.country = r.country AND substr(l.legal_name,1,3) = substr(r.legal_name,1,3)",
    ],
)

linker = Linker([df_left, df_right], settings, db_api=db_api)
# df_left = Swedish companies, df_right = Danish companies
# Links companies that exist in both countries (e.g., Ørsted A/S = Ørsted AB)
```

## Speed

- DuckDB backend: ~1M comparisons/sec on consumer CPU
- Spark backend: ~10M comparisons/sec on cluster
- Blocking reduces pairs from O(n²) to O(n log n): 1M records → ~100K comparisons instead of 500B

## Integration with the Platform

```
┌────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Multi-source    │ ──► │ Splink entity    │ ──► │ Golden record│
│ raw records     │     │ resolution       │     │ with sources │
│ (20 registries) │     │ (probabilistic)  │     │ + confidence │
└────────────────┘     └──────────────────┘     └──────────────┘
```

## Related

- [RapidFuzz](rapidfuzz.md) — fuzzy string matching (faster, simpler, used in Splink comparisons)
- [Confidence Scoring](../../docs/architecture/) — multi-source agreement scoring post-Splink
- [sources.yaml](../../sources/sources.yaml) — input registries
