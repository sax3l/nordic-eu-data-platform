# Adaptive Self-Healing Orchestration Engine

**Component:** `arch_adaptive-engine` — the brain of the platform
**Role:** Senses which extraction method works per target, adapts method + concurrency in real time, detects blocks/errors, and self-heals — so the system always runs at the maximum speed each target currently tolerates while combining every free repo and every licensed tool.
**Builds on:** `OPEN_SOURCE_TOOLS_CATALOG.md`, `cloudflare_waf_bypass_repos_2026.md`, `headless_browser_automation_catalog.md`, `architecture_patterns_reference.md`, `docker_scraping_infrastructure_guide.md`, `WEB_EXTRACTION_NER_PIPELINE.md`, `COMPETITIVE_ANALYSIS_APOLLO_COGNISM_LINKEDIN_2026.md`.

---

## 0. Design Thesis

A naïve scraper picks one method per site and one fixed concurrency, then either gets blocked (too aggressive) or wastes hours (too timid). The platform's goal is the opposite: **treat every target host as a non-stationary bandit problem**. We do not know in advance whether `allabolag.se` is best hit today with `curl_cffi` at 40 rps or needs Botasaurus at 3 rps — and that answer *changes hour to hour* as the target's WAF posture changes. The engine therefore:

1. **Ranks methods cheapest-first** (a `curl_cffi` GET costs ~80 ms and zero browser RAM; a Botasaurus browser solve costs ~6 s and 300 MB; a Screaming Frog or UiPath job costs a license seat and a desktop). It always tries the cheapest method that is *currently working* for that host.
2. **Learns online** via a per-host multi-armed bandit so the ranking self-corrects without human tuning.
3. **Detects failure precisely** (403 vs 429 vs CF challenge vs DataDome vs empty render vs honeypot) and maps each class to a *specific* remediation, not a blanket "retry."
4. **Controls speed with AIMD congestion control** (TCP-style) per host: ramp concurrency up additively while things are green, multiplicatively back off the instant blocks appear.
5. **Combines sources to both raise coverage AND raise speed** — e.g. an Apollo/Bolagsverket API confirm lets us *skip* a slow scrape entirely (cross-source short-circuit).

The whole engine is ~1500 lines of Python (`asyncio`) plus Redis for shared state, so a fleet of workers shares one brain.

---

## 1. The Method Tier Ladder

Every method the platform owns is registered with a **cost weight** (lower = cheaper = preferred) and a capability profile. The router never reaches for tier 4 if tier 1 is green.

| Tier | Method | Repo / Tool (stars) | Cost wt | Solves | Throughput |
|------|--------|---------------------|---------|--------|-----------|
| 0 | **Cross-source API confirm** | Apollo MCP, Bolagsverket iXBRL, brreg/PRH open APIs | 1 | — (skips scrape) | 1000s/s |
| 1 | **curl_cffi (impersonate)** | [lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) 5.9k | 2 | TLS/JA3/JA4, HTTP2 | 50–200 rps |
| 1 | **wreq-python** | [0x676e67/wreq-python](https://github.com/0x676e67/wreq-python) 1.4k | 2 | TLS + HTTP/3/QUIC | 50–200 rps |
| 2 | **cloudscraper** | [VeNoMouS/cloudscraper](https://github.com/VeNoMouS/cloudscraper) 6.6k | 4 | CF IUAM/JS-lite | 10–40 rps |
| 2 | **Scrapling** | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) 65.9k | 4 | rotation+fingerprints | 10–40 rps |
| 3 | **Botasaurus** | [omkarcloud/botasaurus](https://github.com/omkarcloud/botasaurus) 4.8k | 8 | CF JS, full browser | 2–8 rps |
| 3 | **Playwright + stealth** | [microsoft/playwright](https://github.com/microsoft/playwright) 65k + [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches) 1.4k | 8 | JS render, SPA | 2–8 rps |
| 3 | **Camoufox / nodriver** | [daijro/camoufox](https://github.com/daijro/camoufox) 9.5k, [ultrafunkamsterdam/nodriver](https://github.com/ultrafunkamsterdam/nodriver) 4.4k | 9 | hardened FP, Turnstile | 1–5 rps |
| 3.5 | **FlareSolverr pool** | [FlareSolverr/FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) 14.4k | 10 | CF challenge as a service | 0.5–2 rps |
| 4 | **Screaming Frog SEO Spider** | licensed (CLI `--headless`) | 12 | bulk site crawl, sitemaps | site-batch |
| 4 | **Sequentum (Desktop+Cloud)** | licensed (agent export / Cloud API) | 12 | complex auth flows, exports | agent-batch |
| 5 | **UiPath** | licensed (Orchestrator queue) | 16 | portal logins, captcha-gated desktop apps | RPA-batch |
| 5 | **Ranorex** | licensed | 16 | desktop/thick-client apps | RPA-batch |
| 6 | **2captcha / human escalate** | [2captcha-python](https://github.com/2captcha/2captcha-python) 0.8k | 20 | hard CAPTCHA | manual |

The licensed tools sit at the bottom *on cost* but they are **first-class arms** — when the bandit learns that a host only ever succeeds via Sequentum (e.g. an authenticated portal that defeats every headless browser), the router promotes Sequentum to that host's preferred arm and *stops wasting cheap attempts*. That is "use every licensed tool maximally": they are not a last resort by policy, they are last *by cost* but promoted the instant they are the only thing that works.

---

## 2. MethodRouter — Per-Domain Bandit

### 2.1 Algorithm choice

We use **Thompson Sampling with a Beta posterior per (host, method)** for the success/block dimension, blended with a latency penalty. Thompson Sampling beats ε-greedy here because:
- It explores *proportionally to uncertainty* (a method tried twice gets explored more than one tried 500×), which is exactly right for a fleet discovering new hosts continuously.
- It needs no decay schedule tuning.
- It naturally handles non-stationarity when combined with a **sliding window / discounted counts** (we decay successes & failures by γ=0.98 per hour so a method that *used* to work but now gets blocked falls in rank automatically — this is the "demote when conditions change" requirement).

Libraries:
- **[`mabwiser`](https://github.com/fidelity/mabwiser)** (Fidelity, ~1k★) — production MAB with `LearningPolicy.ThompsonSampling()`, `EpsilonGreedy()`, `UCB1()` interchangeable, plus contextual bandits (LinUCB) if we later add features (host TLD, WAF vendor, time-of-day) as context.
- **[`contextualbandits`](https://github.com/david-cortes/contextualbandits)** (~1k★) — if we go contextual.
- **[`BayesianOptimization`](https://github.com/bayesian-optimization/BayesianOptimization)** — only for offline concurrency-ceiling search, not the live loop.

We keep our own thin Beta sampler too (below) so the hot path has zero extra deps and lives in Redis.

### 2.2 Reference implementation

```python
# method_router.py
import math, random, time, json
from dataclasses import dataclass, field
import redis.asyncio as redis

@dataclass
class MethodStat:
    alpha: float = 1.0          # Beta prior successes
    beta: float = 1.0           # Beta prior failures
    ewma_latency_ms: float = 500.0
    last_update: float = field(default_factory=time.time)
    cost_weight: float = 2.0    # tier cost (lower preferred)

    def decay(self, gamma_per_hr=0.98):
        """Non-stationarity: forget old evidence so demotion happens."""
        hrs = (time.time() - self.last_update) / 3600.0
        if hrs > 0:
            d = gamma_per_hr ** hrs
            # decay toward the prior (1,1), never below it
            self.alpha = 1.0 + (self.alpha - 1.0) * d
            self.beta  = 1.0 + (self.beta  - 1.0) * d
            self.last_update = time.time()

    def sample_score(self):
        """Thompson sample of success-prob, penalized by cost & latency."""
        self.decay()
        p_success = random.betavariate(self.alpha, self.beta)
        # reward = expected success per unit cost-time
        cost_time = self.cost_weight * (self.ewma_latency_ms / 100.0)
        return p_success / max(cost_time, 0.1)

    def record(self, ok: bool, latency_ms: float):
        self.decay()
        if ok: self.alpha += 1.0
        else:  self.beta  += 1.0
        self.ewma_latency_ms = 0.7 * self.ewma_latency_ms + 0.3 * latency_ms
        self.last_update = time.time()


# Tier cost table (lower = cheaper). Licensed tools are arms, not exceptions.
TIER_COST = {
    "api_confirm": 1, "curl_cffi": 2, "wreq": 2,
    "cloudscraper": 4, "scrapling": 4,
    "botasaurus": 8, "playwright_stealth": 8, "camoufox": 9, "nodriver": 9,
    "flaresolverr": 10, "screaming_frog": 12, "sequentum": 12,
    "uipath": 16, "ranorex": 16, "captcha_solver": 20,
}

class MethodRouter:
    """Per-host bandit over extraction methods, shared across workers via Redis."""
    def __init__(self, r: redis.Redis, methods: list[str], epsilon_floor=0.03):
        self.r = r
        self.methods = methods
        self.epsilon_floor = epsilon_floor   # always reserve some exploration
        self._cache: dict[str, dict[str, MethodStat]] = {}

    async def _load(self, host: str) -> dict[str, MethodStat]:
        raw = await self.r.hgetall(f"router:{host}")
        stats = {}
        for m in self.methods:
            if m.encode() in raw or m in raw:
                d = json.loads(raw[m] if isinstance(raw[m], str) else raw[m.encode()])
                stats[m] = MethodStat(**d)
            else:
                stats[m] = MethodStat(cost_weight=TIER_COST.get(m, 5))
        self._cache[host] = stats
        return stats

    async def choose(self, host: str, allowed: list[str] | None = None) -> str:
        stats = self._cache.get(host) or await self._load(host)
        pool = [m for m in self.methods if (allowed is None or m in allowed)]
        # epsilon floor: occasionally try the cheapest unproven arm to keep options alive
        if random.random() < self.epsilon_floor:
            return min(pool, key=lambda m: stats[m].cost_weight)
        # Thompson: pick arm with best sampled reward
        return max(pool, key=lambda m: stats[m].sample_score())

    async def update(self, host: str, method: str, ok: bool, latency_ms: float):
        stats = self._cache.get(host) or await self._load(host)
        stats[method].record(ok, latency_ms)
        await self.r.hset(f"router:{host}", method,
                          json.dumps(stats[method].__dict__))
        # promotion/demotion is implicit: next choose() samples the updated posterior
```

**Promotion/demotion is emergent**, not hand-coded: once `sequentum` accumulates wins on a host where `curl_cffi`/`playwright` only accumulate blocks, its sampled reward overtakes them and `choose()` returns it. The hourly decay guarantees a method that *stops* working (host deployed DataDome overnight) loses its lead within a few hours even if it had a long winning streak — automatic re-exploration. The `epsilon_floor` guarantees we never permanently abandon a cheap arm, so when the host relaxes its WAF we rediscover that `curl_cffi` works again and demote the expensive browser.

---

## 3. FailureClassifier — Detect & Classify Blocks

Detection must be *specific* because each failure class has a different optimal remedy. A 429 means "slow down, same identity"; a 403 CF challenge means "escalate to browser/FlareSolverr"; an empty render means "the HTTP method got a JS shell — escalate tier"; a honeypot hit means "this proxy/identity is burned — rotate and blacklist."

### 3.1 Signals we inspect

- **HTTP status:** 403, 429, 503, 401, 5xx.
- **CF / WAF fingerprints in body+headers:** `cf-mitigated: challenge`, `cf-ray`, `__cf_chl`, `cf_clearance`, `Just a moment...`, Turnstile `cdn-cgi/challenge-platform`. Reference detector: [Cloudflare-Cookie-Analysis](https://github.com/seadhy/Cloudflare-Cookie-Analysis) for cf_bm/cf_clearance mechanics; FlareSolverr's own challenge-detection regexes.
- **DataDome:** `x-datadome` / `datadome` cookie, `dd_cookie`, `geo.captcha-delivery.com` redirect, JS `var dd=`.
- **PerimeterX/HUMAN:** `_px`, `px-captcha`, `/_px/`.
- **Akamai:** `_abck`, `ak_bmsc`, `bm_sz` (invalid `_abck` sensor → block). [gospider007/fp](https://github.com/gospider007/fp) characterizes the Akamai fingerprint we must match.
- **Imperva/Incapsula:** `incap_ses`, `___utmvc`, `Incapsula incident`.
- **AWS WAF:** `x-amzn-waf`, `awswaf`, captcha JS.
- **Empty / shell render:** HTTP 200 but body < N bytes, or content-length high but no target selectors (e.g. company name / `<table>` missing) → JS-required. Use a **content-presence assertion** per host (a CSS/xpath that *must* exist).
- **Honeypot:** hidden links with `display:none`/`visibility:hidden`/`width:0` that, if followed, get the IP banned; off-screen form fields. Reference vectors: [niespodd/browser-fingerprinting](https://github.com/niespodd/browser-fingerprinting).
- **Soft-block / poisoned data:** 200 with plausible-looking but *wrong* content (shadow-ban). Detected by cross-source disagreement (the source-fusion layer) and by per-field plausibility (orgnr checksum, MX-valid email).

### 3.2 Reference implementation

```python
# failure_classifier.py
from enum import Enum
import re

class Failure(Enum):
    OK = "ok"
    RATE_LIMIT = "rate_limit"          # 429 → slow, keep identity
    FORBIDDEN = "forbidden"            # 403 generic → rotate identity
    CF_CHALLENGE = "cf_challenge"      # → escalate to browser/flaresolverr
    DATADOME = "datadome"              # → camoufox/residential + slow
    PERIMETERX = "perimeterx"
    AKAMAI = "akamai"                  # → match _abck sensor / browser
    IMPERVA = "imperva"
    AWS_WAF = "aws_waf"
    EMPTY_RENDER = "empty_render"      # 200 but JS shell → escalate tier
    HONEYPOT = "honeypot"             # identity burned → blacklist+rotate
    CAPTCHA = "captcha"                # → solver / licensed tool
    SERVER_ERR = "server_err"          # 5xx → backoff+retry
    NETWORK = "network"                # DNS/conn reset → quick retry
    POISONED = "poisoned"              # soft-ban, wrong data → rotate identity

_CF   = re.compile(r"cf-mitigated|__cf_chl|just a moment|challenge-platform", re.I)
_DD   = re.compile(r"datadome|captcha-delivery", re.I)
_PX   = re.compile(r"_px|px-captcha|/_px/", re.I)
_AKAM = re.compile(r"_abck|ak_bmsc|bm_sz", re.I)
_IMP  = re.compile(r"incap_ses|incapsula incident|___utmvc", re.I)
_AWS  = re.compile(r"awswaf|x-amzn-waf", re.I)
_CAP  = re.compile(r"g-recaptcha|hcaptcha|turnstile|funcaptcha", re.I)

def classify(status: int, headers: dict, body: str,
             required_selector_present: bool | None,
             body_len: int) -> Failure:
    h = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
    blob = h + "\n" + (body[:8000].lower() if body else "")

    if status in (0,) or body is None:           return Failure.NETWORK
    if _DD.search(blob):                          return Failure.DATADOME
    if _PX.search(blob):                          return Failure.PERIMETERX
    if _IMP.search(blob):                         return Failure.IMPERVA
    if _AWS.search(blob):                         return Failure.AWS_WAF
    if _AKAM.search(blob) and status in (403,429):return Failure.AKAMAI
    if _CF.search(blob) or status == 403 and "cf-ray" in h:
        return Failure.CF_CHALLENGE
    if status == 429:                             return Failure.RATE_LIMIT
    if status == 403:                             return Failure.FORBIDDEN
    if _CAP.search(blob):                         return Failure.CAPTCHA
    if 500 <= status < 600:                       return Failure.SERVER_ERR
    if status == 200:
        if required_selector_present is False:    return Failure.EMPTY_RENDER
        if body_len < 512:                        return Failure.EMPTY_RENDER
        return Failure.OK
    return Failure.FORBIDDEN

# Honeypot detection runs on the parsed DOM, separately:
def hit_honeypot(dom) -> bool:
    for a in dom.select("a[href]"):
        st = (a.get("style") or "").replace(" ", "").lower()
        if any(x in st for x in ("display:none","visibility:hidden","width:0","height:0")):
            if a.get("_was_followed"):  # our crawler flag
                return True
    return False
```

### 3.3 Remediation map

The classifier output drives a deterministic remediation policy. This is the "auto-correct errors / sense and adapt method" core:

```python
REMEDIATION = {
    Failure.RATE_LIMIT:   ("slow_down",      None,            "keep_identity"),
    Failure.FORBIDDEN:    ("rotate_identity", None,           "retry"),
    Failure.CF_CHALLENGE: ("escalate_tier",  "flaresolverr",  "rotate_identity"),
    Failure.DATADOME:     ("escalate_tier",  "camoufox",      "residential+slow"),
    Failure.PERIMETERX:   ("escalate_tier",  "camoufox",      "residential"),
    Failure.AKAMAI:       ("escalate_tier",  "playwright_stealth","match_fp"),
    Failure.IMPERVA:      ("escalate_tier",  "botasaurus",    "rotate_identity"),
    Failure.AWS_WAF:      ("escalate_tier",  "botasaurus",    "rotate_identity"),
    Failure.EMPTY_RENDER: ("escalate_tier",  "playwright_stealth","retry"),
    Failure.HONEYPOT:     ("blacklist_proxy",None,            "rotate_identity"),
    Failure.CAPTCHA:      ("escalate_tier",  "captcha_solver","or_licensed"),
    Failure.SERVER_ERR:   ("backoff",        None,            "retry"),
    Failure.NETWORK:      ("quick_retry",    None,            "retry"),
    Failure.POISONED:     ("rotate_identity",None,            "cross_check"),
}
```

`"or_licensed"` means: if a host repeatedly reaches CAPTCHA and the bandit shows even FlareSolverr failing, the remediation router promotes **UiPath/Sequentum** for that host — the licensed tools become the survival path. That is the explicit "escalate to licensed tool" rung.

---

## 4. AdaptiveLimiter — AIMD Congestion Control per Host

Speed must auto-tune: ramp up while green, collapse on the first block. We borrow **TCP congestion control (AIMD)** — Additive Increase, Multiplicative Decrease — applied to *per-host concurrency* and *per-host rate*. This is conceptually what **Scrapy AutoThrottle** does (it targets a latency-derived concurrency), but we make the *block signal* the controller input, not just latency.

### 4.1 Concepts & libraries

- **AIMD:** on each success, `cwnd += 1` (additive increase). On each block/429, `cwnd = max(1, cwnd * 0.5)` (multiplicative decrease). Same loop that gives TCP its sawtooth — provably converges to fair max throughput.
- **Token-bucket rate limit:** [`pyrate-limiter`](https://github.com/vutran1710/PyrateLimiter) (~400★) gives per-key buckets; [`aiolimiter`](https://github.com/mjpieters/aiolimiter) gives an async leaky-bucket; **`aiometer`** (run_all with `max_at_once` + `max_per_second`) caps both concurrency and rate in one call. JS side: **`bottleneck`** (reservoir + minTime) is the canonical equivalent.
- **Backpressure:** the limiter's semaphore *is* the backpressure — when `cwnd` shrinks, `acquire()` blocks producers, so the queue naturally drains slower instead of piling failures.
- **AutoThrottle reference:** Scrapy's `AUTOTHROTTLE_TARGET_CONCURRENCY` algorithm — we reuse its latency-EWMA idea as a secondary governor (don't exceed the concurrency that keeps latency near the target).

### 4.2 Reference implementation

```python
# adaptive_limiter.py
import asyncio, time

class HostLimiter:
    """AIMD concurrency + token-bucket rate, per host. TCP-style sawtooth."""
    def __init__(self, host, cwnd=2, cwnd_max=64, min_interval=0.0,
                 target_latency_ms=1500):
        self.host = host
        self.cwnd = float(cwnd)              # current concurrency window
        self.cwnd_max = cwnd_max
        self.target_latency_ms = target_latency_ms
        self._sem = asyncio.Semaphore(int(cwnd))
        self._inflight = 0
        self._tokens = cwnd                  # token bucket
        self._rate = cwnd                    # tokens/sec ~ cwnd
        self._last = time.monotonic()
        self._min_interval = min_interval
        self._ewma_latency = target_latency_ms
        self._lock = asyncio.Lock()

    async def acquire(self):
        # token bucket throttle (rate) ...
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(self.cwnd, self._tokens + (now-self._last)*self._rate)
            self._last = now
            while self._tokens < 1:
                await asyncio.sleep(1.0 / max(self._rate, 0.1))
                now = time.monotonic()
                self._tokens = min(self.cwnd, self._tokens + (now-self._last)*self._rate)
                self._last = now
            self._tokens -= 1
        await self._sem.acquire()            # concurrency window (backpressure)
        self._inflight += 1

    def release(self):
        self._inflight -= 1
        self._sem.release()

    async def on_success(self, latency_ms):
        """Additive increase, governed by latency (AutoThrottle idea)."""
        self._ewma_latency = 0.8*self._ewma_latency + 0.2*latency_ms
        async with self._lock:
            if self._ewma_latency < self.target_latency_ms and self.cwnd < self.cwnd_max:
                self.cwnd += 1.0                 # +1 per RTT of green
            self._rate = self.cwnd
            await self._resize()

    async def on_block(self, hard=False):
        """Multiplicative decrease. Hard block (CF/DataDome) cuts harder."""
        async with self._lock:
            factor = 0.25 if hard else 0.5
            self.cwnd = max(1.0, self.cwnd * factor)
            self._rate = self.cwnd
            await self._resize()

    async def _resize(self):
        target = max(1, int(self.cwnd))
        cur = self._sem._value + self._inflight
        # grow/shrink the semaphore to match cwnd
        while cur < target:
            self._sem.release(); cur += 1
        # shrinking happens lazily as inflight requests release into a smaller window
```

**Behavioral guarantee:** while a host is green the window climbs +1 per round-trip until either `cwnd_max` or the latency ceiling, so a friendly host (open registry, brreg API) ramps to 64-wide in seconds. The first 429 halves it; a CF/DataDome hard block quarters it. The sawtooth keeps us riding *just under* the block threshold — i.e. maximum speed the target tolerates, discovered live, no hand-tuning. Per-host isolation (the **Bulkhead pattern** from `architecture_patterns_reference.md`) means LinkedIn collapsing to cwnd=1 never slows allabolag.se.

---

## 5. Identity Management — Cohesive Fingerprint Profiles

Random rotation is *detectable*: a Chrome User-Agent paired with a Firefox JA3 and a German Accept-Language from a US IP is an instant ban. The engine binds **UA + full header set + TLS/JA3 + HTTP2 fingerprint + viewport + timezone/locale + proxy geo** into one coherent `IdentityProfile` and rotates *the whole profile*, never a single axis.

### 5.1 Libraries

- **[`browserforge`](https://github.com/daijro/browserforge)** (1.1k★) — Markov-chain generator that emits *internally consistent* UA + headers + screen + a matching fingerprint; this is the core profile factory.
- **[`fake-useragent`](https://github.com/fake-useragent/fake-useragent)** (4k★, archived) / **[`intoli/user-agents`](https://github.com/intoli/user-agents)** (1.2k★, daily-updated) — UA pools when we need raw strings.
- **`curl_cffi` impersonate targets** — the TLS layer must match the UA: `chrome131`, `chrome124`, `firefox133`, `safari17_0`, `edge101`, etc. We map each profile's browser→an `impersonate=` token so JA3/JA4/HTTP2 align with the declared UA.
- **`browserforge.fingerprints`** also feeds Playwright/Camoufox so the *browser* tier reuses the *same* profile (consistent escalation — when we escalate curl_cffi→Playwright for a host, we hand Playwright the identical UA/viewport/locale/proxy).
- **[`fakeredis`](https://github.com/cunla/fakeredis-py)** — for unit-testing the identity store / router without a live Redis.
- **Proxy geo** from the proxy catalog (ProxyBroker, monosans/proxy-list, residential tiers) is pinned per profile so a Swedish target gets a Nordic-geo identity (Sticky-Session pattern).

### 5.2 Reference structure

```python
# identity.py
from dataclasses import dataclass
from browserforge.fingerprints import FingerprintGenerator
import random

# curl_cffi impersonation token must match the chosen browser/version
IMPERSONATE_MAP = {
    ("chrome", 131): "chrome131", ("chrome", 124): "chrome124",
    ("firefox", 133): "firefox133", ("safari", 17): "safari17_0",
    ("edge", 101): "edge101",
}

@dataclass
class IdentityProfile:
    user_agent: str
    headers: dict          # Accept, Accept-Language, sec-ch-ua, ... all consistent
    impersonate: str       # curl_cffi token => binds TLS/JA3/JA4/HTTP2
    viewport: tuple        # (w, h) for browser tier
    locale: str            # e.g. sv-SE
    timezone: str          # e.g. Europe/Stockholm
    proxy: str             # ip:port (geo-matched, sticky per host)
    browser: str
    version: int

class IdentityFactory:
    def __init__(self, proxy_pool):
        self.gen = FingerprintGenerator()
        self.proxy_pool = proxy_pool   # geo-aware

    def make(self, geo="SE", browser=None) -> IdentityProfile:
        fp = self.gen.generate(browser=browser)        # coherent UA+headers+screen
        b  = fp.navigator.userAgentData.brands[-1].brand.lower().split()[0]
        v  = int(fp.navigator.appVersion.split(".")[0]) if False else 131
        imp = IMPERSONATE_MAP.get((b, v), "chrome131")
        return IdentityProfile(
            user_agent=fp.navigator.userAgent,
            headers=fp.headers,                         # full consistent set
            impersonate=imp,
            viewport=(fp.screen.width, fp.screen.height),
            locale=fp.navigator.language,
            timezone="Europe/Stockholm" if geo=="SE" else "UTC",
            proxy=self.proxy_pool.sticky(geo),          # geo + sticky per host
            browser=b, version=v,
        )
```

When the FailureClassifier returns `rotate_identity`, the engine calls `IdentityFactory.make()` for a *fresh whole profile* and blacklists the burned one in Redis (`identity:burned:{host}`). When it returns `keep_identity` (429), it reuses the same profile but waits — because rotating identity on a pure rate-limit just burns more IPs for nothing.

---

## 6. Self-Healing, Retries & Durability

- **Circuit breakers per host:** [`pybreaker`](https://github.com/danielfm/pybreaker) (~700★) — after N consecutive hard-blocks the breaker opens, the host is parked for a cooldown (Adaptive-Backoff table from `architecture_patterns_reference.md`: `block_403: [300,600,1800,3600]`), and the engine spends effort elsewhere instead of hammering a wall.
- **Retries with jittered exponential backoff:** [`tenacity`](https://github.com/jd/tenacity) (~6k★) — `@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))`. Jitter prevents thundering-herd re-tries that themselves trigger rate limits.
- **Dead-Letter Queue:** the Docker/K8s topology in `docker_scraping_infrastructure_guide.md` already defines a DLQ. URLs that exhaust all tiers (including licensed) land in `tasks:dlq:{host}` with the full failure trace for human review / later replay when the host's posture relaxes.
- **Checkpoint / resume:** every URL's state (`pending→inflight→done|dlq`) and the last successful method/identity are persisted in Redis/Postgres, so a worker crash or a fleet restart resumes exactly where it stopped — no re-scraping (also the dedup-cost-saver from the cost reference).
- **Self-correction loop:** the router's online learning *is* the self-correction — no human edits a config when a site changes; the posteriors move and the cascade re-routes.

```python
# orchestrate.py — one URL through the full cascade
import time, tenacity
async def fetch_one(url, host, router, limiter, idf, classifier, fetchers):
    breaker = breakers[host]
    if breaker.opened:                      # circuit open -> park
        return await park(url, host)
    method = await router.choose(host)      # bandit picks cheapest-that-works
    identity = idf.make(geo=geo_for(host))
    await limiter.acquire()
    t0 = time.monotonic()
    try:
        resp = await fetchers[method](url, identity)   # curl_cffi/playwright/sequentum...
        lat = (time.monotonic()-t0)*1000
        sel_ok = host_assert(host, resp.body)          # content-presence check
        fail = classifier(resp.status, resp.headers, resp.body, sel_ok, len(resp.body or ""))
        ok = fail is Failure.OK
        await router.update(host, method, ok, lat)
        if ok:
            await limiter.on_success(lat); breaker.call_succeeded()
            return resp
        # ----- remediate -----
        action, esc_method, ident_act = REMEDIATION[fail]
        hard = fail in (Failure.CF_CHALLENGE, Failure.DATADOME, Failure.PERIMETERX,
                        Failure.AKAMAI, Failure.IMPERVA, Failure.AWS_WAF)
        await limiter.on_block(hard=hard); breaker.call_failed()
        if action == "blacklist_proxy": idf.burn(identity)
        if action == "escalate_tier":   return await retry_with(esc_method, url, host)
        if action == "slow_down":       return await retry_same(method, url, host)
        return await retry_with_rotation(url, host)
    finally:
        limiter.release()
```

---

## 7. Cross-Source Fusion — Speed AND Coverage Simultaneously

The seventh goal ("combine all sources to both raise coverage and speed; a cheap API confirms a scrape so the slow scrape is skipped") is implemented as a **pre-flight + post-flight fusion gate** wrapping the cascade:

- **Pre-flight short-circuit (speed):** before scraping a company, the engine fires the **tier-0 confirms in parallel** — Apollo MCP enrich, Bolagsverket iXBRL, brreg (NO), PRH (FI), GLEIF, the platform's own Fabric `allabolag__companies` 1.86M cache. If two independent cheap sources already agree on the field we need (orgnr, VD, revenue), we **skip the slow scrape entirely** and mark the record `resolved_by=fusion`. This is the single biggest speed lever: ~30–50% of records never need a browser at all.
- **Confidence-weighted fusion (coverage):** when scraping *is* needed, results from every method/source are merged with a probabilistic score (this is the `contact-intel` scoring lane + dedup/fuzzy-match repos from the catalog). A LinkedIn profile found by DuckDuckGo + an email confirmed by MX + a registry officer name reinforce one entity; disagreement flags `POISONED` (soft-ban detection feeds back into the classifier).
- **Parallel-combination throughput:** the fusion gate and the cascade run as `aiometer.run_all` fan-outs (Fan-Out/Fan-In pattern), so 100 companies × {api, scrape, linkedin} all run concurrently under their respective per-host limiters — maximizing every kind of parallelism (per-source, per-host, per-worker).

---

## 8. One-URL Decision State Machine

```
                         ┌────────────────────────┐
                         │  URL dequeued (host H)  │
                         └───────────┬────────────┘
                                     ▼
                  ┌──────────────────────────────────────┐
                  │ PRE-FLIGHT FUSION (tier-0, parallel)  │
                  │ Apollo / Bolagsverket / brreg / PRH / │
                  │ Fabric cache  ── 2 sources agree? ────┼──► YES ─► DONE (resolved_by=fusion, NO SCRAPE)
                  └──────────────────┬───────────────────┘
                                     │ NO / partial
                                     ▼
                       ┌──────────────────────────┐
                       │ circuit breaker open? ────┼──► YES ─► PARK (cooldown, try later)
                       └────────────┬─────────────┘
                                    │ NO
                                    ▼
                  ┌──────────────────────────────────────┐
                  │ MethodRouter.choose(H)  (Thompson)    │
                  │  → cheapest method currently winning  │
                  └──────────────────┬───────────────────┘
                                     ▼
                  ┌──────────────────────────────────────┐
                  │ AdaptiveLimiter.acquire(H)  (AIMD)    │  ◄─ backpressure
                  │ IdentityFactory.make(geo)  (coherent) │
                  └──────────────────┬───────────────────┘
                                     ▼
                       ┌──────────────────────────┐
                       │  FETCH via chosen method  │
                       └────────────┬─────────────┘
                                    ▼
                  ┌──────────────────────────────────────┐
                  │ FailureClassifier(status,hdr,body,sel)│
                  └───┬───────────┬───────────┬───────────┘
                      │ OK        │ soft       │ hard block
                      ▼           ▼            ▼
              ┌───────────┐  ┌─────────────┐  ┌───────────────────────────┐
              │limiter.   │  │429 RATE_LIMIT│  │CF/DataDome/PX/Akamai/...   │
              │on_success │  │→slow,keep id │  │→limiter.on_block(hard)     │
              │router +α  │  │403 FORBIDDEN │  │→escalate tier (browser →   │
              │POST-FUSION│  │→rotate id    │  │  Botasaurus → Camoufox →   │
              │ merge     │  │EMPTY_RENDER  │  │  FlareSolverr → Sequentum  │
              └─────┬─────┘  │→escalate tier│  │  → UiPath → captcha)       │
                    ▼        │HONEYPOT      │  │→router −β (demote arm)     │
                  DONE       │→burn proxy   │  └─────────────┬─────────────┘
                             └──────┬──────┘                │
                                    ▼                       ▼
                         ┌────────────────────┐   tries exhausted (incl licensed)?
                         │ tenacity retry w/   │──────────────► YES ─► DLQ
                         │ jittered backoff    │                       (trace stored,
                         └─────────┬──────────┘                        replay later)
                                   └────► loop back to MethodRouter.choose()
```

---

## 9. Config (engine.yaml)

```yaml
router:
  policy: thompson            # thompson | epsilon_greedy | ucb1  (mabwiser-backed)
  epsilon_floor: 0.03         # always reserve exploration of cheap arms
  decay_gamma_per_hr: 0.98    # non-stationarity / auto-demote
  methods: [api_confirm, curl_cffi, wreq, cloudscraper, scrapling,
            botasaurus, playwright_stealth, camoufox, nodriver,
            flaresolverr, screaming_frog, sequentum, uipath, ranorex, captcha_solver]

limiter:
  cwnd_init: 2
  cwnd_max: 64
  target_latency_ms: 1500
  decrease_factor_soft: 0.5
  decrease_factor_hard: 0.25
  rate_lib: aiometer          # aiometer | pyrate_limiter | aiolimiter

breaker:
  fail_threshold: 5
  reset_timeout_s: 1800
  backoff_403: [300, 600, 1800, 3600]

identity:
  factory: browserforge
  ua_pool: intoli_user_agents
  sticky_session_ttl_s: 3600
  geo_default: SE
  burn_on: [honeypot, poisoned]

fusion:
  preflight_sources: [apollo, bolagsverket, brreg, prh, gleif, fabric_allabolag]
  skip_scrape_if_agreeing_sources: 2

retry:
  lib: tenacity
  max_attempts: 5
  wait: random_exponential
  wait_max_s: 60

dlq:
  backend: redis
  replay_when_host_green: true
```

---

## 10. Repo Shortlist (engine dependencies, all free)

| Concern | Repo | Stars | Why |
|---------|------|-------|-----|
| Bandit policy | [fidelity/mabwiser](https://github.com/fidelity/mabwiser) | ~1k | Thompson/UCB1/ε-greedy, contextual-ready |
| HTTP tier-1 | [lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) | 5.9k | TLS impersonate, fastest |
| HTTP tier-1 alt | [0x676e67/wreq-python](https://github.com/0x676e67/wreq-python) | 1.4k | HTTP/3 + TLS |
| CF-lite | [VeNoMouS/cloudscraper](https://github.com/VeNoMouS/cloudscraper) | 6.6k | cheap CF IUAM solve |
| Browser stealth | [omkarcloud/botasaurus](https://github.com/omkarcloud/botasaurus) | 4.8k | CF JS, framework |
| Hardened FF | [daijro/camoufox](https://github.com/daijro/camoufox) | 9.5k | DataDome/PX/Turnstile |
| Async undetected | [ultrafunkamsterdam/nodriver](https://github.com/ultrafunkamsterdam/nodriver) | 4.4k | fast browser tier |
| CF-as-service | [FlareSolverr/FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) | 14.4k | challenge pool |
| Fingerprint factory | [daijro/browserforge](https://github.com/daijro/browserforge) | 1.1k | coherent profiles |
| UA pool | [intoli/user-agents](https://github.com/intoli/user-agents) | 1.2k | daily UA |
| Rate limit | [vutran1710/PyrateLimiter](https://github.com/vutran1710/PyrateLimiter) | ~400 | token buckets |
| Async limit | [mjpieters/aiolimiter](https://github.com/mjpieters/aiolimiter) | ~500 | leaky bucket |
| Retries | [jd/tenacity](https://github.com/jd/tenacity) | ~6k | jittered backoff |
| Circuit breaker | [danielfm/pybreaker](https://github.com/danielfm/pybreaker) | ~700 | per-host breakers |
| Test Redis | [cunla/fakeredis-py](https://github.com/cunla/fakeredis-py) | ~1k | unit tests |
| FP analysis | [niespodd/browser-fingerprinting](https://github.com/niespodd/browser-fingerprinting) | 5k | honeypot/FP vectors |
| Akamai FP | [gospider007/fp](https://github.com/gospider007/fp) | ~120 | JA3/JA4/HTTP2 char. |

---

## 11. How This Satisfies the Eight Platform Goals

1. **Every free repo maximally** — all tiers are OSS; the bandit *uses* each repo exactly where it wins.
2. **Every licensed tool maximally** — Screaming Frog / Sequentum / UiPath / Ranorex are first-class bandit arms, promoted automatically for hosts only they crack.
3. **Maximum speed** — AIMD rides just under each host's block threshold; tier-0 fusion skips 30–50% of scrapes outright.
4. **Auto error/block self-correction** — FailureClassifier → deterministic remediation; bandit posteriors self-heal on site changes; tenacity + pybreaker + DLQ.
5. **Senses & adapts method + concurrency live** — per-host Thompson Sampling (method) + per-host AIMD (concurrency), both online, both decaying for non-stationarity.
6. **Every kind of parallelism** — per-source, per-host, per-worker fan-out under isolated limiters (Bulkhead).
7. **Combine all sources for coverage AND speed** — pre-flight confirm short-circuits slow scrapes; post-flight confidence fusion raises coverage.
8. **Cover every entity across Nordics + Europe** — geo-pinned identities, registry APIs per country (brreg/PRH/Bolagsverket), licensed-tool escalation for the hardest portals.
```

