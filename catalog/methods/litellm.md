# LiteLLM — Universal LLM Proxy/Router

> **Repo:** https://github.com/BerriAI/litellm | **Stars:** ~20K | **Language:** Python | **License:** MIT

OpenAI-compatible proxy that routes to 100+ LLM providers (Claude, GPT, Gemini, Ollama, vLLM, LM Studio, and every OSS model). The glue that makes "swap engine = config change" real — one line to switch from local Ollama to Claude to vLLM with zero code changes.

## What it solves

Hardcoding model providers in code creates vendor lock-in. Without a proxy, every model change requires code changes. LiteLLM gives you a single OpenAI-compatible endpoint that routes to whichever model you want — including local ones. API key management, rate limiting, fallbacks, and cost tracking built in.

## Install

```bash
pip install litellm
litellm --model ollama/qwen2.5:14b  # Starts proxy at http://localhost:4000
```

## Config: Route to Multiple Local Models

```yaml
# config.yml
model_list:
  - model_name: fast-extractor
    litellm_params:
      model: ollama/llama3.1:8b
      api_base: http://localhost:11434
  - model_name: accurate-extractor
    litellm_params:
      model: ollama/phi4:14b
      api_base: http://localhost:11434
  - model_name: vision-extractor
    litellm_params:
      model: ollama/qwen3-vl:8b
      api_base: http://localhost:11434
  - model_name: claude-fallback
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: ${CLAUDE_API_KEY}

router_settings:
  enable_pre_call_checks: true
  num_retries: 2
  fallbacks:
    - accurate-extractor: [claude-fallback]  # Auto-fallback to Claude if local fails

general_settings:
  master_key: ${LITELLM_MASTER_KEY}
```

## Platform Integration

```python
from openai import OpenAI

# All code points to ONE endpoint. LiteLLM routes internally.
client = OpenAI(base_url="http://localhost:4000/v1", api_key=os.getenv("LITELLM_KEY"))

# Now "accurate-extractor" could be Ollama today, Claude tomorrow, vLLM next week
# Zero code changes in the platform
response = client.chat.completions.create(
    model="accurate-extractor",
    messages=[{"role": "user", "content": "Extract contacts from: ..."}],
    response_format={"type": "json_object"},
)
```

## Key Features for the Platform

1. **Provider-agnostic routing** — swap Ollama → vLLM → Claude without touching platform code
2. **Cost tracking** — logs token usage and cost per model (even for free local models)
3. **Automatic fallbacks** — if Ollama is down, route to Claude automatically
4. **Rate limiting** — prevent overloading local GPU
5. **Load balancing** — spread requests across multiple Ollama/vLLM instances
6. **Caching** — identical prompts skip LLM entirely (saves GPU)

## Cache for Repetitive Extraction

```yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: redis
    port: 6379
    ttl: 3600  # 1 hour cache for identical prompts
```

When extracting "company X contact page" for the same URL, subsequent runs skip LLM entirely. Massive speedup for re-scrapes.

## Docker Compose Addition

```yaml
litellm:
  image: ghcr.io/berriai/litellm:main-latest
  container_name: nep-litellm
  ports:
    - "4000:4000"
  volumes:
    - ./config/litellm.yml:/app/config.yml
  environment:
    CLAUDE_API_KEY: ${CLAUDE_API_KEY:-}  # Optional, for fallback
  depends_on:
    ollama:
      condition: service_healthy
  restart: unless-stopped
```

## Related

- [LM Studio + Ollama](lmstudio-ollama.md) — the local models LiteLLM routes to
- [Unstructured](unstructured.md) — produces the text input
- [Docker Full Stack](../../docs/infrastructure/docker-compose.full-stack.yml)
