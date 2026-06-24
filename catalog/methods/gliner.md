# GLiNER — Zero-Shot, Language-Agnostic NER

> **Repo:** https://github.com/urchade/GLiNER | **Stars:** ~5K | **Language:** Python | **License:** Apache 2.0

Zero-shot NER that needs NO language-specific models. You define what to extract, it finds it — in any language. The platform's universal NER fallback for languages without spaCy models (Czech, Hungarian, Icelandic, Portuguese) and for custom entity types (vehicle VINs, tax IDs, banking details).

## What it solves

spaCy needs a pretrained model per language. Czech, Hungarian, Icelandic, Romanian — no spaCy models exist. GLiNER solves this: you give it entity types ("person", "organization", "email", "vehicle registration number") and it finds them in ANY language. Works out of the box for all 20 target countries.

## Install

```bash
pip install gliner
```

## Zero-Shot Extraction

```python
from gliner import GLiNER

# Load once (small model fits on CPU)
model = GLiNER.from_pretrained("urchade/gliner_large-v2.1")

# Define what you want to extract — in English labels, works for any language
labels = [
    "Person",
    "Organization",
    "Email Address",
    "Phone Number",
    "Address",
    "Job Title",
    "Tax ID",
    "Vehicle Registration Number",
    "Website URL",
]

text = """
AB Volvo (publ), organisationsnummer 556012-5790, med säte i Göteborg.
Kontakt: Anna Wahlberg, VD, anna.wahlberg@volvo.com, 031-66 00 00.
Styrelsen består av Carl-Henric Svanberg (ordförande), Matti Alahuhta,
och Kathryn Marinello. Registreringsnummer: ABC123.
"""

entities = model.predict_entities(text, labels, threshold=0.5)

for entity in entities:
    print(f"{entity['label']}: {entity['text']} ({entity['score']:.0%})")
```

Output:
```
Person: Anna Wahlberg (98%)
Organization: AB Volvo (publ) (99%)
Email Address: anna.wahlberg@volvo.com (99%)
Phone Number: 031-66 00 00 (95%)
Person: Carl-Henric Svanberg (97%)
Job Title: VD (85%)
Job Title: ordförande (82%)
Person: Matti Alahuhta (88%)
Person: Kathryn Marinello (85%)
Vehicle Registration Number: ABC123 (92%)
Tax ID: 556012-5790 (96%)
Address: Göteborg (78%)
```

## Language Test (same model, different languages)

```python
# German
model.predict_entities("Mercedes-Benz AG, Stuttgart. Vorstand: Ola Källenius.", labels)
# → Organization: Mercedes-Benz AG, Location: Stuttgart, Person: Ola Källenius

# French
model.predict_entities("TotalEnergies SE, Paris. Directeur: Patrick Pouyanné.", labels)
# → Organization: TotalEnergies SE, Location: Paris, Person: Patrick Pouyanné

# Hungarian
model.predict_entities("OTP Bank Nyrt., Budapest. Vezérigazgató: Csányi Sándor.", labels)
# → Organization: OTP Bank Nyrt., Location: Budapest, Person: Csányi Sándor
```

## Custom Entity Types for the Platform

```python
# Define platform-specific entity types
PLATFORM_LABELS = [
    # Standard NER
    "Person",
    "Organization",
    "Location",
    "Email Address",
    "Phone Number",
    "Website URL",
    "Job Title",
    "Address",

    # Financial
    "Tax ID",
    "VAT Number",
    "LEI Code",
    "Revenue Amount",
    "Employee Count",

    # Vehicle (for VehIQ integration)
    "Vehicle Registration Number",
    "VIN",
    "Vehicle Make",
    "Vehicle Model",

    # Nordic-specific
    "Organisationsnummer",  # Swedish
    "Org.nr",               # Norwegian
    "CVR Number",           # Danish
    "Y-tunnus",             # Finnish Business ID
]
```

## GLiNER vs spaCy

| | GLiNER | spaCy |
|---|---|---|
| **Languages** | All (zero-shot) | 15+ (pretrained models) |
| **Custom entities** | Yes (just add to labels) | No (need training data) |
| **Speed** | ~100 entities/sec | ~50,000 words/sec |
| **Accuracy (SV/DE/EN)** | 85-90% | 92-95% |
| **Accuracy (CZ/HU/IS)** | 85-90% | N/A (no model exists) |
| **Memory** | ~500MB (large model) | ~500MB per language |
| **GPU** | Optional (2x speedup) | No (CPU only) |

**Platform strategy:** spaCy first for languages with models (SE/NO/DK/FI/DE/FR/IT/ES/NL/PL/EN). GLiNER fallback for languages without (CZ/HU/IS/PT). GLiNER for ALL custom entity types (vehicle, financial, tax IDs).

## Hybrid Pipeline

```python
def extract_hybrid(text: str, country: str) -> dict:
    """spaCy for standard entities, GLiNER for custom + fill gaps."""
    results = {"spacy": {}, "gliner": {}, "merged": {}}

    # 1. spaCy (if available for country)
    if country in SPA_COUNTRIES:
        results["spacy"] = extract_entities(text, country)

    # 2. GLiNER (always — for custom entities spaCy can't do)
    results["gliner"] = gliner_extract(text, PLATFORM_LABELS)

    # 3. Merge: GLiNER fills gaps spaCy missed or can't do
    results["merged"] = merge_results(results["spacy"], results["gliner"])
    return results["merged"]
```

## Speed

- CPU: ~100 entities/sec
- GPU: ~200 entities/sec (if CUDA available)
- Memory: ~500MB for large model
- Best for: filling gaps spaCy can't handle, and languages without spaCy models

## Related

- [spaCy](spacy.md) — faster for supported languages
- [Transformers NER](transformers-ner.md) — if you need even higher accuracy with fine-tuning
- [Splink](splink.md) — entity resolution after NER extraction
