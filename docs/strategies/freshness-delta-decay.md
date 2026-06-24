# Strategy: Freshness — delta/change-feed subscription + decay-driven re-verification scheduling

**Cluster:** Freshness · **Layer:** temporal confidence / refresh
**Builds on:** `docs/architecture/pillars/fusion-confidence.md` §4 (freshness & decay, half-lives, re-verify queue), `docs/architecture/MASTER_BLUEPRINT_FULL.md` §4.2 (delta feeds), §4.5 (304/CDX), §7.5 (decay).
**Compose with:** `orchestrate-work-fabric` (refresh jobs enter as a fair-share lane), `cost-aware-fallback` (cheap re-checks before expensive re-scrape), `monitor-bandit-feedback` (decay parameters re-fit from observed correctness), `orchestrate-autoscale-seatbroker` (refresh surges drive autoscale).

---

## 1. Mechanism

B2B data is not static — it **decays 22–30%/year** (15–20% *quarterly* on unverified records). A record verified 14 months ago is statistically mostly wrong. This strategy keeps the canonical store fresh by two complementary mechanisms — **push** (subscribe to source change feeds) and **pull** (decay-scheduled re-verification) — so the estate never silently rots and the platform's calibrated-confidence promise stays true over time.

**(a) Delta / change-feed subscription (push, near-zero cost).** Instead of periodically re-pulling whole registers, the platform subscribes to each source's native delta feed and applies only the diff:
- **Bolagsverket** delta, **brreg** nightly + change endpoints, **DK CVR** updates, **Companies House** + **PSC** daily bulk diffs, **FR SIRENE/INPI** daily delta, **BE KBO** daily delta, **CZ ARES** / **PL** updates, **GLEIF** daily golden copy.
These land on the **Faust/Kafka change firehose** (from `orchestrate-work-fabric`), are partitioned by `(country, entity)`, and are **replayable** — a consumer crash never loses a change. A delta event flips the affected field's `verified_at` to "now" for free, removing it from the re-verify queue without a single scrape.

**(b) Field-specific decay (the temporal confidence input).** Every field carries `{verified_at, source}`. Freshness is `0.5^(age / half_life)`:

```
reg_id 3650d · legal_name 1825d · registered_address 730d · phone_mobile 500d
email 400d (~22%/yr) · role.title 270d (~9-mo) · website.liveness 30d · vehicle.owner 365d
```

So a registered company name barely decays while a person's direct dial and a role title decay fast — exactly matching real-world churn.

**(c) Decay-driven re-verification scheduling (pull).** A priority queue re-checks a field when `freshness < 0.6` **AND** the field matters (high-seniority roles, customer-flagged records re-checked sooner). It is a cron-driven sweep **sized so the whole estate cycles within one half-life of its fastest-decaying field** (website.liveness at 30d sets the sweep cadence). Re-checks climb the **cheapest-first** ladder:
1. **Free change-detection:** ETag/`Last-Modified` → `304 Not Modified` (hishel), Wayback-CDX / sitemap-`lastmod` diff, content-hash (`xxhash`/`blake3`) — a field on a page that *demonstrably hasn't changed* keeps high freshness, no re-extraction.
2. **Cheap confirm:** registry-diff, MX re-ping, libphonenumber re-validate.
3. **Expensive last:** full re-scrape / SMTP-RCPT, only when the cheap rungs are inconclusive *and* the field matters.

Change detection is itself a confidence input — proven-unchanged fields retain higher freshness than raw age implies.

## 2. Tools / repos it uses

- **[Faust-streaming](https://github.com/faust-streaming/faust)** + Kafka — partitioned, replayable delta firehose.
- **[hishel](https://github.com/karpetrosyan/hishel)** — HTTP cache honoring ETag/Last-Modified → `304`.
- **Wayback-CDX API / sitemap `lastmod`** — free change detection.
- **[xxhash](https://github.com/ifduyue/python-xxhash) / blake3** — content-hash dedup.
- **dnspython** (MX re-ping), **libphonenumber** (phone re-validate).
- **Redis** priority queue (the re-verify queue) + the per-field `verified_at` store in Fabric/Postgres.
- Source delta endpoints: Bolagsverket / brreg / CVR / Companies House / SIRENE / INPI / KBO / ARES / GLEIF.

## 3. Failure mode it eliminates

- **Silent staleness** — the headline failure of every incumbent (Apollo, Cognism, ZoomInfo claim freshness they can't show per-field). Without decay scheduling, a record looks "verified" forever; here it loses confidence on a measured clock and is re-checked before it misleads a customer.
- **Wasteful full re-pulls** — re-downloading whole national registers nightly is bandwidth/compute waste and a politeness risk; delta subscription replaces it with diffs.
- **Re-scrape storms** — without the cheap-first ladder, a freshness sweep would re-scrape the whole estate; `304`/CDX/content-hash short-circuits make most re-checks free.
- **Mis-prioritised refresh** — uniform re-verification wastes budget on `reg_id` (10-year half-life) while a `role.title` (9-month) goes stale. Field-specific half-lives + "field matters" gating eliminate it.

## 4. Composition

- → **`orchestrate-work-fabric`**: re-verify jobs and delta-applied updates enter as normal-priority `(country, domain)` shards, competing fairly with first-pass discovery; the Kafka firehose *is* the fabric's change lane.
- → **`cost-aware-fallback`**: the cheap-first re-check ladder is the freshness instance of free-before-paid — `304`/MX-ping precede any budgeted re-scrape.
- ↔ **`monitor-bandit-feedback`**: customer bounce/answer feedback re-fits the isotonic calibration and the per-source reliability that the freshness weighting feeds; observed churn can re-tune half-lives.
- ↔ **`orchestrate-autoscale-seatbroker`**: the morning re-verify surge drives scale-up; quiet windows scale to zero.

## 5. Success contribution

Freshness is the strategy that makes success **durable over time** rather than a one-shot snapshot. Its contribution: (a) **delta subscription** keeps company-level fields (the registry-carried 30–60%) continuously correct at near-zero marginal cost, so coverage doesn't erode between full builds; (b) **decay scheduling** ensures the fast-churning people/role/email fields — where the ~22–30%/yr decay actually bites — are re-verified on a clock matched to their half-life, holding their *calibrated* confidence honest (a `0.83` stays ~83% correct because stale fields are re-checked or down-weighted, not left to drift). Quantified honestly: freshness cannot create coverage the law closes (UBO, vehicle-owner) and cannot stop decay — it *bounds* decay's effect by re-verifying within one half-life, converting an uncontrolled 22–30%/yr rot into a managed, measured refresh cycle. That is precisely the per-field provenance + freshness wedge incumbents cannot match.

## 6. Compliance envelope

- **Re-verification respects the same caps** — a freshness sweep is dispatched through the work fabric's per-shard token buckets, so it cannot breach DE Handelsregister's ≤60/hr cap or any rate limit; it never becomes a back-door for an aggressive re-crawl.
- **Erasure propagation is a freshness duty** — a delta feed or a re-check that detects an Art.17 erasure / suppression flips the record to tombstoned and propagates to exports; freshness plumbing and right-to-erasure plumbing share the same path (`COMPLIANCE.md` §4).
- **`last_verified` provenance is non-optional** — every refreshed field re-stamps `{source, lawful_basis, verified_at}`; the freshness multiplier is computed from it, and the output API exposes `needs_reverify[]` honestly.
- **No SMTP at volume** — SMTP-RCPT re-confirmation is reserved for premium/low-volume from dedicated warmed IPs (never scraping proxies), to avoid Spamhaus/greylisting; routine refresh uses MX-ping only.
- **Delta feeds are official channels** — subscribing to a registry's published change feed is the *sanctioned*, lowest-impact way to stay fresh, fully aligned with the T1 "official-API/open-bulk first" posture.
