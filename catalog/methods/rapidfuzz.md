# RapidFuzz — Fast Fuzzy String Matching

> **Repo:** https://github.com/rapidfuzz/RapidFuzz | **Stars:** ~4K | **Language:** Python/C++ | **License:** MIT

The fastest fuzzy string matching library. C++ implementation with Python bindings. Used everywhere in the platform: company name matching, person name dedup, address normalization, org number validation. 10-100x faster than fuzzywuzzy.

## Install

```bash
pip install rapidfuzz
```

## Core Patterns

### Company Name Matching

```python
from rapidfuzz import fuzz, process

# Match scraped name against registered name
scraped = "AB Volvo (publ)"
registered = "Volvo Aktiebolag"

similarity = fuzz.ratio(scraped.lower(), registered.lower())  # 0-100
partial = fuzz.partial_ratio("Volvo", "AB Volvo (publ)")       # Subset match
token = fuzz.token_sort_ratio(scraped, registered)              # Word order insensitive
weighted = fuzz.WRatio(scraped, registered)                     # Weighted combination

# Best match from database
matches = process.extract(
    "Volvo AB",
    ["AB Volvo (publ)", "Volvo Cars AB", "Volvo Lastvagnar AB", "Volvofinans AB"],
    scorer=fuzz.WRatio,
    limit=3,
)
# → [("AB Volvo (publ)", 96.0, 0), ("Volvo Cars AB", 85.0, 1), ...]
```

### Person Name Dedup

```python
def are_same_person(name_a: str, name_b: str, threshold: int = 85) -> bool:
    """Compare two person names with typo tolerance."""
    # Normalize
    a = name_a.lower().strip()
    b = name_b.lower().strip()

    # Exact match
    if a == b:
        return True

    # Same initials + last name (e.g., "A. Wahlberg" vs "Anna Wahlberg")
    a_parts = a.split()
    b_parts = b.split()
    if len(a_parts) >= 2 and len(b_parts) >= 2:
        if a_parts[-1] == b_parts[-1] and a_parts[0][0] == b_parts[0][0]:
            return True

    # Fuzzy match
    return fuzz.WRatio(a, b) >= threshold
```

### Address Normalization

```python
def normalize_address(raw: str) -> str:
    """Normalize address for comparison."""
    import re
    addr = raw.lower().strip()
    addr = re.sub(r'\b(gatan|vägen|g\.|v\.)\b', '', addr)
    addr = re.sub(r'\b(strasse|str\.|gasse)\b', '', addr)
    addr = re.sub(r'\s+', ' ', addr)
    return addr

# Compare normalized addresses
fuzz.ratio(
    normalize_address("Drottninggatan 5, 111 51 Stockholm"),
    normalize_address("Drottningg. 5, Stockholm 11151")
)
# → 92 (high match after normalization)
```

## Speed

- 500K comparisons/sec (single-core CPU)
- 10-100x faster than fuzzywuzzy
- Memory: negligible (~5MB for any workload)

## In the Pipeline

```
Raw company names → RapidFuzz → match against registered names → Splink for full record linkage
Raw person names  → RapidFuzz → dedup contacts → merge into single golden contact record
Raw addresses     → RapidFuzz → normalize + match → link to registered address
```

## Related

- [Splink](splink.md) — probabilistic record linkage (uses RapidFuzz internally)
- [spaCy](spacy.md) — first-pass NER extraction
- [OCR Pipeline](ocr-pipeline.md) — the text source that needs dedup
