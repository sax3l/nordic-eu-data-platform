# spaCy NER — Multilingual Named Entity Recognition

> **Framework:** https://github.com/explosion/spaCy | **Stars:** ~31K | **Language:** Python | **License:** MIT

Industrial-strength NLP. The platform's first-pass NER engine — fast, free, accurate for 15+ European languages. Runs locally on CPU (no GPU needed). Extracts persons, organizations, locations, dates, money, and more from unstructured text before the LLM enrichment pass.

## Install

```bash
pip install spacy

# Download language models
python -m spacy download sv_core_news_lg   # Swedish
python -m spacy download nb_core_news_lg   # Norwegian
python -m spacy download da_core_news_lg   # Danish
python -m spacy download fi_core_news_lg   # Finnish
python -m spacy download de_core_news_lg   # German
python -m spacy download fr_core_news_lg   # French
python -m spacy download it_core_news_lg   # Italian
python -m spacy download es_core_news_lg   # Spanish
python -m spacy download nl_core_news_lg   # Dutch
python -m spacy download pl_core_news_lg   # Polish
python -m spacy download xx_sent_ud_sm     # Multi-language fallback
python -m spacy download en_core_web_lg    # English
```

## Language Map

```python
LANG_MAP = {
    "SE": "sv_core_news_lg",
    "NO": "nb_core_news_lg",
    "DK": "da_core_news_lg",
    "FI": "fi_core_news_lg",
    "IS": "en_core_web_lg",   # No Icelandic spaCy model — use English or GLiNER
    "DE": "de_core_news_lg",
    "AT": "de_core_news_lg",
    "CH": "de_core_news_lg",  # Swiss German = standard German model
    "FR": "fr_core_news_lg",
    "IT": "it_core_news_lg",
    "ES": "es_core_news_lg",
    "PT": "pt_core_news_lg",
    "NL": "nl_core_news_lg",
    "BE": "nl_core_news_lg",  # Flemish = Dutch model
    "PL": "pl_core_news_lg",
    "CZ": "xx_sent_ud_sm",    # No Czech model — use multi-language fallback
    "HU": "xx_sent_ud_sm",    # No Hungarian model
    "UK": "en_core_web_lg",
    "IE": "en_core_web_lg",
}
```

## Core Extraction Pipeline

```python
import spacy
import re
from typing import Optional

# Lazy-load models (only loaded once per worker)
_nlp_cache = {}

def get_nlp(country: str) -> spacy.Language:
    model = LANG_MAP.get(country, "en_core_web_lg")
    if model not in _nlp_cache:
        _nlp_cache[model] = spacy.load(model)
    return _nlp_cache[model]

def extract_entities(text: str, country: str = "SE") -> dict:
    """Extract PER, ORG, LOC, MONEY, DATE, and contact patterns."""
    nlp = get_nlp(country)
    doc = nlp(text[:100000])  # Truncate for speed

    entities = {
        "persons": [],
        "organizations": [],
        "locations": [],
        "dates": [],
        "money": [],
        "org_numbers": [],
        "emails": [],
        "phones": [],
        "urls": [],
    }

    # spaCy named entities
    for ent in doc.ents:
        if ent.label_ == "PER":
            entities["persons"].append({"text": ent.text, "confidence": 0.85})
        elif ent.label_ == "ORG":
            entities["organizations"].append({"text": ent.text, "confidence": 0.80})
        elif ent.label_ in ("LOC", "GPE"):
            entities["locations"].append({"text": ent.text, "confidence": 0.90})
        elif ent.label_ == "DATE":
            entities["dates"].append({"text": ent.text, "confidence": 0.95})
        elif ent.label_ == "MONEY":
            entities["money"].append({"text": ent.text, "confidence": 0.95})

    # Regex for contact patterns (spaCy doesn't always catch these)
    entities["emails"] = list(set(re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
    )))
    entities["phones"] = list(set(re.findall(
        r"\+?\d[\d\s()-]{6,}\d", text
    )))
    entities["urls"] = list(set(re.findall(
        r"https?://[^\s<>\"']+", text
    )))

    # Swedish org number pattern
    if country == "SE":
        entities["org_numbers"] = list(set(re.findall(
            r"\b\d{6}[-]\d{4}\b", text
        )))
    # Norwegian org number
    elif country == "NO":
        entities["org_numbers"] = list(set(re.findall(
            r"\b\d{3}\s?\d{3}\s?\d{3}\b|ORG\.\s*\d{9}", text
        )))
    # Danish CVR
    elif country == "DK":
        entities["org_numbers"] = list(set(re.findall(
            r"\b\d{8}\b|CVR[:\s]*\d{8}", text
        )))

    return entities
```

## Country-Specific Patterns

### Swedish Titles (board/management)
```python
SWEDISH_TITLES = [
    "VD", "Verkställande direktör", "Styrelseordförande",
    "Styrelseledamot", "Ekonomichef", "CFO", "CEO",
    "Marknadschef", "Försäljningschef", "IT-chef",
    "Personalchef", "HR-chef", "Produktionschef", "Teknisk chef",
]
```

### German Titles
```python
GERMAN_TITLES = [
    "Geschäftsführer", "Geschäftsführerin", "Vorstand",
    "Vorstandsvorsitzender", "Aufsichtsrat", "Prokurist",
    "Leiter", "Abteilungsleiter", "Personalleiter",
    "Vertriebsleiter", "Marketingleiter", "IT-Leiter",
]
```

### Match titles near person names
```python
def extract_contacts_with_titles(text: str, country: str) -> list[dict]:
    """Find person names with nearby titles."""
    nlp = get_nlp(country)
    doc = nlp(text[:100000])

    titles = TITLE_MAP.get(country, [])
    contacts = []

    for sent in doc.sents:
        persons = [ent.text for ent in sent.ents if ent.label_ == "PER"]
        found_titles = [t for t in titles if t.lower() in sent.text.lower()]
        if persons and found_titles:
            contacts.append({
                "name": persons[0],
                "titles_matched": found_titles,
                "sentence": sent.text[:200],
            })
    return contacts
```

## Speed

- CPU: ~50,000 words/sec (10-100x faster than LLM)
- Memory: ~500MB per loaded model
- One model handles entire language — load once, reuse
- 100K entities/sec on modern CPU

## In the Pipeline

```
Raw text → spaCy (first-pass NER, 50K w/s) → LLM (enrichment, 100 tok/s)
                ↓                                    ↓
         persons, orgs, locations            structured contacts, confidence
                ↓                                    ↓
              (free, fast, reliable)        (slower, richer, more accurate)
```

## Related

- [GLiNER](gliner.md) — the zero-shot NER alternative (no per-language models needed)
- [LM Studio + Ollama](lmstudio-ollama.md) — the LLM enrichment pass
- [Unstructured](unstructured.md) — produces the clean text input
- [Extraction Pipeline](../../examples/extraction_pipeline.py)
