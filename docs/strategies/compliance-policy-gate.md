# Strategy: Per-Source Compliance Policy Gate

**Cluster:** Compliance-as-Success (1 of 3)
**Status:** Executable. Folds critic fix **P0-4** and the policy-aware-routing correction into a first-class router precondition.
**Builds on:** `docs/architecture/MASTER_BLUEPRINT_FULL.md` §2 (Per-Source Policy Gate), `docs/architecture/pillars/adaptive-engine.md` (MethodRouter), `docs/architecture/critic-gaps.md` P0-4, `docs/COMPLIANCE.md` (source tiers + hard lines), `country-data/_verified/*.md` (the legal facts this gate encodes).

---

## 1. The mechanism

The adaptive engine is, by design, a relentless escalator: when `curl_cffi` is blocked it climbs to `cloudscraper`, then `camoufox`, then a licensed Sequentum/UiPath seat, and it *learns* to route straight to whatever cracks a host. That relentlessness is exactly what makes it dangerous against government registries that publish **hard legal caps**. Left ungoverned, the bandit would happily walk `handelsregister.de` past its 60-requests/hour ceiling — and that ceiling is not a politeness suggestion, it is the line above which **§§303a/b StGB** (German computer-sabotage / data-alteration criminal law) attaches. The same engine would escalate a headless browser against **ES CORPME** (`opendata.registradores.org` / `sede.registradores.org`), whose WAF explicitly rejects automated access, and keep hammering because a block, to a bandit, is just a signal to spend more.

The **policy gate** is a hard precondition that runs *after* the intake/dedup gate and *before* the MethodRouter ever samples an arm. It consults a machine-readable **per-source policy table**, keyed `(source, country)`, seeded directly from the `country_*.md` research:

```
policy[(source, country)] = {
  rate_cap_hard:            int | null,    # absolute req/hr ceiling, enforced as a token bucket
  automated_access_forbidden: bool,        # if true → bandit MAY NOT select any fetch method
  reuse_restriction:        enum,          # none | no_direct_marketing | authorities_only | b2b_attest
  preferred_alternative:    source_id | null,  # the lawful route to the same data
  legal_note:               text          # the cited statute / ToS clause
}
```

The gate's verdict is one of: **route to the bulk/API alternative** (e.g. DE Handelsregister → OffeneRegister bulk + openregister.de API; ES CORPME sede → BOE BORME gazette API; NL named companies → paid KVK API, never the anonymised free bulk); **cap-and-allow** (clamp the AdaptiveLimiter's token bucket to `rate_cap_hard` for that host, so the bandit can use it but can never exceed the legal ceiling); or **forbid** (mark the source `automated_access_forbidden` so the bandit's method list for that host is empty and the target is parked, not escalated). The router only ever sees the *post-gate* method set, so "never escalate here" is structurally impossible to violate rather than merely discouraged.

## 2. Tools / repos it uses

- **The policy table itself** — generated from `country-data/_verified/*.md` (the verified legal facts: DE 60/hr §303a/b, ES CORPME WAF-forbidden, BE KBO `no_direct_marketing`, NL KVK anonymised free bulk, FR INPI free reuse route vs RNE authorities-only). This is the "turn the country research into routing decisions" action the critic names as highest-leverage.
- **AdaptiveLimiter** (`aiometer` / `pyrate-limiter` / `aiolimiter`) — the existing per-host token bucket; the gate clamps its ceiling to `rate_cap_hard`. No new mechanism, just an authoritative input.
- **MethodRouter** (`mabwiser` Thompson/LinUCB) — receives a filtered arm set; `automated_access_forbidden` sources contribute *zero* arms.
- **Bulk Ingestion Plane** (Tier -1) and **Tier-0 API confirmers** — the `preferred_alternative` targets the gate redirects to (OffeneRegister, BORME, brreg, Zefix, GLEIF).
- **Output `lawful_basis` filter** (fusion layer §7) — consumes `reuse_restriction` so a `no_direct_marketing` field is kept for resolution but withheld from contactable exports (the hand-off to the suppression/provenance strategy).

## 3. The failure mode it eliminates

It eliminates the **single most existential failure mode in the blueprint**: an autonomous escalator committing a *criminal-law or access-control breach* against a government registry, or *re-marketing data a source legally forbids*. The critic frames this as the direct contradiction (P0-4) between the "scrape everything" framing of the engine docs and the "criminal exposure / WAF-hostile / forbidden reuse" reality of the country docs. A single §303a/b incident, a CORPME automated-access complaint, or an FPS-Economy reuse violation does not cost a retry — it can trigger an injunction, an IP/identity ban from the authoritative source, or a regulator action that shuts the operation down. In success-probability terms, an ungated escalator has a non-trivial per-run probability of an unrecoverable, operation-ending event; the gate drives that probability to ~0 on the catalogued sources by making the unlawful method *unselectable*.

## 4. Strategies it composes with

- **Suppression + provenance** (`compliance-suppression-provenance.md`): the policy gate decides *whether and how* to acquire a field; suppression/provenance decide *whether the acquired field may be emitted*. The gate writes `reuse_restriction` and the lawful route into provenance; the output filter enforces it. Two independent checkpoints — gate at acquisition, filter at emission — so a gate miss is still caught downstream (defense-in-depth).
- **Sustainability moat** (`compliance-sustainability-moat.md`): every lawful-route redirect the gate performs is evidence in the provenance trail that the moat sells — "we route to the licensed KVK API, not the anonymised bulk, and here is the record."
- **Skip-the-scrape arbitration** (fusion §6): the gate's `preferred_alternative` is almost always *cheaper* (a free bulk file or API confirm) than the scrape it replaces — so compliance and speed point the same way. Routing DE off Handelsregister onto OffeneRegister bulk is simultaneously the lawful move and the fast move.
- **Expected-utility seat routing** (licensed-tools §6.3): a `forbidden` verdict removes the target from the licensed-seat queue entirely, so scarce Sequentum/UiPath seats are never burned on a target that may not be automated.

## 5. Success contribution

Define per-source policy-violation probability as the chance a given run selects a method that breaches a hard cap, an automated-access ban, or a reuse restriction. Ungated, on the ~6 catalogued high-risk sources (DE Handelsregister, ES CORPME sede, BE KBO contact reuse, NL KVK, plus FR RNE authorities-only and the gazette WAFs), this is materially non-zero on every encounter and *compounds toward certainty* over millions of runs. The gate makes the violating method **structurally unselectable**, so the residual violation risk on catalogued sources is bounded by table-completeness error (a source whose policy we haven't yet encoded), not by router behaviour. Combined-success contribution: it converts the blueprint's biggest legal landmine from "near-certain eventually" to "bounded by how complete our policy catalogue is" — and because the redirects are to cheaper bulk/API routes, it *raises* throughput while removing the risk. This is the first layer of the defense-in-depth chain; the suppression layer catches its residual at emission time.

## 6. Compliance envelope

This strategy **is** a compliance control, so its own envelope is the union of every cap it enforces. It honours `docs/COMPLIANCE.md` end-to-end: official-API/open-bulk first (every redirect target is a T1/T2 lawful route); legal caps treated as **preconditions, not obstacles to brute through**; never aggressive-escalates a government registry (`automated_access_forbidden` empties the arm set); `no_direct_marketing` / `authorities_only` reuse fields are flagged for the output filter, never re-marketed. It explicitly does **not** attempt to widen any cap — where a source closes a door (NL KVK names behind a paid contract, ES UBO behind access control), the gate routes to the lawful paid/alternative route or records an honest coverage gap. The gate adds no new acquisition capability; it only ever *removes* unlawful options from the router. Failure-open is forbidden: if the policy table can't be loaded, the engine runs in conservative mode (cheapest-method-first, no escalation against any unknown government source) rather than defaulting to aggressive escalation.
