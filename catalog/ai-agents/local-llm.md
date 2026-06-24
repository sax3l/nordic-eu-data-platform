# Local LLM brains — inference engines & open models

**Compiled:** 2026-06-24 | **Scope:** the open-source AI "brains" for the adaptive harvesting platform — the inference *engines* that serve models, and the open *models* that act as worker brains.

This catalog answers **"which open AI runs our worker pool, and where."** It maps each engine/model onto the platform's architecture pillars: the [`adaptive-engine`](../../docs/architecture/) (multi-armed-bandit method router, failure classifier → auto-remediation), the [`speed-parallelism`](../../docs/architecture/) work fabric (source-racing, batched OCR/NER), and [`fusion-confidence`](../../docs/architecture/) (entity resolution, structured extraction). All star counts confirmed via web search June 2026; treat them as ±, GitHub moves fast.

> **Cost framing.** The entire point of a *local* brain layer is escaping per-token API pricing and rate caps at 50M-record scale. A worker pool that calls a metered API for every page classification/extraction is dead on arrival economically. These engines + open weights give us **$0 marginal inference** on hardware we already own/rent, with no prompt leaving our perimeter (a GDPR-by-design win — personal data never touches a third-party LLM API).

> **Where this layer sits.** Engines below the line are *runtimes*; models are *weights* you load into them. The router doesn't call a model directly — it calls an **OpenAI-compatible `/v1/chat/completions` endpoint** that one of these engines exposes. That indirection is the whole integration story: pick the engine per deployment tier, hot-swap models per task, keep one client interface.

---

## Part 1 — Inference engines (the runtime that serves the brain)

### vLLM
- **Repo:** https://github.com/vllm-project/vllm — **~75K stars** (one of the most active OSS AI projects, 2000+ contributors; originated UC Berkeley Sky Computing Lab)
- **License:** Apache 2.0
- **What it does:** High-throughput, memory-efficient serving engine. PagedAttention + continuous batching give it ~9x the throughput of single-request runtimes under concurrency. OpenAI-compatible server, tensor/pipeline parallelism, FP8/AWQ/GPTQ quant, structured-output (guided JSON/regex/grammar via xgrammar/outlines), speculative decoding.
- **Where it fits in OUR platform:** **The production worker-pool engine.** This is the default backend behind the [`speed-parallelism`](../../docs/architecture/) work fabric — one vLLM replica per GPU node serves *thousands* of concurrent classify/extract/route calls from Celery/Temporal workers. Continuous batching is exactly what a queue-depth-autoscaled fabric needs: requests from many workers coalesce into GPU batches automatically. Use it for the high-volume inner loop — page-type classification, field extraction, "is this the right contact?" judgments.
- **Hardware/cost:** GPU-mandatory (NVIDIA primary; AMD ROCm + Intel maturing). A single 24GB GPU (RTX 4090 / L4) serves a 7–14B model to a large worker fleet; a 4×A100/H100 node serves 70B-class or MoE. $0 software; cost is GPU rent/amortization. Throughput-per-dollar is best-in-class.
- **Maturity:** Very high — de-facto industry standard for self-hosted serving, broad production adoption, fast release cadence.
- **Integration note:** Launch `vllm serve <model>`, point the router's OpenAI client at it. Enable **guided decoding** (`guided_json` / `response_format`) so extraction workers get schema-valid JSON with ~zero overhead → feeds [`fusion-confidence`](../../docs/architecture/) directly. Run N replicas behind a load balancer; the bandit router treats "LLM-extract" as one method among Screaming-Frog/regex fallbacks and tracks its success/latency per host.

### SGLang
- **Repo:** https://github.com/sgl-project/sglang — **~28K stars** (deployed at xAI, NVIDIA, AMD, LinkedIn; reportedly trillions of tokens/day across 400K+ GPUs)
- **License:** Apache 2.0
- **What it does:** High-performance serving framework with a **structured front-end language**. Killer features for us: **RadixAttention** (automatic KV-cache reuse across requests that share a prefix) and **compressed-FSM constrained decoding** (forces JSON-Schema / regex / grammar output at ~100% validity, near-zero overhead).
- **Where it fits in OUR platform:** **The structured-extraction engine.** When the workload is "pull these 18 fields out of every company page into the exact same JSON schema," SGLang is the sharpest tool: the shared system-prompt + schema prefix is cached once via RadixAttention (huge speedup when 50M pages share one extraction prompt), and the FSM guarantees the output parses on the first try — no retry loop, no malformed-JSON poison entering [`fusion-confidence`](../../docs/architecture/). Also the right engine for multi-step agentic flows where one prompt branches.
- **Hardware/cost:** Same GPU class as vLLM. Prefix-cache reuse means *higher effective throughput* than vLLM specifically on our repetitive-prompt extraction workload, so potentially cheaper per record. $0 software.
- **Maturity:** High and rising fast; production-proven at hyperscale. Slightly steeper learning curve than vLLM for the SGLang DSL (but the plain OpenAI endpoint works too).
- **Integration note:** Stand up `python -m sglang.launch_server`. Structure every extraction as a fixed prefix (schema + instructions) + variable page text so RadixAttention bites. Use it as the **specialist extraction lane** racing alongside the generalist vLLM lane in the [source-racing](../../docs/architecture/) pattern; the router keeps whichever returns valid JSON first.

### llama.cpp
- **Repo:** https://github.com/ggml-org/llama.cpp — **~118K stars** (hit 100K in March 2026, faster than PyTorch/TensorFlow; the ggml C/C++ tensor library is the substrate under Ollama, LM Studio, and much else)
- **License:** MIT
- **What it does:** CPU-first (with optional GPU offload) LLM inference in portable C/C++. GGUF quantized weights (down to ~2-bit), runs on laptops, ARM, Apple Silicon (Metal), CUDA, Vulkan, even Raspberry Pi. Ships `llama-server` with an OpenAI-compatible API + grammar-constrained sampling (GBNF).
- **Where it fits in OUR platform:** **The no-GPU / edge / overflow brain.** When workers run on CPU-only scrape boxes, cheap cloud instances, or operator laptops, llama.cpp lets a 3–8B model do light classification and triage without any GPU. Also the **burst-overflow tier**: when the GPU pool is saturated, spill low-priority jobs to CPU llama.cpp replicas rather than queueing. GBNF grammar sampling gives the same schema-valid output guarantee as SGLang/vLLM, so CPU-extracted records are still clean for fusion.
- **Hardware/cost:** Runs anywhere; quantized 7B fits in ~5–6GB RAM. Latency/throughput far below GPU engines — fine for elastic, latency-tolerant background work, not the hot inner loop. Effectively free to scale horizontally on commodity CPU.
- **Maturity:** Extremely high — the most-starred, most-portable runtime; foundational to the ecosystem.
- **Integration note:** Run `llama-server -m model.gguf` per box; same OpenAI client. Register CPU replicas in the worker pool as a **low-cost / high-latency method** the bandit router only picks when GPU lanes are hot or the job is cheap — its AIMD-style cost model naturally routes here under load.

### Ollama
- **Repo:** https://github.com/ollama/ollama — **~172K stars** (52M monthly downloads; the default "run a model locally" tool of 2026; wraps llama.cpp/ggml)
- **License:** MIT
- **What it does:** Dead-simple local model manager + runner. `ollama pull qwen3` → `ollama run`. One-line model fetch, automatic quant selection, OpenAI-compatible server, model library, hot model-swapping, GPU+CPU. Built on llama.cpp.
- **Where it fits in OUR platform:** **The dev/prototyping and single-node brain.** Where vLLM/SGLang are the production fleet, Ollama is how engineers iterate on prompts locally and how *small* deployments (a single scrape VM, an operator workstation, a Nordic-region edge node) run a brain with zero ops. Great for the **router's "cheap probe" lane** on modest hardware and for offline/air-gapped runs where no prompt may leave the box. Its painless model-swap makes it the natural home for the **model-routing experiments** (try Qwen vs Phi vs Gemma on a task without rebuilding infra).
- **Hardware/cost:** CPU or single GPU; auto-picks a quant that fits. Convenience-over-peak-throughput — not the engine for thousands of concurrent requests (use vLLM there). Free.
- **Maturity:** Very high; the most popular local-LLM entry point.
- **Integration note:** Already covered by the in-house `openclaw-setup` skill (Ollama is the free uncapped local backend there) — reuse that operational knowledge. Expose `http://host:11434/v1`; identical client code to vLLM means **promoting a model from Ollama-prototype to vLLM-production is a config change, not a rewrite.**

### LM Studio
- **Site/repo:** https://lmstudio.ai/ (GUI app is **closed source**; underlying engines llama.cpp + Apple MLX are OSS; `lms` CLI + `llmster` daemon are closed-source binaries, free for personal use)
- **License:** **Proprietary (free tier)** — *not* OSS. Flag this: it doesn't meet the "free/OSS" bar the way the others do.
- **What it does:** Polished desktop GUI for discovering, downloading (GGUF/MLX), and running models, with a built-in model browser, visual parameter controls, and an OpenAI-compatible local server. v0.4+ adds the headless `llmster` daemon so it can run server-side/in CI without the GUI.
- **Where it fits in OUR platform:** **Human-in-the-loop / operator console, not pipeline infra.** Useful for an *operator* to manually eyeball a model's behavior, sanity-check a prompt, or compare quants visually before we commit. **Do not put it in the automated worker pool** — it's closed-source, the licensing is murkier at scale, and Ollama/llama.cpp do the same headless job openly. Keep it as a convenience tool on a workstation; prefer the OSS engines for anything the platform depends on.
- **Hardware/cost:** Same local-hardware class as Ollama; free for personal use (review terms before any commercial/server deployment).
- **Maturity:** High as a product; closed-source means less suitable as a load-bearing dependency.
- **Integration note:** If used at all, treat the `llmster` OpenAI endpoint like any other backend — but **default to Ollama** for the same role to stay fully OSS and license-clean.

### HF Text-Generation-Inference (TGI)
- **Repo:** https://github.com/huggingface/text-generation-inference — **⚠️ ARCHIVED by Hugging Face on 2026-03-21 (read-only).**
- **License:** v1.0+ under **HFOIL 1.0** (restrictive Hugging Face Optimized Inference License); last Apache-2.0 release was **v0.9.4**.
- **What it does:** Production LLM serving toolkit (continuous batching, tensor parallelism, quant) powering HF Inference Endpoints. Historically a strong vLLM competitor.
- **Where it fits in OUR platform:** **Do not adopt for new build.** Two disqualifiers: (1) the repo is archived/no longer developed, and (2) the post-0.9.4 license is non-OSS and restrictive — wrong fit for a platform whose moat is clean, license-clean provenance. **vLLM and SGLang supersede it entirely** for our serving needs with permissive Apache-2.0 licensing and active development. Listed here only so a future reader doesn't reach for it.
- **Hardware/cost:** GPU, comparable class — moot given the above.
- **Maturity:** Was high; now frozen. Migrate any TGI mental models to vLLM.
- **Integration note:** N/A — **explicitly excluded** from the worker pool. If you find a reference to TGI in old notes, read it as "use vLLM instead."

---

### Engine selection cheat-sheet

| Need | Engine | Why |
|---|---|---|
| Production hot loop, thousands of concurrent calls | **vLLM** | Continuous batching, throughput/$ leader, Apache-2.0 |
| Repetitive schema extraction over millions of pages | **SGLang** | RadixAttention prefix cache + FSM-guaranteed JSON |
| CPU-only boxes, edge nodes, GPU-overflow spill | **llama.cpp** | Runs anywhere, GBNF grammar, MIT |
| Single node, dev/prototyping, air-gapped, model-swap experiments | **Ollama** | One-line ops, MIT, reuse `openclaw-setup` |
| Operator eyeballing / manual compare | LM Studio | GUI only — **closed source, keep off the pipeline** |
| (legacy) | ~~TGI~~ | **Archived + non-OSS license — excluded** |

---

## Part 2 — Open models (the brain weights loaded into the engines)

Sizing rule of thumb (4-bit quant, the practical default): **VRAM ≈ params × ~0.6GB** (7B≈5–6GB, 14B≈10GB, 32B≈18–20GB, 70B≈36–40GB). MoE models cost VRAM by *total* params but compute by *active* params — cheap to run, expensive to hold.

### Qwen 3 (and 2.5) — Alibaba
- **Sizes:** Dense 0.6B / 1.7B / 4B / 8B / 14B / 32B; MoE 30B-A3B (3B active) and 235B-A22B (22B active). (Qwen3.5, Feb 2026, scales to 397B/17B-active.) Trained on ~36T tokens, **119 languages** — strong on Nordic + DE/FR/IT.
- **License:** **Apache 2.0** (open weights, unrestricted commercial use).
- **Where it fits as a worker brain:** **The default generalist worker model.** Best-in-class open multilingual quality at every size, permissive license, and explicit **agentic/tool-calling** strength. Run **Qwen3-7B/14B on vLLM** as the everyday classify/extract/route brain; **30B-A3B MoE** when you want 30B-ish quality at ~3B compute cost (ideal for the throughput fabric — cheap per token, fits a single big GPU). The multilingual reach is decisive for a *Nordic+EU* platform parsing pages in 20+ languages.
- **Hardware:** 7B→single 24GB GPU serves a fleet (vLLM) or CPU (llama.cpp); 30B-A3B→one 24–48GB GPU; 235B→multi-GPU node.
- **Integration note:** Make **Qwen3-14B (Apache-2.0)** the router's baseline arm for general extraction/classification; benchmark 30B-A3B for the high-volume lane.

### Llama 4 (Scout / Maverick) + Llama 3.3 70B — Meta
- **Sizes:** **Scout** 109B total / 17B active (MoE, **10M-token context**); **Maverick** 400B total / 17B active (MoE, 1M context). Prior gen **Llama 3.3 70B** dense remains a workhorse. (Behemoth ~2T teacher paused May 2026, not released.)
- **License:** **Llama 4 Community License** — commercial-OK *with caveats*: can't use outputs to train competing models; >700M-MAU firms need a separate Meta license. **Not fully permissive** — weaker than Apache-2.0 for us.
- **Where it fits as a worker brain:** **The long-context specialist.** Scout's 10M-token window is the standout: feed an *entire* company website / multi-page registry filing / long PDF dump in one shot for whole-document extraction — no chunking, no lost cross-references. 17B active params mean it runs at ~17B cost despite its size. Use Scout for the **"read the whole site at once"** extraction jobs the chunk-and-stitch pipeline struggles with.
- **Hardware:** MoE = high VRAM to *hold* (109B/400B total) but cheap to *run* (17B active) → needs a multi-GPU node or heavy quant; Llama-3.3-70B fits ~2×24GB or one 48GB at 4-bit.
- **Integration note:** Provision Scout on a dedicated long-context node; the router escalates to it only when input length exceeds what Qwen-14B handles well (cost-aware routing). Mind the license caveat — fine for *our* data extraction, just don't use outputs to train a rival model.

### DeepSeek V3 / R1
- **Sizes:** Both **671B MoE, 37B active**. **R1** = flagship reasoning model; distills exist (R1-Distill 7B/14B/32B/70B) for consumer hardware.
- **License:** **MIT** (code) + open model agreement (weights) — commercially usable, **permissive**.
- **Where it fits as a worker brain:** **The hard-reasoning escalation tier + a free distillation teacher.** Full 671B R1 is *not* practical to self-host (needs ~700GB at FP8, data-center scale) — skip it for the inner loop. What we actually use: (1) the **R1-Distill models** (e.g. 32B at ~17.5GB, 70B at ~36.5GB) as the **reasoning brain** for the gnarliest decisions — ambiguous entity resolution, "are these two companies the same legal entity across two national registries?", multi-hop disambiguation feeding [`fusion-confidence`](../../docs/architecture/); (2) R1 as a **teacher** to distill our own task-specific small models, cheaply and license-cleanly (MIT).
- **Hardware:** Full model = multi-node, avoid. **Distill-32B → one 24GB GPU; Distill-70B → 2×GPU or 64GB Mac Studio.**
- **Integration note:** Wire **R1-Distill-32B** as the router's "think hard" arm — invoked only when the cheap Qwen/Phi arm returns low confidence. Reasoning is slower; gate it behind a confidence threshold so it's not in the hot path.

### Mistral Small 3 (24B) + Mixtral 8x7B / 8x22B
- **Sizes:** **Mistral Small 3 = 24B dense** (latency-optimized, ~150 tok/s, ~81% MMLU, on par with Llama-3.3-70B but 3x faster); **Mixtral 8x7B** (47B total / ~13B active) and **8x22B** (141B total / 39B active) MoE.
- **License:** **Apache 2.0** (Small 3, both Mixtrals) — fully permissive. (Note: older Mistral Small variants used a research-only license; Small **3** fixed that.)
- **Where it fits as a worker brain:** **The low-latency function-calling worker.** Small 3 is purpose-built for "rapid function execution in agentic workflows" — exactly the [`adaptive-engine`](../../docs/architecture/) loop where the brain decides *which tool/method to fire next* and must return fast. Its 70B-class quality at 3x speed makes it a strong middle arm: heavier than Qwen-7B, far cheaper than 70B, Apache-2.0. Mixtral 8x7B is a proven, efficient MoE fallback.
- **Hardware:** Small 3 (24B) → one 24GB GPU at 4-bit (vLLM) and serves the fleet; Mixtral 8x22B → multi-GPU.
- **Integration note:** Strong candidate for the **router's decision/orchestration brain** (fast tool-selection) distinct from the extraction brain — its function-calling reliability matters where Qwen does the bulk extraction.

### Gemma 3 (and 2) — Google
- **Sizes:** **1B / 4B / 12B / 27B**; 1B text-only, **4B/12B/27B are multimodal (SigLIP vision encoder)**; 128K context, 140+ languages, structured outputs + function calling.
- **License:** **Gemma license** (permissive for most commercial use; not OSI-Apache but broadly usable — read terms).
- **Where it fits as a worker brain:** **The vision-capable small worker.** The differentiator vs Qwen/Mistral is built-in **vision** at small sizes — directly relevant to the [`ui-automation`](../../docs/) / OCR-exfiltration path for **primary official sources with no API** (e.g. DE Handelsregister, IT Registro Imprese), where a worker must *read a rendered page/scanned doc/CAPTCHA-free screenshot* and extract fields. Gemma-3-4B/12B can do "look at this screenshot, return the structured fields" on modest hardware — a cheaper alternative than a dedicated OCR+LLM two-step for some layouts. (Reminder: vision/UI-automation is for **primary official sources only**, never competitor tools — per [`COMPLIANCE.md`](../../docs/COMPLIANCE.md).)
- **Hardware:** 4B → CPU/small GPU (llama.cpp/Ollama); 27B → one 24GB GPU.
- **Integration note:** Deploy **Gemma-3-12B** as the multimodal lane for screenshot/document-image extraction in the official-registry scrapers; route text-only work to Qwen/Mistral.

### Phi-4 (14B) + Phi-4-reasoning / -mini — Microsoft
- **Sizes:** **Phi-4 = 14B** (16K context); **Phi-4-reasoning 14B**; **Phi-4-mini**; **Phi-4-reasoning-vision-15B** (multimodal, Mar 2026). Punches at 70B-class on math/code/reasoning benchmarks.
- **License:** **MIT** (all Phi-4 variants) — maximally permissive.
- **Where it fits as a worker brain:** **The efficient reasoning small-model + edge brain.** 14B with 70B-class reasoning under an MIT license is the sweet spot for a **cheap, dense, fast classifier/validator** that still reasons — e.g. the confidence-scoring / data-validation step in [`fusion-confidence`](../../docs/architecture/) ("does this extracted record look internally consistent?"). Small enough to run many replicas on modest GPUs or even CPU (llama.cpp), MIT means zero license friction for fine-tuning a task-specific variant. A great **default for the router's "smart but cheap" arm** before escalating to R1-Distill.
- **Hardware:** 14B → ~10GB at 4-bit, one consumer GPU serves a fleet; runs on CPU for overflow.
- **Integration note:** Use **Phi-4-14B (MIT)** as the validation/scoring brain and as the base we **fine-tune** for our specific extraction schemas (MIT + small size = cheap, owned, reproducible).

---

### Model-routing map (how the worker pool picks a brain)

| Task in the pipeline | Primary brain | Escalation | Engine |
|---|---|---|---|
| Page-type classification, light triage | Qwen3-7B / Phi-4-mini | — | vLLM / llama.cpp (overflow) |
| Bulk field extraction → JSON schema | **Qwen3-14B** (or 30B-A3B) | Mistral Small 3 | **SGLang** (FSM JSON) |
| Whole-site / long-PDF single-shot read | **Llama 4 Scout** (10M ctx) | — | vLLM (long-ctx node) |
| Tool/method selection in the adaptive loop | **Mistral Small 3** (fast func-calling) | Qwen3-14B | vLLM |
| Screenshot / document-image extraction (official registries) | **Gemma-3-12B** / Phi-4-vision | — | vLLM / Ollama |
| Hard entity-resolution / disambiguation | **DeepSeek R1-Distill-32B** | full reasoning loop | vLLM (gated by confidence) |
| Record validation / consistency scoring | **Phi-4-14B** | R1-Distill | vLLM / llama.cpp |

The [adaptive-engine](../../docs/architecture/) bandit treats each (model, engine) pair as an arm with per-host success/latency/cost stats and learns which brain wins where — cheap arms first, reasoning arms only on low confidence.

---

## Compliance note

Everything here is **our own** infrastructure running **open weights** on **our** hardware — squarely in-scope. None of it touches the TIER-5 line: these brains extract from **primary/official sources** and our own pipeline, never to bulk-exfiltrate a competitor's database behind their login. Local inference is also a GDPR-by-design win — **no personal data leaves our perimeter** to a third-party LLM API, and every extracted field can still be tagged with source + lawful-basis + timestamp per [`COMPLIANCE.md`](../../docs/COMPLIANCE.md).

## Sources
- vLLM — https://github.com/vllm-project/vllm
- SGLang — https://github.com/sgl-project/sglang
- llama.cpp — https://github.com/ggml-org/llama.cpp
- Ollama — https://github.com/ollama/ollama
- LM Studio — https://lmstudio.ai/
- HF Text-Generation-Inference (archived) — https://github.com/huggingface/text-generation-inference
- Qwen3 — https://github.com/QwenLM/Qwen3 · https://qwenlm.github.io/blog/qwen3/
- Llama 4 — https://huggingface.co/blog/llama4-release
- DeepSeek V3/R1 — https://github.com/deepseek-ai/DeepSeek-V3 · https://huggingface.co/deepseek-ai/DeepSeek-R1
- Mistral Small 3 / Mixtral — https://mistral.ai/news/mistral-small-3/ · https://mistral.ai/news/mixtral-8x22b/
- Gemma 3 — https://huggingface.co/blog/gemma3 · https://ai.google.dev/gemma/docs/releases
- Phi-4 — https://venturebeat.com/ai/microsoft-makes-powerful-phi-4-model-fully-open-source-on-hugging-face
