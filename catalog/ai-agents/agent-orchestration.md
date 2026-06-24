# AI Agent Frameworks — Orchestration & Worker Brains

> Catalog of free / open-source AI agent frameworks evaluated as the "brains" for the Nordic-EU data-harvesting platform.
> Scope: orchestrating the adaptive router + worker pool, driving stubborn no-API UIs via vision/AI clicks, cheap local inference, and structured extraction.
> All star counts confirmed via web search (June 2026); they move fast — treat as approximate.

## Compliance reminder (read first)

Per `docs/COMPLIANCE.md`, AI-driven UI automation + OCR/vision is for **primary official sources with no API** (DE Handelsregister, IT Registro Imprese, etc.) — **NOT** for bulk extraction behind competitor logins (Apollo/ZoomInfo/Cognism = Tier 5, benchmark-only). Every framework below is scoped to lawful T1–T4 harvesting + competitor *feature* intelligence. The agent layer must respect robots.txt, rate limits, and `429`/`Retry-After`, and must tag every personal-data field with source + lawful basis + last-verified timestamp.

## Where the platform needs an AI brain

| Platform role | What it needs | Best-fit tools (this batch) |
|---|---|---|
| **Adaptive router** (decides per-source strategy, escalates on block) | Stateful graph, retries, human-in-loop, checkpointing | **LangGraph**, Semantic Kernel |
| **Worker pool — structured extraction** (page/PDF → typed record) | Schema-enforced output, validation, retries | **Pydantic-AI**, LlamaIndex, DSPy |
| **Worker pool — stubborn UI** (no-API registries, AI clicks) | VLM + browser control, screenshot loop | **SmolAgents** (+Helium), OpenHands |
| **Worker pool — RAG / fusion** (dedup, entity resolution over docs) | Retrieval pipelines, rerank, doc stores | **Haystack**, LlamaIndex |
| **Cheap local inference** (high-volume, no per-token cost) | Runs against Ollama/vLLM, small models | **SmolAgents**, Pydantic-AI, Agno |
| **Self-optimization** (auto-tune prompts/extractors per source) | Compile + optimize against a metric | **DSPy** |
| **Multi-agent research/profiling** (competitor feature-intel) | Role-playing agents, conversation | CrewAI, AutoGen/AG2 |

---

## 1. LangGraph

- **Repo:** https://github.com/langchain-ai/langgraph — ~35.5k stars
- **License:** MIT
- **What it does:** Low-level, stateful orchestration framework that models an agent as a **graph** of nodes/edges with a typed shared state. Built-in persistence/checkpointing, time-travel, interrupts (human-in-the-loop), streaming, retries, and durable long-running execution. Production-trusted (Klarna, Replit, Elastic).
- **Fit in our platform:** **The adaptive router.** A harvest job = a graph: `classify-source → pick-strategy → fetch → detect-block → (escalate to UI/VLM | rotate proxy | back off) → extract → validate → persist`. Checkpointing makes long multi-country sweeps resumable; interrupts give the operator the LinkedIn/per-campaign sign-off the compliance doc requires. State machine cleanly encodes the `429`/`Retry-After` adaptive-limiter behavior.
- **Hardware/cost:** Library only; zero infra cost. Runs against any LLM incl. local Ollama. LangGraph Platform (hosted) is optional and paid — **we self-host, skip it.**
- **Maturity:** High. Most-trusted orchestration substrate; large ecosystem, frequent releases.
- **Integration note:** Python + JS (`langgraphjs`). Define the router as a `StateGraph`; each worker-pool capability (extractor, UI-driver, RAG) becomes a node or a subgraph invoked as a tool. Pairs naturally with Pydantic-AI/DSPy nodes. Some coupling to the LangChain ecosystem, but the graph core is usable standalone.

## 2. CrewAI

- **Repo:** https://github.com/crewAIInc/crewAI — ~47.8k stars
- **License:** MIT
- **What it does:** Higher-level framework for orchestrating **role-playing autonomous agents** ("crews") that collaborate on a task, plus a lighter "Flows" event-driven mode. Independent of LangChain. Strong DX for "give each agent a role + goal + tools."
- **Fit in our platform:** **Multi-agent research / competitor feature-intel** (Tier-5 *legitimate* profiling: one agent reads pricing pages, one summarizes coverage claims, one benchmarks our sample accounts). Less ideal as the core router — the role-play abstraction is looser than LangGraph's explicit state machine, and we want deterministic, auditable control for the harvest path.
- **Hardware/cost:** Library only; model-agnostic incl. local models. Optional paid CrewAI enterprise/control-plane — not needed.
- **Maturity:** High adoption, very large community. Fast-moving API; pin versions.
- **Integration note:** Use selectively for the analyst/research lane, **not** the harvest critical path. Can be wrapped as a LangGraph node if we want crews-on-demand.

## 3. Microsoft AutoGen / AG2

- **AutoGen repo:** https://github.com/microsoft/autogen — ~50k stars, **MIT**, now **maintenance mode** (community-managed, no new features).
- **AG2 repo (active fork):** https://github.com/ag2ai/ag2 — ~4–5k stars, **Apache-2.0** (original MIT base + Apache modifications). AG2 inherited the `pyautogen`/`autogen` PyPI names and Discord; original creators left Microsoft to run it.
- **What it does:** Conversational **multi-agent** framework — agents (incl. a `UserProxyAgent` that can execute code) talk in structured group chats to solve tasks. Pioneered the multi-agent-conversation pattern.
- **Fit in our platform:** Same lane as CrewAI — multi-agent reasoning/research, code-executing agents for ad-hoc analysis. Code-executor agents could drive scripted extraction, but for our deterministic router LangGraph is a better fit.
- **Hardware/cost:** Library only; model-agnostic incl. local.
- **Maturity:** AutoGen = stable but **frozen** → do not build new work on `microsoft/autogen`. **AG2** is the living line but far smaller/younger; the fork split fragmented the community (AutoGen → AG2 → Microsoft Agent Framework / Semantic Kernel convergence). **Adopt cautiously**, prefer AG2 if used.
- **Integration note:** Treat as optional research-lane tool. Watch the AutoGen→Semantic-Kernel/Microsoft-Agent-Framework consolidation before committing.

## 4. OpenHands (formerly OpenDevin)

- **Repo:** https://github.com/OpenHands/OpenHands (org All-Hands-AI) — ~65k+ stars
- **License:** MIT
- **What it does:** AI software-engineering agent platform — agents act across a real codebase/sandbox: run a browser, execute shell, edit files, call APIs, complete whole engineering tasks in a sandboxed runtime.
- **Fit in our platform:** Two angles. (a) **Stubborn-UI / browser worker** — its sandboxed browser+computer agent can drive a no-API registry behind a real browser. (b) **Meta / self-building** — point it at *our own* repo to scaffold new source adapters. Heavyweight for a per-page worker, but valuable as a sandboxed "do a hard thing in a real environment" escalation target.
- **Hardware/cost:** Heaviest in this batch — wants Docker sandboxes; non-trivial CPU/RAM per agent; benefits from a strong model. Self-hostable and free; cloud offering is paid.
- **Maturity:** Very high momentum, large community; a new V1 `software-agent-sdk` exists for embedding.
- **Integration note:** Wrap as a **sandboxed escalation worker** the router calls only when lighter extractors fail (expensive, isolate it). Don't make it the default worker.

## 5. HuggingFace SmolAgents

- **Repo:** https://github.com/huggingface/smolagents — ~28k stars
- **License:** Apache-2.0
- **What it does:** Barebones "agents that think in **code**" — the agent writes Python actions instead of JSON tool-calls (`CodeAgent`). Core logic is ~1k LOC. First-class **VLM/vision** support and a built-in **vision web-browser** example using **Helium/Selenium** (screenshot → VLM → `click`/`scroll`).
- **Fit in our platform:** **The stubborn-UI worker + cheap local lane.** This is the clean answer to "drive a no-API registry via AI clicks": VLM sees the screenshot, decides the click, Helium executes — exactly the Handelsregister / Registro-Imprese case. Minimal, hackable, and runs against **any model incl. local Ollama/Inference**, so high-volume extraction has no per-token cost. Code-action style also makes structured scraping concise.
- **Hardware/cost:** Tiny framework footprint. Vision web-browsing needs a capable VLM (best results with strong VLMs; can run local Qwen-VL on a GPU box, or hosted for hard pages). Browser needs Selenium/Chromedriver.
- **Maturity:** Maturing fast, strong HF backing, active releases. Smaller ecosystem than LangChain but deliberately minimal.
- **Integration note:** Implement the UI-driver node as a SmolAgents `CodeAgent` + Helium, invoked by the LangGraph router on `needs-browser`/`block-detected`. Keep a local-model config for volume + a hosted-VLM config for the hardest pages.

## 6. LlamaIndex (agents)

- **Repo:** https://github.com/run-llama/llama_index — ~50k stars
- **License:** MIT
- **What it does:** Data/agent framework centered on **ingestion, indexing, retrieval, and document workflows**; now positions itself as a "document agent & OCR platform." Event-driven `Workflows` + agent abstractions over rich connectors and vector stores.
- **Fit in our platform:** **RAG / document-extraction worker + fusion support.** Strong for turning messy registry filings, PDFs, and annual reports into retrievable, queryable structured data, and for entity-resolution/dedup over the harvested corpus. Its OCR/doc-parsing pipeline is directly useful for scanned T1 documents.
- **Hardware/cost:** Library; cost = embeddings + a vector store (can be local, e.g. Postgres/pgvector, Qdrant). Some premium parsing (LlamaParse/LlamaCloud) is a paid hosted add-on — **prefer OSS parsers** to stay zero-cost.
- **Maturity:** Very high; one of the largest, most stable data-framework ecosystems.
- **Integration note:** Use as the **retrieval/doc lane**, complementary to (not competing with) the LangGraph router. Wrap a `Workflow` as a router tool for "parse this filing → typed record."

## 7. Haystack (deepset)

- **Repo:** https://github.com/deepset-ai/haystack — ~25k stars
- **License:** Apache-2.0
- **What it does:** Production-grade, modular **pipeline** orchestration for retrieval, routing, memory, and generation — explicit, composable components for RAG, semantic search, and agent workflows. EU vendor (deepset, Germany).
- **Fit in our platform:** **Production RAG/fusion pipelines** where we want explicit, auditable component graphs (matters for provenance/GDPR traceability). Good fit for the dedup/entity-resolution + semantic-search layer over harvested data; the explicit-pipeline model maps well to "show, per field, where it came from."
- **Hardware/cost:** Library; same profile as LlamaIndex (embeddings + vector store, can be fully local/OSS).
- **Maturity:** High; battle-tested in enterprise search, strong docs, stable releases.
- **Integration note:** Choose Haystack **or** LlamaIndex for the RAG lane to avoid redundancy — Haystack if we prioritize explicit/auditable pipelines and EU vendor alignment; LlamaIndex if we prioritize the largest connector/OCR ecosystem. Either wraps as a router tool.

## 8. Microsoft Semantic Kernel

- **Repo:** https://github.com/microsoft/semantic-kernel — ~27.9k stars
- **License:** MIT
- **What it does:** Model-agnostic SDK to build/orchestrate **agents and multi-agent systems**, with planners, plugins/skills, memory, and strong **.NET + Python + Java** support. Microsoft is converging AutoGen's ideas into SK / the Microsoft Agent Framework.
- **Fit in our platform:** Alternative orchestration substrate, attractive **only if we go .NET-heavy** or are deep in Azure (the memory layer already lives in Fabric/Azure). Plugin model is clean for wrapping tools. For a Python-first stack, LangGraph's explicit state machine + checkpointing is the stronger router.
- **Hardware/cost:** Library; model-agnostic incl. local; integrates tightly with Azure OpenAI.
- **Maturity:** High, enterprise-backed, stable; but the MS agent stack is mid-consolidation (SK ⇄ AutoGen ⇄ Agent Framework).
- **Integration note:** Keep as the **Azure/.NET fallback** orchestrator given our existing Azure/Fabric footprint. Not the default if the worker pool is Python.

## 9. DSPy (Stanford NLP)

- **Repo:** https://github.com/stanfordnlp/dspy — ~35k stars
- **License:** MIT
- **What it does:** "Programming, not prompting." Declarative modules + **optimizers/compilers** that auto-tune prompts (and few-shot examples) against a metric, instead of hand-written brittle prompts. Self-improving pipelines.
- **Fit in our platform:** **The self-optimization layer for extractors.** Each source has a different layout; DSPy lets us *compile* an extractor against a labeled sample and a quality metric, then re-optimize when a site changes (self-adapting harvesting — the platform's core promise). Also enables cheap-model + optimized-prompt to match a bigger model's accuracy, cutting cost.
- **Hardware/cost:** Library; the optimization step costs some LLM calls up front, then the compiled program runs cheap (ideal with local models for volume).
- **Maturity:** High and rising; strong research pedigree, active releases.
- **Integration note:** Use DSPy to **build/optimize the extraction modules** that Pydantic-AI/LangGraph nodes then execute in production. Store compiled programs per-source; re-compile on drift. Highest-leverage "self-adapting" component in this batch.

## 10. Pydantic-AI

- **Repo:** https://github.com/pydantic/pydantic-ai — ~17.9k stars
- **License:** MIT
- **What it does:** Type-safe agent framework from the Pydantic team — "FastAPI feeling for GenAI." Agents with **schema-validated structured outputs** (Pydantic models), typed tools/deps, retries on validation failure, and model-agnostic providers.
- **Fit in our platform:** **The default structured-extraction worker.** Page/PDF/registry response → validated Pydantic record with automatic re-ask on schema violation = exactly the typed, provenance-tagged output the platform needs (each field a typed model attribute we annotate with source + lawful basis). Lightweight, model-agnostic (incl. local), minimal lock-in.
- **Hardware/cost:** Library; near-zero overhead; runs against any model incl. local Ollama/vLLM.
- **Maturity:** Maturing fast, strong backing (Pydantic = ubiquitous in Python data stack), stabilizing API.
- **Integration note:** Make Pydantic-AI the **extraction node type** inside the LangGraph router; define one canonical Pydantic schema per record type (company, officer, filing) and reuse across sources. Pairs perfectly with DSPy (DSPy optimizes the prompt, Pydantic-AI enforces the output).

## 11. Agno (formerly Phidata)

- **Active repo:** https://github.com/agno-agi/agno — ~39.8k stars (predecessor `agno-agi/phidata` archived)
- **License:** Reported as **Apache-2.0 / MPL-2.0** across sources — **verify the exact license in-repo before adopting** (MPL is weak-copyleft; matters for a commercial product).
- **What it does:** High-performance Python framework for building/running/managing agents, with memory, knowledge (RAG), tools, and **AgentOS** — a FastAPI-based runtime for production multi-agent serving. Emphasis on speed and low instantiation overhead.
- **Fit in our platform:** Candidate **runtime/serving layer** for the worker pool (AgentOS = ready-made FastAPI host with monitoring) and a fast multi-agent option. Overlaps heavily with LangGraph+Pydantic-AI; its edge is the batteries-included runtime + performance.
- **Hardware/cost:** Library + optional self-hosted AgentOS runtime; model-agnostic incl. local. Low per-agent overhead (its selling point for high concurrency).
- **Maturity:** High adoption; rebrand (Phidata→Agno) + 2.x AgentOS churn means some API instability.
- **Integration note:** Evaluate AgentOS as the **worker-pool host** if we want serving + memory + monitoring out of the box, rather than assembling it. **License must be confirmed first.**

## 12. Atomic Agents

- **Repo:** https://github.com/BrainBlend-AI/atomic-agents — ~5.8k stars
- **License:** MIT
- **What it does:** Lightweight, **modular** framework ("building AI agents, atomically") built on Instructor + Pydantic — strict input/output schemas per atomic agent, composable into pipelines. Ships `atomic-assembler` (CLI), `atomic-forge` (tools).
- **Fit in our platform:** Same niche as Pydantic-AI — **schema-strict structured extraction** as small composable units. Philosophy (atomic, typed, predictable) aligns well with auditable provenance. But smallest community here, so higher maintenance risk.
- **Hardware/cost:** Library; minimal; model-agnostic incl. local.
- **Maturity:** Lower (smallest stars/community). Solid design, thinner ecosystem.
- **Integration note:** Treat as a **fallback/alternative to Pydantic-AI**, not a parallel adoption — picking both would duplicate the structured-extraction lane. Prefer Pydantic-AI for ecosystem; revisit Atomic Agents only if its atomic-pipeline model proves a better fit.

---

## Recommended stack (this batch)

```
                         ┌─────────────────────────────┐
   adaptive router  →    │  LangGraph (StateGraph)     │  stateful, checkpointed,
                         │  classify→strategy→fetch→   │  human-in-loop sign-off
                         │  detect-block→escalate      │
                         └──────────────┬──────────────┘
                                        │ invokes per source/state
        ┌───────────────┬───────────────┼────────────────┬───────────────┐
        ▼               ▼               ▼                ▼               ▼
  Pydantic-AI      SmolAgents       LlamaIndex /      DSPy           OpenHands
  structured       VLM + Helium     Haystack          compiles &     sandboxed
  extraction       AI-click UI      RAG / OCR /       optimizes      escalation
  (typed record)   (no-API regs)    entity-fusion     extractors     (hard cases)
        │                                              │
        └──────────  cheap LOCAL inference (Ollama/vLLM) for volume  ──────────┘
```

- **Build on:** LangGraph (router), Pydantic-AI (extraction), SmolAgents (UI/VLM + local), DSPy (self-optimization), LlamaIndex **or** Haystack (RAG/fusion).
- **Escalation only:** OpenHands (sandboxed, expensive).
- **Conditional:** Semantic Kernel (Azure/.NET fallback), Agno (runtime — license check first).
- **Selective / research lane:** CrewAI, AutoGen/AG2 (competitor feature-intel, not harvest path).
- **Fallback:** Atomic Agents (alt to Pydantic-AI; don't adopt both).

## Sources

- [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)
- [microsoft/autogen](https://github.com/microsoft/autogen) · [ag2ai/ag2](https://github.com/ag2ai/ag2)
- [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands)
- [huggingface/smolagents](https://github.com/huggingface/smolagents) · [vision web-browser example](https://huggingface.co/docs/smolagents/en/examples/web_browser)
- [run-llama/llama_index](https://github.com/run-llama/llama_index)
- [deepset-ai/haystack](https://github.com/deepset-ai/haystack)
- [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel)
- [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy)
- [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai)
- [agno-agi/agno](https://github.com/agno-agi/agno)
- [BrainBlend-AI/atomic-agents](https://github.com/BrainBlend-AI/atomic-agents)

_Star counts confirmed via web search, June 2026; approximate and fast-moving._
