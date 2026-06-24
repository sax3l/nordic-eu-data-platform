# Architecture: The Definitive OSS Combination Matrix

**Version:** 2026-06-24
**Author scope:** How to CHAIN open-source repos for maximum success + speed. This is NOT a flat catalog (see `C:/temp/OPEN_SOURCE_TOOLS_CATALOG.md` for the 85+ repo list with per-repo detail). This document answers the only question that matters at runtime: **given THIS target, in THIS state, what tool do I reach for next, why, and what do I fall back to when it fails.**

---

## 0. The Governing Principle: Cheapest-Method-First with Sensing

Every request should climb a **cost ladder** and stop at the first rung that returns a valid payload. The "cost" of a rung is dominated by latency and detectability, not money:

```
Rung 0  Already-have-the-data   (cache / sibling API confirms)      ~0 ms
Rung 1  Raw HTTP + TLS spoof    curl_cffi(impersonate)             20-80 ms
Rung 2  Hidden JSON/GraphQL     direct API hit (harvested route)   30-120 ms
Rung 3  CF-light HTTP solver    cloudscraper / FlareSolverr         1-5 s
Rung 4  Stealth headless        nodriver / camoufox / botasaurus    2-8 s
Rung 5  Licensed escalation     Sequentum / Ranorex / UiPath        5-30 s
Rung 6  Paid services           2captcha / capsolver / ISP proxy    +$ + latency
```

The orchestrator's job is to **sense which rung works per target** (store the winning rung per `(domain, page-type)` in a `method_memory` table) and **start every subsequent request for that target at the known-good rung minus one** (probe one cheaper rung occasionally to detect a defense downgrade). This single behavior is what produces both higher coverage AND higher speed: the slow rungs are never paid for when a cheap rung succeeds, and the cheap rung is never wasted re-probing a hard target.

**Combine-all-sources-simultaneously corollary:** for any entity, fire the *cheap confirmer* (a free API — Bolagsverket, brreg, PRH, Apollo MCP free match, a sibling registry) in parallel with the *expensive scrape*. If the confirmer returns the field you needed before the scrape finishes, **cancel the scrape**. The confirmer doubles as a validator (cross-source agreement = high confidence) and as a speed multiplier (kills in-flight slow work). This is the "cheap API confirms a scrape so the slow scrape can be skipped" pattern, made concrete.

---

## 1. THE MASTER MATRIX

Situation → ordered tool chain → expected speed → fallback. Concurrency column = recommended parallel workers per node for that rung (free-proxy fabric assumed; halve if proxy-starved).

| # | Situation (signal you detect) | Ordered tool chain (stop at first success) | Expected speed / page | Concurrency | Fallback when whole chain fails |
|---|---|---|---|---|---|
| 1 | **Static HTML**, no JS gate, 200 OK with content in body | `curl_cffi(impersonate=chrome)` → `selectolax` (HTMLParser) → CSS select | 20–80 ms | 50–200 | go to row 5 (treat as soft-blocked) |
| 2 | **lxml-needed** (XPath, namespaces, malformed XML, sitemaps) | `curl_cffi` → `lxml.html` / `lxml.etree` + `cssselect` | 60–120 ms | 50–150 | selectolax if lxml chokes on encoding |
| 3 | **Hidden JSON / `__NEXT_DATA__` / `__NUXT__` / inline state** | `curl_cffi` → regex/`selectolax` pull `<script id=__NEXT_DATA__>` → `orjson.loads` | 25–90 ms | 100–200 | row 4 (find the real API) |
| 4 | **GraphQL / REST XHR endpoint** behind a SPA | harvest route once (mitmproxy/devtools) → replay with `curl_cffi` + captured headers/`persistedQuery` hash | 30–120 ms | 80–150 | row 8 (render it) |
| 5 | **Soft block** (403/429/503, JS-challenge HTML, `cf-mitigated` header) | `cloudscraper` → `FlareSolverr` (Docker) → `curl_cffi(impersonate)` + fresh proxy/UA | 1–5 s | 10–40 | row 6 |
| 6 | **Cloudflare Turnstile / managed challenge / IUAM v2** | `FlareSolverr` → `CycleTLS`/`curl_cffi` with harvested `cf_clearance` (same IP+UA!) → `camoufox` → `nodriver` → **`botasaurus`** | 2–8 s | 4–12 | **escalate to Sequentum** (row 19) |
| 7 | **DataDome / PerimeterX / Akamai Bot Manager** | `camoufox` (Firefox-patched, best TLS+JS coherence) → `nodriver` + `rebrowser-patches` → `botasaurus` → residential ISP proxy | 3–10 s | 3–8 | Sequentum Cloud (row 19) |
| 8 | **JS-rendered SPA** (empty body, React/Vue/Angular, content via fetch) | `nodriver` (async, fewest leaks) → `undetected-playwright` → `camoufox` → `puppeteer-extra+stealth` (Node) | 2–6 s | 6–16 | block resources, retry; then row 19 |
| 9 | **Infinite scroll / lazy content** | headless from row 8 + scroll loop → **intercept the XHR** and switch to row 4 mid-session | 3–8 s | 6–12 | paginate via discovered API params |
| 10 | **Login / cookie-walled** (LinkedIn, registries) | headless login once → **export storage_state/cookies** → replay all subsequent reads with `curl_cffi` carrying cookies | 2 s login, 50 ms/read | 1 login → 50 reads | rotate identity, re-login |
| 11 | **PDF / annual report / filing** | `PyMuPDF`(fitz) fast text → if scanned: `pdfplumber` (tables) → OCR chain (row 13) | 50–300 ms text | 20–50 | OCR fallback |
| 12 | **Image/scan needing text** | `PaddleOCR` (PP-OCRv4) → `docTR`/`RapidOCR` (ONNX, fast) → `Tesseract 5` → **Claude Vision** | 100–800 ms | 4–8 (GPU) | Claude Vision (last) |
| 13 | **Low-quality scan** (skew, noise, low DPI) | `opencv` preprocess (deskew, denoise, binarize, upscale) → then row 12 | +30–80 ms | 4–8 | noteshrink cleanup → retry |
| 14 | **Entity extraction from messy text** | `spaCy nlp.pipe` (batched) → `GLiNER`/`transformers` NER → **Claude API** for hard cases | 20 ms/doc spaCy | 8–32 (pipe batch) | Claude API |
| 15 | **Structured fields from a page** (name/title/email/phone) | CSS/XPath rules first → `selectolax` extract → NER (row 14) only on residual free-text | <5 ms rules | 100+ | NER fallback |
| 16 | **Email discovery + verify** | pattern infer (`first.last@`) → MX lookup (`dnspython`) → SMTP RCPT probe (throttled) → cross-source confirm | 5 ms infer, 150 ms MX | 20–50 | accept syntactic + MX only |
| 17 | **Dedup / entity resolution across sources** | `RapidFuzz` blocking → `datasketch` MinHash/LSH candidate gen → `Splink`/`dedupe` probabilistic linkage | 10k pairs/s | CPU-bound | RapidFuzz token_set only |
| 18 | **CAPTCHA actually presented** (after detection-first failed) | **detect & avoid first** (back off, rotate, re-route) → OSS Turnstile solvers (Boterdrop, cf-clearance-scraper) → **2captcha/capsolver** paid | varies | low | paid solver (last resort) |
| 19 | **Everything OSS exhausted** (hard target, JS+TLS+behavioral) | **Sequentum Desktop** (agent + proxy + CAPTCHA mgmt) → **Sequentum Cloud** (scale) → **UiPath** (app/portal flows) → **Ranorex** (desktop/Win32 apps, Citrix) | 5–30 s | licensed pool | manual queue |
| 20 | **Bulk site crawl / sitemap / SEO surface** | **Screaming Frog SEO Spider** (licensed, list+spider mode, custom extraction) → feed URL frontier to rows 1–8 | 100–500 URL/s discovery | n/a | sitemap parser + curl_cffi |

---

## 2. THE ANTI-DETECTION IDENTITY STACK (binds rows 1, 5–10)

Detection works by **incoherence**: a Chrome User-Agent with a Firefox TLS fingerprint, or a header set whose `Accept-Language` doesn't match the UA's locale. The fix is to generate **one coherent identity** and apply it across *every* layer of the request.

```python
# identity.py — coherent profile factory (browserforge + curl_cffi)
from browserforge.fingerprints import FingerprintGenerator
from browserforge.headers import HeaderGenerator
import random

_fp_gen = FingerprintGenerator()
_hdr_gen = HeaderGenerator(browser="chrome", os=("windows", "macos"))

# curl_cffi impersonation target MUST match the fingerprint's browser+version
_IMPERSONATE_MAP = {
    "chrome": ["chrome120", "chrome123", "chrome124", "chrome131"],
    "firefox": ["firefox133"],
    "safari": ["safari17_0", "safari18_0"],
}

def make_identity():
    fp = _fp_gen.generate(browser="chrome", os="windows")
    browser_family = "chrome"
    headers = _hdr_gen.generate(browser=browser_family)   # Accept-Language etc. coherent with UA
    impersonate = random.choice(_IMPERSONATE_MAP[browser_family])
    return {
        "headers": headers,                  # header-generator: ordered, realistic
        "user_agent": headers["User-Agent"],
        "impersonate": impersonate,          # TLS/JA3/HTTP2 matches the UA
        "viewport": (fp.screen.width, fp.screen.height),
        "timezone": fp.navigator.timezone if hasattr(fp.navigator, "timezone") else "Europe/Stockholm",
        "locale": fp.navigator.language if hasattr(fp.navigator, "language") else "sv-SE",
    }
```

**Rule:** the `impersonate` value (TLS layer), the `User-Agent` (HTTP header layer), and — when you escalate to a browser — the launch fingerprint (camoufox/nodriver) must all describe the *same* browser+version. browserforge is the source of truth; `fake-useragent` is only a low-fidelity fallback when browserforge is unavailable. For browsers, **camoufox accepts a browserforge fingerprint object directly**, so the same identity flows from HTTP rung straight into the headless rung — the target sees one consistent entity even as you escalate.

---

## 3. THE FREE PROXY FABRIC (binds every networked row)

Free proxies are 40–60% dead at any moment, so the fabric must be **self-healing**: ingest many sources, health-check continuously, score by `(success_rate, latency, last_ok)`, and serve only live ones. Paid ISP/residential proxies are summoned **only** when the free tier fails a target N times (cost-aware escalation).

**Sources (union, deduped):** `TheSpeedX/PROXY-List`, `monosans/proxy-list`, `proxifly/free-proxy-list`, `clarketm/proxy-list` → plus `ProxyBroker2` (async discovery+validation) → plus **Tor** via `stem` (3–10 circuits, rotate `NEWNYM` every M requests) for a free residential-ish identity on light targets.

```python
# proxy_fabric.py — health-checked pool with cost-aware paid escalation
import asyncio, time, aiohttp
from collections import defaultdict

class ProxyFabric:
    def __init__(self, paid_pool=None):
        self.alive = {}                      # proxy -> {score, latency, last_ok}
        self.fail = defaultdict(int)
        self.paid_pool = paid_pool or []     # ISP/residential, used last
        self.domain_fail = defaultdict(int)  # per-domain free-tier failures

    async def _check(self, session, proxy):
        t = time.time()
        try:
            async with session.get("https://httpbin.org/ip", proxy=f"http://{proxy}",
                                    timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    self.alive[proxy] = {"latency": time.time()-t, "last_ok": time.time(),
                                         "score": self.alive.get(proxy, {}).get("score", 1)+1}
        except Exception:
            self.fail[proxy] += 1
            if self.fail[proxy] >= 3:
                self.alive.pop(proxy, None)

    async def health_loop(self, candidates, interval=120):
        async with aiohttp.ClientSession() as s:
            while True:
                await asyncio.gather(*(self._check(s, p) for p in candidates))
                await asyncio.sleep(interval)

    def get(self, domain):
        # cost-aware: free first; only buy when free repeatedly fails this domain
        if self.domain_fail[domain] >= 5 and self.paid_pool:
            return ("paid", self.paid_pool[self.domain_fail[domain] % len(self.paid_pool)])
        if self.alive:
            best = max(self.alive, key=lambda p: (self.alive[p]["score"], -self.alive[p]["latency"]))
            return ("free", best)
        return ("direct", None)

    def report(self, domain, proxy_kind, ok):
        if proxy_kind == "free" and not ok:
            self.domain_fail[domain] += 1
        if ok:
            self.domain_fail[domain] = max(0, self.domain_fail[domain]-1)
```

**Sticky sessions** (from `architecture_patterns_reference.md`): bind one proxy per `(domain)` for up to 1 h to look like a returning user; rotate on block. **Bulkhead:** isolate a per-domain rate limiter + circuit breaker so one hostile domain can't starve the pool.

---

## 4. DECISION ORDER FOR ANTI-BOT WALLS (expanded row 5–7)

**Detection signals → branch (sense before you spend):**

| Signal observed | Wall identified | Enter chain at |
|---|---|---|
| `Server: cloudflare` + `cf-mitigated: challenge` / `__cf_chl` JS | Cloudflare JS challenge | cloudscraper → FlareSolverr |
| Turnstile widget `cf-turnstile` / `0x4AAAA…` sitekey | Cloudflare Turnstile | FlareSolverr (token) → camoufox → botasaurus |
| `x-datadome` cookie / `datadome` JS / `geo.captcha-delivery.com` | DataDome | camoufox → nodriver+rebrowser → ISP proxy |
| `_px` cookies / `/px/` resources / `pxhd` | PerimeterX/HUMAN | camoufox → nodriver → Sequentum |
| `akamai` `bm_sz`/`_abck` cookies, sensor POST | Akamai Bot Manager | curl_cffi w/ correct JA3 → camoufox → Sequentum |
| `Incapsula`/`visid_incap` | Imperva | cloudscraper → FlareSolverr → camoufox |

**Why this order:** each step is strictly more expensive and more detectable-if-misconfigured than the last. cloudscraper/FlareSolverr solve *JS-compute* challenges cheaply; `cf_clearance` reuse via curl_cffi gives you a fast HTTP path **once a token exists** (must reuse the exact IP+UA that earned it — see `cloudflare_waf_bypass_repos_2026.md`). camoufox beats nodriver on the hardest walls because its Firefox patches produce the most coherent TLS+JS+canvas story; nodriver is faster to spin up and leaks less than vanilla Playwright. botasaurus is the "kitchen-sink" last OSS rung (cache + IP rotation + CF bypass in one). **Only then** do you spend a Sequentum license.

---

## 5. CAPTCHA: DETECTION-FIRST, PAY LAST

The cheapest CAPTCHA is the one you never trigger. Order of operations:

1. **Avoid:** if a CAPTCHA appears, treat it as a *block signal*, not a puzzle — back off (adaptive backoff table), rotate identity+proxy, slow request rate, retry from a cheaper rung. ~70% of CAPTCHAs vanish under a clean identity + human-paced timing.
2. **Token-harvest (OSS):** for Turnstile, `cf-clearance-scraper` / `Boterdrop-Solver` (Camoufox+FastAPI) mint a token you replay over HTTP.
3. **Paid last resort:** `2captcha`/`capsolver` ONLY when (1) and (2) fail and the data ROI justifies ~$0.001–0.003/solve. Gate this behind the same cost-aware counter as paid proxies.

---

## 6. PARALLELISM MODEL (how everything runs at once)

Throughput = (workers) × (1 / latency-of-winning-rung). Maximize via **four orthogonal axes combined**:

- **Across targets** — N async workers, each pinned to a domain bulkhead (separate rate limiter + circuit breaker + sticky proxy).
- **Across rungs (speculative race)** — for high-value entities, fire the *cheap confirmer API* and the *scrape* concurrently; first valid result wins, the loser is cancelled (`asyncio.wait(..., FIRST_COMPLETED)`).
- **Across methods (hedged request)** — if rung-1 hasn't returned in `p95+ε`, start rung-3 without waiting for rung-1 to fail. Cancel the slower.
- **Across machines** — Redis/RabbitMQ work queue + DLQ (see `docker_scraping_infrastructure_guide.md`); CPU-bound stages (OCR, NER, dedup) on a separate worker pool from IO-bound fetch workers so a GPU OCR batch never blocks fetchers.

**Concurrency is sensed, not fixed:** start each domain at a conservative RPS; on a streak of 200s, ramp up; on the first 429/403, halve and arm the circuit breaker. This is the real-time adaptation the platform requires.

---

## 7. GLUE CODE — THE 3 MOST IMPORTANT CHAINS

### Chain A — Static/JSON fast path with selectolax (rows 1–4)

**Why selectolax wins on speed:** selectolax wraps **Modest/Lexbor**, C engines that parse HTML in a single pass into a compact node tree with no Python object per node until you ask for one. BeautifulSoup builds a full Python object graph (every tag, string, and navigable-string is a Python object) and, with the `html.parser` backend, runs interpreted Python per token. In practice selectolax parses + selects a typical profile page in **~2–5 ms vs ~40–150 ms for BS4** (10–30× faster) and uses a fraction of the memory, which is what lets row 1 run at 100–200 concurrent workers on one box. lxml is close to selectolax on raw parse but selectolax wins on CSS-heavy extraction and malformed HTML resilience; reach for lxml only when you need XPath.

```python
# chain_a.py — curl_cffi + selectolax with __NEXT_DATA__ shortcut
from curl_cffi import requests as creq
from selectolax.parser import HTMLParser
import orjson
from identity import make_identity

def fetch_static(url, proxy=None):
    ident = make_identity()
    r = creq.get(url, impersonate=ident["impersonate"], headers=ident["headers"],
                 proxies={"https": proxy} if proxy else None, timeout=20)
    return r

def extract(url, css_map, proxy=None):
    r = fetch_static(url, proxy)
    if r.status_code in (403, 429, 503) or "cf-mitigated" in r.headers:
        return {"_block": True, "_status": r.status_code}     # -> escalate to Chain B
    tree = HTMLParser(r.text)

    # SHORTCUT: hydrated JSON beats DOM scraping every time
    nd = tree.css_first('script#__NEXT_DATA__')
    if nd is not None:
        try:
            return {"_source": "next_data", "data": orjson.loads(nd.text())}
        except Exception:
            pass

    out = {"_source": "dom"}
    for field, selector in css_map.items():       # selectolax CSS, ~µs per select
        node = tree.css_first(selector)
        out[field] = node.text(strip=True) if node else None
    return out

# usage
# extract("https://site/company/123",
#         {"name": "h1.company-name", "city": "span.locality", "vat": "[data-vat]"})
```

### Chain B — Escalation ladder with method-memory + speculative confirmer (rows 5–8 + parallel API)

This is the heart of the platform: it senses the wall, climbs only as far as needed, remembers the winning rung per domain, and races a free API confirmer so the slow scrape can be **cancelled** the moment a cheap source already has the field.

```python
# chain_b.py — adaptive escalation + cancel-on-confirm
import asyncio, time
from chain_a import extract
# OSS rungs (import lazily so a missing binary doesn't break the whole app)

method_memory = {}   # domain -> best_rung_index (persist to disk/db in prod)
RUNGS = ["static", "cloudscraper", "flaresolverr", "camoufox", "nodriver", "sequentum"]

async def free_api_confirm(entity):
    """Cheap parallel confirmer: Bolagsverket/brreg/PRH/Apollo-free.
    Returns the needed field fast, or None. Doubles as a cross-source validator."""
    # ... hit registry/MCP; return {"name":..., "vat":...} or None
    return None

async def rung_static(url, proxy):    return extract(url, CSS, proxy)

async def rung_cloudscraper(url, proxy):
    import cloudscraper
    s = cloudscraper.create_scraper()
    html = s.get(url, proxies={"https": proxy} if proxy else None).text
    return _parse(html)

async def rung_flaresolverr(url, proxy):
    import aiohttp
    async with aiohttp.ClientSession() as s:
        async with s.post("http://localhost:8191/v1", json={
            "cmd": "request.get", "url": url, "maxTimeout": 60000,
            **({"proxy": {"url": f"http://{proxy}"}} if proxy else {})}) as r:
            j = await r.json()
            return _parse(j["solution"]["response"])

async def rung_camoufox(url, proxy):
    from camoufox.async_api import AsyncCamoufox
    async with AsyncCamoufox(headless=True, proxy={"server": f"http://{proxy}"} if proxy else None) as b:
        page = await b.new_page(); await page.goto(url, wait_until="networkidle")
        return _parse(await page.content())

async def rung_nodriver(url, proxy):
    import nodriver as uc
    browser = await uc.start(browser_args=[f"--proxy-server={proxy}"] if proxy else None)
    page = await browser.get(url); html = await page.get_content()
    browser.stop(); return _parse(html)

RUNG_FUNCS = {"static": rung_static, "cloudscraper": rung_cloudscraper,
              "flaresolverr": rung_flaresolverr, "camoufox": rung_camoufox,
              "nodriver": rung_nodriver}  # "sequentum" => external licensed job

def _parse(html):  # placeholder: real impl uses selectolax like Chain A
    return {"_ok": bool(html), "html_len": len(html or "")}

def _looks_blocked(res):
    return (not res) or res.get("_block") or res.get("html_len", 1) < 500

async def fetch_adaptive(url, domain, entity, proxy_fabric):
    # 1) speculative confirmer races the scrape
    confirm_task = asyncio.create_task(free_api_confirm(entity))

    # 2) start at remembered rung minus one (occasionally re-probe cheaper)
    start = max(0, method_memory.get(domain, 0) - 1)
    for i in range(start, len(RUNGS)):
        rung = RUNGS[i]
        if rung == "sequentum":
            res = await submit_sequentum_job(url)        # licensed escalation
        else:
            kind, proxy = proxy_fabric.get(domain)
            scrape = asyncio.create_task(RUNG_FUNCS[rung](url, proxy))
            done, _ = await asyncio.wait({scrape, confirm_task},
                                         return_when=asyncio.FIRST_COMPLETED)
            if confirm_task in done and confirm_task.result():
                scrape.cancel()                          # cheap API won -> skip slow scrape
                method_memory[domain] = min(method_memory.get(domain, i), i)
                return {"_source": "free_api", **confirm_task.result()}
            res = await scrape
            proxy_fabric.report(domain, kind, ok=not _looks_blocked(res))

        if not _looks_blocked(res):
            method_memory[domain] = i                    # remember winning rung
            return {"_source": rung, **res}
        # else: escalate to next rung

    return {"_source": "exhausted", "_manual_queue": True}

async def submit_sequentum_job(url):  # Sequentum Desktop/Cloud agent endpoint
    return {"_ok": True, "html_len": 9999}
```

### Chain C — OCR → NER fusion for filings/scans (rows 11–14)

PDF text first (free, instant); OCR only the pages that have no text layer; preprocess before OCR; then run a single batched NER pass. The cascade stops at the first engine whose mean confidence clears a threshold, so PaddleOCR handles the bulk and Claude Vision is touched only on the truly hard scans.

```python
# chain_c.py — fitz -> opencv -> Paddle/docTR/Tesseract -> spaCy.pipe -> Claude
import fitz, cv2, numpy as np
from paddleocr import PaddleOCR
import spacy

_paddle = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
_nlp = spacy.load("en_core_web_md")   # or xx_ent_wiki_sm for Nordic multilingual

def _deskew_denoise(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.fastNlMeansDenoising(g, h=10)
    coords = np.column_stack(np.where(g < 128))
    if len(coords):
        ang = cv2.minAreaRect(coords)[-1]; ang = -(90+ang) if ang < -45 else -ang
        h, w = g.shape; M = cv2.getRotationMatrix2D((w//2, h//2), ang, 1.0)
        g = cv2.warpAffine(g, M, (w, h), flags=cv2.INTER_CUBIC,
                           borderMode=cv2.BORDER_REPLICATE)
    return cv2.threshold(g, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

def page_text(page):
    t = page.get_text("text")
    if len(t.strip()) > 40:                      # real text layer -> no OCR
        return t, 1.0
    pix = page.get_pixmap(dpi=300)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    img = _deskew_denoise(img[:, :, :3])
    res = _paddle.ocr(img, cls=True)
    lines = [w[1][0] for blk in (res or []) for w in (blk or [])]
    confs = [w[1][1] for blk in (res or []) for w in (blk or [])]
    mean_conf = sum(confs)/len(confs) if confs else 0.0
    # if mean_conf < 0.75 -> retry docTR/RapidOCR, then Tesseract, then Claude Vision
    return "\n".join(lines), mean_conf

def extract_entities(doc_path):
    doc = fitz.open(doc_path)
    texts = [page_text(p)[0] for p in doc]
    out = []
    for sp in _nlp.pipe(texts, batch_size=32):   # batched = the spaCy speed unlock
        out.append([(e.text, e.label_) for e in sp.ents
                    if e.label_ in ("ORG", "PERSON", "GPE", "MONEY", "DATE")])
    # hard/ambiguous pages (low NER yield + low OCR conf) -> Claude API for structured pull
    return out
```

---

## 8. DEDUP & ENTITY RESOLUTION (row 17, binds all sources)

Combining all sources raises coverage only if you can **resolve** that two records are the same entity. Three-stage pipeline:

1. **Block** with `RapidFuzz` (`token_set_ratio` on normalized name) to avoid O(n²) — only compare within blocks (e.g., same `lan`/`kommun` or same orgnr prefix).
2. **Candidate-generate** with `datasketch` MinHash + LSH over shingled name+address — finds near-duplicates across millions of rows in near-linear time.
3. **Decide** with `Splink` (or `dedupe`) probabilistic record linkage: trained match weights over (name, orgnr, address, domain, phone), producing a calibrated match probability and clusters. orgnr/registry-number is the gold blocking+match key for Nordic data; fall back to fuzzy name+domain when it's missing.

Cross-source agreement (registry + scrape + Apollo confirmer all say the same VAT/orgnr) is your **confidence score** and your **validator** — disagreements route to a review queue rather than being fabricated.

---

## 9. LICENSED-TOOL ESCALATION (rows 19–20, used maximally)

The OSS chain handles the long tail cheaply; the licensed tools are reserved for what OSS can't reliably do — and they are wired in as **rungs**, not silos:

- **Screaming Frog SEO Spider** — the URL-discovery front-end for *every* large site: list/spider mode + custom extraction (XPath/CSS/regex) emits a clean URL frontier and even pulls structured fields in one pass; feed its export into the row-1–8 fetchers. Also the canonical tool for website/coverage sweeps across all target companies.
- **Sequentum (Desktop + Cloud)** — the top OSS-exhausted rung (row 6/7 fallback): built-in proxy management, CAPTCHA handling, JS rendering, and change-resilient agents. Desktop for authoring/hard one-offs; Cloud for parallel scale. This is where Cloudflare/DataDome targets that beat camoufox+nodriver go.
- **UiPath** — portal/app flows that are really *processes* (multi-step logins, document downloads from government/bank portals, RPA over web apps where a scraper would be brittle).
- **Ranorex** — desktop/Win32/Citrix and thick-client apps (legacy registry clients, internal tools) that have no web surface to scrape at all.

A licensed-tool job is dispatched exactly like an OSS rung: same work queue, same method-memory, same per-domain circuit breaker — so the orchestrator can decide, per target, that "this domain always needs Sequentum" and route straight there next time, skipping the wasted OSS climb.

---

## 10. PUTTING IT TOGETHER — THE SENSING LOOP

```
for each task (entity, url, domain):
  1. consult method_memory[domain] -> start rung = best-1
  2. fire free_api_confirm() in parallel (cheap source + validator)
  3. climb rungs 1->6 (OSS) -> 7 (Sequentum) -> UiPath/Ranorex if app-flow
     - sense blocks (status, headers, body length, CAPTCHA, wall signature)
     - cancel scrape if confirmer returns the field first
     - report proxy outcome -> fabric adjusts; adjust RPS -> ramp/halve
  4. on success: record winning rung; parse with selectolax/JSON
  5. extract: rules -> NER pipe -> Claude for residue
  6. resolve: RapidFuzz -> MinHash/LSH -> Splink; cross-source confidence
  7. on exhaustion: dead-letter queue -> manual/licensed review
```

Every loop iteration makes the next one faster (method-memory), cheaper (cost-aware paid escalation), and more accurate (cross-source confirmation). That is the definition of a system that runs at maximum speed, self-corrects, senses-and-adapts per target, parallelizes every way, and fuses all sources to raise both coverage and throughput at once.
