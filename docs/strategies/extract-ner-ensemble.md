# Strategy: NER Ensemble (language-routed, voting, LLM-backed)

**Layer:** EXTRACTION · **Component:** `extract-ner-ensemble`
**Last updated:** 2026-06-24
**Builds on:** `docs/architecture/MASTER_BLUEPRINT_FULL.md` §2 (NER language dispatcher), §4.7, §8.2 (per-country model IDs), critic P1-6; `catalog/OPEN_SOURCE_TOOLS_CATALOG.md` §7 (spaCy, transformers, flair, stanza, GLiNER via transformers).

---

## 1. Mechanism

Free-text residual that rules couldn't structure (officer lists, "om oss"/"about" prose, press releases, OCR'd imprints) is mined for entities — `PERSON`, `ORG`, `ROLE/TITLE`, `LOC/ADDRESS` — by a **language-routed ensemble with a vote and an LLM tie-breaker**:

1. **Language detect + route.** `doc.lang` (fasttext/`lingua`) selects the best per-market model from the blueprint's §8.2 table rather than a one-size multilingual model: `KB/bert-base-swedish-cased-ner` / `sv_core_news_lg` (SE), `TurkuNLP` FinBERT (FI), DaCy large (DK), `NbAiLab/nb-bert-base-ner` (NO), `flair/ner-german-large` / `de_core_news_lg` (DE/AT), RobBERT / `nl_core_news_lg` (NL), `Jean-Baptiste/camembert-ner` (FR), `it_core_news_lg` (IT), `roberta-large-bne-capitel-ner` (ES), BERTimbau (PT), `en_core_web_trf` (UK/IE), `pl_core_news_lg`/HerBERT (PL), NameTag 3 (CZ), HuSpaCy (HU), with `xx_ent_wiki_sm` / `nbailab-base-ner-scandi` as the fallback only where no dedicated model exists (IS, LU).
2. **Schema-flexible second model.** `GLiNER` (zero-shot, label-promptable via transformers) extracts target labels the off-the-shelf model lacks — e.g. `JOB_TITLE`, `DECISION_MAKER`, Nordic role terms (`VD`, `beslutsfattare`) — without per-language fine-tuning.
3. **Vote / reconcile.** Spans from the language model and GLiNER are aligned; agreement on a span+label raises confidence, disagreement flags it. spaCy `nlp.pipe(batch_size=256, n_process=N)` keeps this at 150-500 docs/s.
4. **LLM fallback.** Only the *ambiguous* residual — conflicting spans, low model confidence, or messy multi-entity sentences — goes to the Claude API for resolution. This is the costly rung, gated to the minority of spans the ensemble can't agree on.

Each extracted entity is normalized (diacritic-aware) and emitted as a claim with the model that produced it as `source_id`.

## 2. Tools / repos

`explosion/spaCy` (+ per-language `*_core_news_lg`/`_trf` pipelines), `huggingface/transformers` (KB/bert, FinBERT, camembert, flair-german, roberta-bne, BERTimbau, HerBERT), `flairNLP/flair`, `stanfordnlp/stanza` (66-language safety net), GLiNER (via transformers), `lingua`/fasttext for language ID, `jellyfish`/`unidecode` for normalization. Claude API for the gated fallback. Runs on the Dramatiq CPU/GPU parse fleet.

## 3. Failure mode it eliminates

It eliminates **multilingual NER degradation** — the critic's P1-6 gap: hardcoding `en_core_web_md`/`xx_ent_wiki_sm` across 20 markets throws away the accuracy the country research already found (the multilingual fallback is materially worse than `KB/bert` on Swedish, FinBERT on Finnish, etc.). It also eliminates **single-model blind spots**: any one NER model misses entity types or mis-segments names with particles (`van der`, `von`, `de la`) and Nordic compounds; the ensemble vote + GLiNER's promptable labels catch what the base model drops, and the LLM resolves the genuinely hard residual instead of silently emitting a wrong span.

## 4. Composition

- **Receives from `extract-parser-cascade`** (free-text residual after rule extraction) and **from `extract-ocr-cascade`** (recovered scan text) — it runs on the *minimum* text, never the whole page, because rules and structured-state already captured the easy fields.
- **Feeds `resolve-entity-resolution`:** extracted `PERSON`/`ORG` spans become candidate person/company records whose names are normalized by the same diacritic/legal-form logic the resolver uses.
- **Feeds `resolve-fusion-confidence`:** each model is a source with a measured `r_s` per field-type-per-country (e.g. `linkedin_search/role.title → 0.88`); ensemble agreement is itself an agreement signal that compounds in the log-odds fuse.
- **Feeds `verify-validation-qa`:** extracted persons are checked against the drop-non-humans rule (an `ORG` mis-tagged as `PERSON`, or "Reception" as a name, is dropped before it pollutes the contact graph).
- **Depends on the per-source policy gate** for lawful-basis tagging of the personal entities it surfaces.

## 5. Success contribution

Per-document entity recall is `1 − Π(1 − pᵢ)` across the language model, GLiNER, and the LLM fallback. Routing to the correct per-language model lifts the base rate from the multilingual-fallback level (often ~0.80-0.85 F1) to the dedicated-model level (~0.88-0.94 F1 per the country files), and the GLiNER + LLM rungs catch most of the residual, pushing per-document recall toward ~0.95+ on legible text. This directly raises *contact coverage* — the platform's weakest, highest-value layer — by reliably pulling officer names and titles out of prose that registries don't structure. The contribution is bounded honestly: NER cannot invent a contact the text doesn't contain, so universe coverage of people remains capped by what the lawful surface (registry officers + public imprints + public LinkedIn SERP) actually exposes.

## 6. Compliance envelope

NER processes already-fetched lawful text and emits **personal data** (names, titles), so it is a GDPR-sensitive stage and the strictest envelope applies: (a) every extracted person carries `{source_id (model + origin source), source_url, collected_at, method=inference, jurisdiction}` so Art. 14 notification and lawful-basis (`legitimate_interest` for B2B role/contact, backed by an LIA) are enforceable; (b) entities from sources tagged `reuse=no_direct_marketing` (BE KBO, DE directories) inherit that flag; (c) DE/FR personal fields get the stricter suppression window; (d) special-category inferences are out of scope — the ensemble extracts business-contact entities, not protected attributes; (e) the LLM fallback only receives text the source permits third-party processing of, and never authenticated-LinkedIn content (LinkedIn is resolved from public SERP only). Non-human "contacts" are dropped, shrinking the personal-data surface to actual decision-makers.
