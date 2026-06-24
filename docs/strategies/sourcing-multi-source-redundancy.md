# Strategy — Multi-Source Redundancy

**Cluster:** Sourcing & Coverage · **Status:** Executable · **Date:** 2026-06-24
**Composes the source-race fabric + fusion layer** of `docs/architecture/MASTER_BLUEPRINT_FULL.md §4.4, §7`. Hardens against the single-points-of-failure called out in `critic-gaps.md`.

---

## The mechanism

**Every field must be reachable from at least two independent sources, so that one
source failing — going down, getting WAF-hostile, being legally closed, or simply being
wrong — never means data loss.** We treat each `(field, country)` as having a *source
set* rather than a single source, and we record, per source, a measured reliability
`r_s` (`MASTER_BLUEPRINT_FULL §7.4`). Concretely, for the most important fields:

- **legal_name / reg-id / status (company):** national register **bulk** (Tier -1) *and*
  the register's live API (Tier 0) *and* GLEIF (LEI↔reg-id) *and* an aggregator (North
  Data / Pappers / OpenCorporates, within each provider's ToS). Four independent paths.
- **VAT / active-status:** national register *and* VIES (cross-border anchor + active-status confirm).
- **email (contact):** website scrape (`r≈0.74`) *and* pattern inference + MX (`r≈0.55`)
  *and* an aggregator's API field — plus **validation as a pseudo-source** (MX/SMTP,
  catch-all detection) injected with its own reliability.
- **phone:** website scrape *and* directory (hitta/eniro/proff, T3) *and* libphonenumber validation.
- **person↔company role:** register officers bulk *and* website team/leadership page *and* public-SERP LinkedIn resolution (`linkedin_urn`, public surface only).
- **website:** register-declared domain *and* SERP discovery *and* DNS/MX liveness.

Redundancy is *engineered*, not incidental: the `BulkSource`/source registry tags which
sources cover which fields per country, and the router is required to have a **fallback
path** for any field whose primary is unavailable. When the primary fails its
`FailureClassifier` check (block, empty render, poisoned 200), the router doesn't give up
— it routes to the next independent source for that field.

## Tools / repos it uses

- **Router + classifier:** the adaptive engine (`mabwiser` Thompson bandit, `FailureClassifier`) selects *among* a field's sources by live cost/success (`MASTER_BLUEPRINT_FULL §3`).
- **Source backends:** Tier-0 registry/GLEIF/VIES clients; OSS fetch fabric (`curl_cffi`, `cloudscraper`, `Scrapling`, `Botasaurus`, `Camoufox`, `nodriver`); licensed backends behind one `ScraperBackend` (Screaming Frog, Sequentum, UiPath, Ranorex).
- **Validation pseudo-sources:** `dnspython` (MX), `libphonenumber`, website-liveness probe.
- **Fusion:** `RapidFuzz` blocking → `Splink` resolution → **log-odds agreement scoring** that the redundant sources feed into (`MASTER_BLUEPRINT_FULL §7.4`).

## Failure mode it eliminates

**Single-source data loss and silent single-source error.** If `legal_name` came only
from one scraped directory, then a CORPME WAF block, a Bolagsverket maintenance window, or
a poisoned soft-ban 200 would zero out that field for a whole country. Redundancy
converts each of those from a *data-loss* event into a *route-to-the-alternate* event.
It also eliminates **imported error**: a single source's mistakes (Apollo's claimed-97 %/
delivered-65–70 % accuracy) flow straight into the product unless a second independent
source can contradict them. With ≥2 sources, a wrong value is caught as a *disagreement*
that the fusion layer down-weights, rather than published as fact. This is the structural
prerequisite for the calibrated-honesty moat (`docs/COMPLIANCE.md §"why this wins"`).

## Strategies it composes with

- **Bulk-first** (`sourcing-bulk-first.md`): bulk registers are the cheapest member of most fields' source sets — redundancy is what lets us *also* keep a non-bulk path for the same field for the markets/fields bulk can't cover.
- **Cross-source confirmation** (`sourcing-cross-confirmation.md`): redundancy *provides the second source*; confirmation is what we *do* with two of them (agreement → confidence + skip-the-slow-source). The two are a pair — redundancy is the supply, confirmation is the consumer.
- **Coverage-completion loop** (`coverage-completion-loop.md`): when one source is exhausted on a field, the loop's next round tries the *redundant* source — redundancy is what gives the loop somewhere to go.
- **Residual-tail handling** (`residual-tail-handling.md`): a field with **only one** reachable source (or zero) is by definition fragile/closed and is flagged to the tail handler; redundancy is the test that classifies a field as "tail."

## Success contribution

Per-target *extraction* success on a field becomes the fallback-cascade formula
**`p_extract = 1 − Π(1 − pᵢ)`** over the independent sources `i` (`MASTER_BLUEPRINT_FULL`
fallback cascade). Two sources at `p=0.74` and `p=0.55` give `1 − (0.26·0.45) = 0.883`,
versus `0.74` from the best single source — and a third cheap source pushes it past
`0.95`. This is the mechanism by which **per-target extraction can approach ~100 %** even
though **no single source is near 100 %**. It is distinct from *universe coverage*: adding
sources raises the odds we extract a field *for an entity we can lawfully reach*, but it
**cannot** add entities the law closes — redundancy multiplies `p_extract`, not the
reachable universe. Independence is the load-bearing assumption: two sources that are
really the same upstream (a directory that re-publishes the register) count as one, so the
source registry tracks lineage to avoid fake redundancy.

## Compliance envelope

- **Every redundant source must independently pass the policy gate.** Adding a second
  source is never licence to use a *forbidden* one: ES CORPME stays `automated_access_forbidden`
  (route to BOE BORME instead), DE Handelsregister stays capped at 60/h (route to
  OffeneRegister), authenticated LinkedIn stays off (public SERP only). A redundant path
  that breaks a precondition is **not** a valid path.
- **Reuse restrictions are per-source**, so a field redundantly available from a
  `reuse=no_direct_marketing` source (BE KBO, DE directories) keeps that tag; fusion records *which* source supplied the emitted value so the output filter applies the strictest applicable restriction.
- **Provenance is per-value, not per-field:** the canonical record stores `sources[]` with each `{source_id, lawful_basis, collected_at}` — redundancy makes provenance richer, never vaguer.
- **No competitor-DB laundering:** aggregators (T2) are used within their API ToS as one independent source; we never OCR/UI-extract a competitor's login-gated DB to manufacture a "second source" (`docs/COMPLIANCE.md` hard line #1).

**Honesty note:** redundancy raises extraction reliability on the reachable set; it does
not and cannot conjure data from legally-closed sources. Fields with one-or-zero lawful
sources are reported as exactly that.
