# dedupe.io — Probabilistic Record Deduplication

> **Repo:** https://github.com/dedupeio/dedupe | **Stars:** ~4K | **Language:** Python | **License:** MIT

Probabilistic deduplication and fuzzy matching with active learning. The OSS alternative to Splink for smaller-to-medium datasets. Uses supervised learning (you label a few pairs) to learn matching parameters.

## When to Use (vs Splink vs RapidFuzz)

| | RapidFuzz | dedupe.io | Splink |
|---|---|---|---|
| **Scale** | Any | <1M records | 1M-100M+ records |
| **Setup** | Code rules | Label pairs | Code rules |
| **Accuracy** | Good (rule-based) | Excellent (ML) | Excellent (probabilistic) |
| **Speed** | Fastest | Medium | Fast |
| **Use case** | Single-field matching | Full record linkage | Large-scale entity resolution |

Platform uses Splink for cross-registry company matching (scale). dedupe.io for contact dedup within a single country batch (medium scale). RapidFuzz for individual name/address comparisons (small, fast).

## Install

```bash
pip install dedupe
```

## Usage

```python
import dedupe
from dedupe import StaticDedupe

# 1. Define fields for comparison
fields = [
    {"field": "full_name", "type": "String"},
    {"field": "email", "type": "String"},
    {"field": "phone", "type": "String"},
    {"field": "org_number", "type": "Exact"},
    {"field": "title", "type": "String"},
]

# 2. Train (label ~50 pairs manually)
deduper = dedupe.Dedupe(fields)
deduper.sample(data, sample_size=15000)

# ... manual labeling ...
# deduper.mark_pairs(labelled_pairs)
# deduper.train()

# 3. Cluster (find duplicates)
clusters = deduper.partition(data, threshold=0.5)
# clusters = [[record1, record2], [record3], ...]

# 4. Merge clusters into golden records
for cluster in clusters:
    if len(cluster) > 1:
        golden = merge_duplicates(cluster)
```

## Related

- [Splink](splink.md) — for large-scale (1M+) record linkage
- [RapidFuzz](rapidfuzz.md) — for single-field fuzzy matching
- [spaCy](spacy.md) — produces the entity data that needs dedup
