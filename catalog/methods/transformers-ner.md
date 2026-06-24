# Transformers NER — Hugging Face Custom NER Models

> **Repo:** https://github.com/huggingface/transformers | **Stars:** ~130K | **Language:** Python | **License:** Apache 2.0

The heavy artillery for NER. When spaCy isn't accurate enough and GLiNER doesn't have the right labels, fine-tune a BERT/RoBERTa model on our own labeled data. Used for entity types that no pretrained model handles: Nordic org numbers, vehicle VINs, financial statement fields, specific job titles.

## When to Use (vs spaCy vs GLiNER)

| | spaCy | GLiNER | Transformers |
|---|---|---|---|
| **General entities (PER/ORG/LOC)** | Use first (fast) | Use if no spaCy model | Overkill |
| **Custom entities** | Need training | Just add labels | Fine-tune for best accuracy |
| **Domain-specific** | Not ideal | Works okay | **Best** (fine-tuned) |
| **Accuracy needed** | 92-95% | 85-90% | **96-99%** (fine-tuned) |
| **Speed** | 50K w/s | 100 ent/s | 500 ent/s (GPU) |
| **Setup time** | 1 minute | 1 minute | Hours (training) |

## Example: Fine-Tune for Swedish Org Numbers + Titles

```python
from transformers import AutoTokenizer, AutoModelForTokenClassification, Trainer, TrainingArguments
from datasets import Dataset
import json

# 1. Load labeled data (we generate this from high-confidence extractions)
with open("labeled_data/swedish_entities.json") as f:
    data = json.load(f)

# Format: [{"text": "AB Volvo, VD Anna Wahlberg", "entities": [
#   {"start": 0, "end": 8, "label": "ORG"},
#   {"start": 10, "end": 12, "label": "TITLE"},
#   {"start": 13, "end": 26, "label": "PERSON"}
# ]}]

# 2. Tokenize and align labels
tokenizer = AutoTokenizer.from_pretrained("KB/bert-base-swedish-cased")
model = AutoModelForTokenClassification.from_pretrained(
    "KB/bert-base-swedish-cased",
    num_labels=len(LABEL_LIST)
)

# 3. Train
training_args = TrainingArguments(
    output_dir="./models/sv-ner-custom",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    learning_rate=2e-5,
    evaluation_strategy="steps",
    save_strategy="steps",
    logging_steps=100,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)
trainer.train()

# 4. Use the fine-tuned model
from transformers import pipeline
ner = pipeline("ner", model="./models/sv-ner-custom", tokenizer=tokenizer)
result = ner("AB Volvo, VD Anna Wahlberg, 556012-5790")
```

## Recommended Base Models per Language

| Language | Base Model | Notes |
|---|---|---|
| Swedish | `KB/bert-base-swedish-cased` | National Library of Sweden |
| Norwegian | `NbAiLab/nb-bert-base` | National Library of Norway |
| Danish | `Maltehb/danish-bert-botxo` | Community model |
| Finnish | `TurkuNLP/bert-base-finnish-cased-v1` | University of Turku |
| German | `dbmdz/bert-base-german-cased` | MDZ Digital Library |
| French | `camembert-base` | Facebook/INRIA |
| Italian | `dbmdz/bert-base-italian-cased` | |
| Spanish | `dccuchile/bert-base-spanish-wwm-cased` | |
| Dutch | `GroNLP/bert-base-dutch-cased` | University of Groningen |
| Polish | `dkleczek/bert-base-polish-cased` | |
| English | `bert-base-cased` | Google |
| Multilingual | `xlm-roberta-base` | Covers all 20 languages |

## Active Learning Loop

```python
# After each batch, feed corrected data back to fine-tuning
def active_learning_loop(model, new_labeled_data):
    # 1. Merge with existing training data
    merged = combine_datasets(existing_training_data, new_labeled_data)

    # 2. Fine-tune for 1 epoch (quick update)
    trainer = Trainer(model=model, args=quick_update_args, train_dataset=merged)
    trainer.train()

    # 3. Deploy updated model
    model.save_pretrained("./models/sv-ner-custom")
```

## Related

- [spaCy](spacy.md) — faster, good enough for 95% of cases
- [GLiNER](gliner.md) — zero-shot, no training needed
- [LM Studio + Ollama](lmstudio-ollama.md) — LLM-based extraction (alternative to NER)
