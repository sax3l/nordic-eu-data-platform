# LM Studio + Ollama — Local LLM Infrastructure

> **LM Studio:** https://lmstudio.ai | **Ollama:** https://github.com/ollama/ollama | **vLLM:** https://github.com/vllm-project/vllm

100% local, 100% free LLM inference. No API keys, no rate limits, no per-token cost. LM Studio for desktop/single-machine (GUI + API), Ollama for containerized workers (Docker-native), vLLM for high-throughput serving. The platform's brains — powers NER enrichment, contact extraction, entity resolution, adaptive routing decisions, and the UI-click agent.

## Why Local LLM Matters

Every API call to Claude/GPT for extraction costs money ($0.01-$0.05 per entity). At platform scale (50M+ contacts), that's $250K-$2.5M in API costs. A local model running on your own GPU costs $0.00 per token — only electricity. Even a consumer RTX 4090 (24GB) can run:

- **Qwen2.5-14B** (GGUF Q4_K_M) at ~80 tok/s
- **Llama-3.1-8B** at ~150 tok/s
- **DeepSeek-R1-Distill-Llama-8B** at ~120 tok/s
- **Phi-4-14B** (Microsoft, excellent for structured extraction) at ~70 tok/s

That's enough for 100K+ entity extractions per hour on a single GPU.

## Install

### LM Studio (Desktop — dev/experimentation)

```bash
# Download from https://lmstudio.ai
# GUI for model download + local API server (OpenAI-compatible)
# API at http://localhost:1234/v1
```

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
response = client.chat.completions.create(
    model="qwen2.5-14b-instruct",
    messages=[{"role": "user", "content": "Extract company name and org number from: Bolagsverket AB (559000-0001)"}]
)
```

### Ollama (Containerized Workers — production)

```bash
docker run -d --gpus all -p 11434:11434 --name ollama ollama/ollama
ollama pull qwen2.5:14b
ollama pull llama3.1:8b
ollama pull phi4:14b
# API at http://localhost:11434/v1 (OpenAI-compatible)
```

### vLLM (High-Throughput — multi-GPU, batched inference)

```bash
pip install vllm
# Launch with continuous batching for max throughput
vllm serve Qwen/Qwen2.5-14B-Instruct \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.95
```

## Platform Use Cases

### 1. Contact Extraction from Unstructured Elements

```python
async def extract_contacts(elements_text: str) -> dict:
    """After Unstructured parses a page, LLM extracts structured contacts."""
    prompt = f"""Extract all people from this text. For each person, return JSON:
    [{{"name": "...", "title": "...", "email": "...", "phone": "..."}}]
    Text: {elements_text[:4000]}"""  # chunk if longer
    resp = client.chat.completions.create(model="qwen2.5:14b", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return json.loads(resp.choices[0].message.content)
```

### 2. NER Enrichment After spaCy Base Pass

```python
async def enrich_ner(spacy_entities: list, context: str) -> dict:
    """spaCy gets the base entities; LLM disambiguates and enriches."""
    prompt = f"""Given these entities: {spacy_entities}
    And this context: {context[:2000]}
    Return JSON with: company_name, org_number, person_name, title, email, phone, confidence per field."""
    resp = client.chat.completions.create(
        model="phi4:14b",  # Microsoft Phi-4 is excellent at structured extraction
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
```

### 3. Adaptive Router Decision-Making

```python
async def choose_method(site_stats: dict) -> str:
    """The LLM decides which scraping method to try next based on live stats."""
    prompt = f"""Given this site's recent stats: {json.dumps(site_stats)}
    Choose the cheapest method likely to succeed: curl_cffi, cloudscraper, flaresolverr, cloakbrowser, sequentum.
    Return: {{"method": "...", "reasoning": "..."}}"""
    resp = client.chat.completions.create(model="llama3.1:8b", ...)
```

### 4. Entity Resolution / Dedup Decision

```python
async def are_same_person(person_a: dict, person_b: dict) -> bool:
    prompt = f"""Are these the same person?
    A: {person_a}, B: {person_b}
    Return: {{"match": true/false, "confidence": 0.xx, "reasoning": "..."}}"""
    ...
```

## Recommended Models per Task

| Task | Model | Size | Why |
|---|---|---|---|
| Contact extraction | **Phi-4-14B** | 14B | Best OSS at structured JSON extraction |
| Multilingual NER | **Qwen2.5-14B** | 14B | Strong on sv/no/da/fi/de/fr |
| OCR correction | **Qwen3-VL-8B** | 8B | Vision model for screenshot scanning |
| Router decisions | **Llama-3.1-8B** | 8B | Fast, good enough for method selection |
| Entity resolution | **DeepSeek-R1-Distill-8B** | 8B | Logical reasoning, verifiable chain-of-thought |
| Code generation | **Qwen2.5-Coder-7B** | 7B | Auto-fix broken selectors, adapt extraction |
| Embeddings | **BGE-M3** | 567M | Multilingual embeddings for semantic search |

## Hardware Requirements

| GPU | VRAM | Best Model | Tokens/sec |
|---|---|---|---|
| RTX 4090 | 24GB | Qwen2.5-14B Q4 | ~80 tok/s |
| RTX 3090 | 24GB | Phi-4-14B Q6 | ~60 tok/s |
| RTX 4070 | 12GB | Llama-3.1-8B Q8 | ~150 tok/s |
| RTX 3060 | 12GB | Qwen2.5-7B Q8 | ~100 tok/s |
| CPU-only | 64GB RAM | Qwen2.5-14B Q4 | ~5 tok/s (slow but works) |
| Mac M3 Max | 128GB | Qwen2.5-72B Q4 | ~25 tok/s |

## Speed

- **Ollama**: ~80-150 tok/s on consumer GPU (enough for real-time per-page enrichment)
- **vLLM**: ~500-2000 tok/s on A100 (batched inference, scales to 100+ concurrent)
- **LM Studio**: ~60-120 tok/s (single-user, dev workflow)
- **Cost**: $0.00 per token (electricity only: ~$0.50/hour for a 4090 under full GPU load)

## In the Pipeline

```
Raw HTML/PDF → Unstructured → spaCy base NER → LM Studio/Ollama enrichment → Fusion engine → Storage
                   ↑                            ↑
            (2-5 docs/sec)             (100K+ entities/hour on 1 GPU)
```

## Related

- [Unstructured](unstructured.md) — produces the text input
- [OCR Pipeline](ocr-pipeline.md) — produces images for vision models
- [Browser-Use AI Agents](browser-use.md) — uses LLM for browser control
- [spaCy NER](spacy.md)
