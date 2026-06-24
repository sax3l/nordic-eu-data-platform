# Method runbooks

One runbook per harvesting method. Each is short and operational: what it does, install, a working snippet, speed/accuracy, gotchas, and **where it sits in the fallback chain**. The `method:` field in [`../../sources/sources.yaml`](../../sources/sources.yaml) points here.

## The fallback chain (sense → adapt → escalate)

The adaptive router escalates only as far as it must — cheapest method that *currently works* wins, and the choice re‑tunes per host as conditions change.

```
              ┌─────────────────────────── HTTP tier (cheap, fast) ───────────────────────────┐
 static html  │ curl_cffi (TLS impersonate) + selectolax/lxml                                  │
 hidden API   │ direct JSON / __NEXT_DATA__ / GraphQL endpoint                                 │
              └───────────────────────────────────────────────────────────────────────────────┘
                         │ blocked? 403 / 429 / CF challenge / empty render
                         ▼
              ┌────────────────────── CF / anti‑bot tier ─────────────────────────────────────┐
              │ cloudscraper → FlareSolverr → CycleTLS → camoufox / nodriver → botasaurus      │
              └───────────────────────────────────────────────────────────────────────────────┘
                         │ still blocked / JS‑heavy / login
                         ▼
              ┌────────────────────── browser tier (slow, strong) ────────────────────────────┐
              │ CloakBrowser (C++ patched Chromium, 30/30 benchmarks)                          │
              │ + coherent identity profiles + proxy rotation                                  │
              │ + Crawelee orchestrator (queuing, auto-retry)                                  │
              └───────────────────────────────────────────────────────────────────────────────┘
                         │ stateful portal / no API / visual‑only
                         ▼
              ┌────────────────────── AI‑Agent tier ───────────────────────────────────────────┐
              │ Browser‑Use / Skyvern / Stagehand (LLM‑driven browser, self‑healing selectors) │
              │ + OCR cascade (PaddleOCR → Surya → GOT‑OCR2 → Vision LLM)                      │
              └───────────────────────────────────────────────────────────────────────────────┘
                         │ login‑gated / enterprise portal / agent failed
                         ▼
              ┌──────────────── licensed / RPA tier (seat‑limited) ───────────────────────────┐
              │ Screaming Frog (bulk crawl) · Sequentum · UiPath · Ranorex                     │
              │ + Unstructured.io (document parsing before OCR/NER)                            │
              └───────────────────────────────────────────────────────────────────────────────┘
```

Every tier reports `success / latency / block` back to the router so the bandit can prefer whatever is winning right now for that host.

## Runbook Index

### HTTP Tier
| Runbook | Tool | Status |
|---|---|---|
| `curl-cffi.md` | curl_cffi TLS impersonation | planned |
| `selectolax.md` | selectolax/lxml parsing | planned |

### CF / Anti-Bot Tier
| Runbook | Tool | Status |
|---|---|---|
| `cloudscraper.md` | cloudscraper | planned |
| [`flaresolverr.md`](flaresolverr.md) | FlareSolverr (Docker CF solver) | **done** |
| `cycletls.md` | CycleTLS | planned |
| `camoufox.md` | Camoufox (Firefox stealth) | planned |
| `nodriver.md` | nodriver / Patchright | planned |
| `botasaurus.md` | Botasaurus | planned |

### Browser + Orchestration Tier
| Runbook | Tool | Status |
|---|---|---|
| [`cloakbrowser.md`](cloakbrowser.md) | CloakBrowser (C++ stealth Chromium) | **done** |
| [`crawlee.md`](crawlee.md) | Crawlee (prod crawler framework) | **done** |
| [`stealth-bypass-chain.md`](stealth-bypass-chain.md) | Complete anti-detection strategy | **done** |
| [`account-creation.md`](account-creation.md) | Automated signup + auth | **done** |
| [`rota-proxy.md`](rota-proxy.md) | Rota proxy rotation engine | **done** |
| `proxy-fabric.md` | Multi-tier proxy fabric | planned |
| `fake-identity-stack.md` | Identity profile generation | planned |
| `playwright-stealth.md` | Playwright stealth | planned |
| `undetected-playwright.md` | Undetected Playwright | planned |

### AI Agent Tier
| Runbook | Tool | Status |
|---|---|---|
| [`browser-use.md`](browser-use.md) | Browser-Use / Skyvern / Stagehand / LaVague | **done** |
| `skyvern.md` | Skyvern form automation | (covered in browser-use.md) |
| `stagehand.md` | Stagehand (TS, Playwright-native) | (covered in browser-use.md) |

### Document Processing Tier
| Runbook | Tool | Status |
|---|---|---|
| [`unstructured.md`](unstructured.md) | Unstructured.io (PDF/HTML/DOCX → structured) | **done** |
| [`ocr-pipeline.md`](ocr-pipeline.md) | PaddleOCR → Surya → GOT-OCR2 → Vision LLM | **done** |
| `paddleocr.md` | PaddleOCR | (covered in ocr-pipeline.md) |
| `tesseract.md` | Tesseract | (covered in ocr-pipeline.md) |
| `surya.md` | Surya (SOTA OSS OCR 2026) | (covered in ocr-pipeline.md) |

### NER + AI Tier
| Runbook | Tool | Status |
|---|---|---|
| [`lmstudio-ollama.md`](lmstudio-ollama.md) | LM Studio + Ollama + vLLM local LLM | **done** |
| [`openclaw.md`](openclaw.md) | OpenClaw AI assistant gateway | **done** |
| `spacy.md` | spaCy NER | planned |
| `gliner.md` | GLiNER NER | planned |
| `transformers-ner.md` | Transformers NER | planned |

### Data Extraction Tier
| Runbook | Tool | Status |
|---|---|---|
| [`trafilatura.md`](trafilatura.md) | Trafilatura (boilerplate stripping) | **done** |
| [`firecrawl.md`](firecrawl.md) | Firecrawl (AI site-to-Markdown) | **done** |
| `jina-reader.md` | Jina AI Reader | planned |

### Dedup + Fusion Tier
| Runbook | Tool | Status |
|---|---|---|
| [`splink.md`](splink.md) | Splink (probabilistic record linkage) | **done** |
| `rapidfuzz.md` | RapidFuzz | planned |
| `dedupe.md` | dedupe.io OSS | planned |

### LLM Infrastructure Tier
| Runbook | Tool | Status |
|---|---|---|
| [`litellm.md`](litellm.md) | LiteLLM (universal proxy, 100+ providers) | **done** |

### Licensed Tools Tier
| Runbook | Tool | Status |
|---|---|---|
| [`screaming-frog.md`](screaming-frog.md) | Screaming Frog SEO crawler ($199/yr) | **done** |
| [`sequentum.md`](sequentum.md) | Sequentum RPA (visual scraping) | **done** |
| [`uipath.md`](uipath.md) | UiPath (enterprise RPA + Document Understanding) | **done** |
| [`ranorex.md`](ranorex.md) | Ranorex (desktop + web automation) | **done** |

### Control Plane Tier
| Runbook | Tool | Status |
|---|---|---|
| [`mcp-servers.md`](mcp-servers.md) | MCP servers (9 servers: Brave, Puppeteer, Postgres, Docker, Slack, FS, GitHub, SerpAPI, Tavily) | **done** |

**Status:** 22 runbooks written, ~15 remaining planned. See [`DOCUMENTATION_PLAN.md`](../../DOCUMENTATION_PLAN.md) for the full documentation schedule.
