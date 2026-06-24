# Strategy — Cross-Source Confirmation

**Cluster:** Sourcing & Coverage · **Status:** Executable · **Date:** 2026-06-24
**Composes the log-odds fusion + skip-the-scrape arbitration** of `docs/architecture/MASTER_BLUEPRINT_FULL.md §4.4, §7.4, §7.7`. Implements critic fix **P1-2** (staggered hedging, no paid-source in the race).

---

## The mechanism

When two independent sources **agree** on a field's value, two things happen at once:
confidence in that value rises (a coverage win), and the slow/expensive source we would
otherwise have launched can be **skipped or cancelled** (a speed win). One control flow,
both goals. This is the platform's headline differentiator — *agreement is simultaneously
a quality signal and a cost governor.*

Fusion is **log-odds** (`MASTER_BLUEPRINT_FULL §7.4`): each agreeing source contributes
`freshness · log(r_s/(1−r_s))`; disagreeing sources contribute half-weight negative
evidence; prior = `log(0.05/0.95)`. Two independent `r=0.75` sources that agree fuse to
≈0.90 — agreement **compounds**. A single registry at `r=0.99` anchors a field on its own.
A guessed `r=0.55` pattern-email stays low until something else confirms it. **Validation
acts as a pseudo-source:** a scraped email that also passes MX gets a second agreeing
signal; one that fails MX gets a strong contradiction; SMTP-RCPT confirm (`r≈0.9`)
outweighs catch-all MX (`r≈0.6`), and the badge surfaces *which* check passed.

The speed half is the **skip-the-scrape arbiter**. Before dispatching any expensive
method the router asks `need_expensive_fetch(entity, field, target_conf=0.85)`:

- current confidence ≥ target **and** fresh → **skip** (don't fetch at all);
- a cheap confirm would push it over → **cheap_only** (fire one cheap confirmer, stop);
- else → **full** (escalate the cascade).

Execution uses **staggered hedging, not parallel-everything** (`MASTER_BLUEPRINT_FULL §4.4`):
fire free/cheap Tier-0 confirmers (bulk index, registry API, cached lookup) first; only if
they miss the ~0.4 s deadline does the expensive browser tier launch. Because
`task.cancel()` does not instantly free an in-flight socket or Chromium tab, **not
launching** the expensive arm — rather than racing-then-cancelling — is what actually
saves proxy bandwidth and RAM.

## Tools / repos it uses

- **Fusion:** `Splink` (Fellegi-Sunter resolution into DuckDB/Spark), `RapidFuzz` blocking, the log-odds agreement scorer, isotonic `calibrate()` (`MASTER_BLUEPRINT_FULL §7.6`).
- **Cheap confirmers:** Tier-0 registry/GLEIF/VIES clients; the Tier -1 bulk index; `hishel` HTTP cache; the entity Bloom filter.
- **Validation pseudo-sources:** `dnspython` MX, catch-all detection, `libphonenumber`, website-liveness.
- **Arbitration plumbing:** `asyncio` staggered hedge (`hedged()` in `MASTER_BLUEPRINT_FULL §4.4`); the cost-aware counter that gates paid sources.

## Failure mode it eliminates

Three at once. **(1) Wasted expensive fetches:** without confirmation, the cascade would
escalate to a browser/licensed seat even when two free sources already agree — burning the
scarcest resources on already-known answers. **(2) Over-/under-confidence:** without
agreement scoring, a single noisy scrape would be published at the same confidence as a
registry-anchored fact (the exact failure that makes incumbents' "97 %/98 %" claims
hollow). **(3) The paid-credit double-charge** (critic P1-2): putting Apollo enrich in the
initial parallel wave risks spending a credit on a field a free registry would have won.
Confirmation gates the paid source *behind* the free-confirm miss, so we only pay when
cheap agreement genuinely failed.

## Strategies it composes with

- **Multi-source redundancy** (`sourcing-multi-source-redundancy.md`): redundancy *supplies* the ≥2 independent sources; confirmation is the logic that turns two of them into confidence-plus-skip. They are a supply/consume pair.
- **Bulk-first** (`sourcing-bulk-first.md`): a bulk-index hit is the cheapest, highest-`r_s` confirmer — it most often pushes a field over the target and cancels the cascade outright.
- **Coverage-completion loop** (`coverage-completion-loop.md`): confirmation defines "done" for a field (confidence ≥ target, fresh) — the loop terminates a field when confirmation says it's settled, and re-opens it when freshness decays below 0.6.
- **Residual-tail handling** (`residual-tail-handling.md`): **persistent disagreement** that even a browser tie-break can't resolve is a signal to route the entity to the tail (manual QA / licensed / honest gap), not to publish a coin-flip.

## Success contribution

Confirmation contributes to **both** axes. On **speed**: it is the largest single
fetch-suppressor *after* bulk-first — empirically ~70–85 % of entities terminate at the
cheap confirm stage at ≈80 ms, FREE (`MASTER_BLUEPRINT_FULL §4.4`), so only the hard tail
pays for a browser or a paid credit. On **quality/coverage**: agreement compounding lets
two mediocre sources jointly clear the 0.85 confidence bar that neither clears alone,
converting "reachable but low-confidence" fields into *publishable* ones — a genuine
coverage gain on the lawful set. Critically, the confidence numbers are **calibrated**
(isotonic regression vs registry-confirmable ground truth, re-fit quarterly): a field that
reads `0.83` is correct ~83 % of the time. Confirmation is therefore the mechanism that
makes the honesty moat *measurable* rather than asserted.

## Compliance envelope

- **Cheapest-and-most-lawful-first is preserved:** confirmation fires open registry/bulk/
  VIES confirmers before any scrape, so the most compliant source is also the one that
  most often ends the work. The policy gate still applies — a confirmer that would require
  a forbidden access (CORPME automated access, authenticated LinkedIn) is simply not in the
  confirmer set.
- **Validation pseudo-sources stay polite:** SMTP-RCPT confirm is reserved for premium/
  low-volume from dedicated warmed IPs, never scraping proxies (critic P2-1/P2-7), so
  confirmation never trips Spamhaus or burns probe IPs at scale.
- **Calibration honesty (critic P2-4):** cold-start calibration is bootstrapped only from
  the registry-confirmable subset; email/phone confidence is marked **uncalibrated** until
  bounce/answer feedback accrues — we never publish a calibrated number for a field with no
  ground truth.
- **Provenance of the confirming evidence is retained:** the emitted value records *which*
  sources agreed and *which* validation check passed, so a downstream consumer can audit
  the confidence, consistent with the per-field provenance requirement (`docs/COMPLIANCE.md §4`).

**Honesty note:** confirmation raises confidence on values we can lawfully observe twice;
where only one lawful source exists, the value is published at single-source confidence and
labelled as such — never inflated to imply corroboration that didn't happen.
