# Strategy: Intake Suppression + Field-Level Provenance

**Cluster:** Compliance-as-Success (2 of 3)
**Status:** Executable. Folds critic fixes **P2-7** (suppress at intake), **P2-1** (no SMTP-RCPT from scraping IPs), and the **P0-4** reuse-restriction enforcement into the data path.
**Builds on:** `docs/architecture/pillars/fusion-confidence.md` §7 (provenance, DNC, erasure), `docs/architecture/MASTER_BLUEPRINT_FULL.md` §3.6 + §7.8, `docs/architecture/critic-gaps.md` P2-7/P2-1, `docs/COMPLIANCE.md` (GDPR by design).

---

## 1. The mechanism

This strategy makes GDPR mechanical at the two ends of the pipeline: **suppression at intake** (a person is never fetched, stored, or enriched if they have opted out or been erased) and **per-field provenance** (every value carries its source, lawful basis, and timestamp, and a value with no lawful basis cannot be emitted).

**Intake suppression.** National do-not-contact registers — SE NIX, DE Robinsonliste, FR Bloctel, plus equivalents per market — and the platform's own **erasure tombstones** are loaded as hard filters and checked at the **intake gate**, the same pre-flight stage where Bloom dedup and freshness TTL run. A contact whose normalized phone (E.164) or email hashes into a DNC set, or matches a tombstone, is dropped *before* any fetch lane, parse, or enrichment touches it. The blueprint originally filtered suppressed contacts only at output (fusion §7.4); the critic's P2-7 correction moves the check to intake so suppressed/erased people are never scraped or retained at all — shrinking both wasted scrape budget and the personal-data retention surface (data minimisation, Art. 5(1)(c)).

**Erasure tombstones.** A right-to-erasure request writes a `redaction` record: values are purged, but the `person_uid` surrogate and a salted hash of the natural keys are retained. Re-scraping that person later re-matches the tombstone at intake and is dropped — erasure is *durable* against re-ingestion rather than a one-time delete that the next crawl silently undoes. Erasure propagates to derived exports through the provenance graph (a single query answers "where did this value go").

**Field-level provenance.** Every canonical field carries `FieldProvenance{source_id, source_url, collected_at, method, lawful_basis, lia_ref, jurisdiction}`. Provenance is non-optional and enforced in the *schema*: the output API filters any field whose `lawful_basis` is absent or whose `reuse_restriction` forbids the requested use. Public-register firmographics carry `public_register` / `legal_obligation`; B2B work contact fields carry `legitimate_interest` backed by a documented LIA referenced in `lia_ref`; DE/FR personal contact fields default to shorter suppression/re-consent windows and are excluded from bulk exports unless the consumer attests B2B purpose; SE personnummer and equivalents are never stored for marketing. The per-source `reuse_restriction` from the policy gate (e.g. BE KBO contact fields tagged `no_direct_marketing`) is enforced here: the field stays in the graph for entity resolution but is withheld from contactable exports.

## 2. Tools / repos it uses

- **Suppression sets** — DNC lists (NIX/Robinsonliste/Bloctel) and tombstones held in Redis sets / Bloom filters keyed on E.164 phone and lowercased/IDN-normalized email; checked in the intake gate alongside the entity Bloom.
- **`libphonenumber` + `dnspython`** — phone E.164 normalization and email MX validation, so suppression matches on canonical forms, not raw strings.
- **Provenance store** — JSONB provenance sidecar on the canonical store (Postgres/Fabric columnar), one envelope per field; the resolution graph (`blocking`/`clusters`) in DuckDB/Spark carries source pointers for audit.
- **Output `lawful_basis` filter** — the read-model layer that drops fields lacking a basis or violating `reuse_restriction`, and honours `?contactable=true` by withholding `suppressed=true` fields.
- **Warmed dedicated SMTP IPs (premium only)** — per P2-1, SMTP-RCPT probing runs only from dedicated warmed IPs for low-volume premium verification, *never* from scraping proxies; bulk email confidence relies on MX + catch-all detection + cross-source agreement (fusion §5.3) so the platform never trips Spamhaus/greylisting and burns sending reputation.

## 3. The failure mode it eliminates

Two failure modes, both fatal to an EU data product:

1. **Contacting people who opted out or were erased** — a direct GDPR/ePrivacy breach (and, for SE NIX / FR Bloctel, a national-law breach) that generates complaints, regulator attention, and the kind of headline that ends a data business. Intake suppression makes it impossible to fetch or store them; output suppression catches anything that slipped through. Tombstones make erasure *stick* against the next crawl — eliminating the classic "we deleted them, then re-scraped them next week" violation.
2. **Emitting a field we cannot account for** — Apollo's structural weakness is exactly that it cannot say, per field, where a value came from or on what lawful basis. A field with no provenance is unauditable, so an Art. 14 / Art. 15 ("where did you get my data") request cannot be answered, and a `reuse_restriction` cannot be honoured. Schema-enforced provenance makes "unaccountable field" unrepresentable: no basis → not emitted.

It also eliminates the **self-inflicted infrastructure failure** of blacklisting the platform's sending IPs by mass SMTP probing from scraping proxies (P2-1).

## 4. Strategies it composes with

- **Policy gate** (`compliance-policy-gate.md`): the gate decides the lawful *acquisition* route and writes `reuse_restriction` + lawful route into provenance; this strategy enforces those at *storage and emission*. Gate = acquisition checkpoint, suppression/provenance = retention + emission checkpoints. A gate miss on `reuse=no_direct_marketing` is still caught at output (defense-in-depth: two independent layers, the second catches the first's residual).
- **Fusion + confidence** (fusion-confidence §5–§7): provenance is the substrate the log-odds fusion reads (which sources agreed, how fresh) and that the calibration loop audits. Validation-as-a-source (MX, libphonenumber) is recorded as provenance too, so the `method_badge` ("mx_confirmed_not_smtp") is provenance-backed honesty.
- **Sustainability moat** (`compliance-sustainability-moat.md`): the provenance trail and erasure plumbing *are* the moat's product surface — the `sources[]` + `lawful_basis` + `method_badge` envelope is what a buyer's DPO audits and what Apollo/ZoomInfo cannot show.
- **Intake dedup/Bloom** (speed §4.2/4.5): suppression piggybacks on the same intake gate as Bloom dedup and freshness TTL, so the compliance check costs essentially nothing extra and *reduces* downstream fetch volume.

## 5. Success contribution

Per-target EXTRACTION success is unaffected by suppression on the lawfully-contactable set — suppression only removes people who must not be in the output, which *raises* effective deliverability (no bounces to opted-out addresses, no complaints). The contribution to combined success is in *durability*: a pipeline that contacts opt-outs or cannot answer an Art. 15 request has its long-run success probability collapse to ~0 the moment a regulator or a large customer's DPO audits it. Intake suppression + schema-enforced provenance + durable tombstones drive the per-record "compliance defect that survives to output" rate toward zero, bounded only by suppression-list freshness (how recently we synced NIX/Bloctel) rather than by pipeline behaviour. Concretely it lifts the **emittable, contactable, auditable** fraction of the universe — the only fraction that has commercial value — and it does so while *shrinking* retained personal data, which lowers breach blast-radius and audit cost simultaneously.

## 6. Compliance envelope

This strategy is the GDPR-by-design core of the platform. Envelope: suppression checked at **intake and output** (Art. 5 minimisation, Art. 21 objection, national DNC law); **right-to-erasure** plumbed from day one with re-ingestion-proof tombstones (Art. 17); **field-level lawful basis** mandatory, with the Art. 6(1)(f) legitimate-interest path documented per LIA and the stricter DE (UWG) / FR (CNIL) windows encoded; **special-category and national personal IDs never stored for marketing**; **reuse restrictions** (`no_direct_marketing`, `authorities_only`) enforced at emission. It honours `docs/COMPLIANCE.md`'s technical-signals rule by keeping SMTP-RCPT off scraping IPs and off by default. It claims no coverage it cannot lawfully hold: suppressed and erased subjects are *deliberately* absent from contactable output, and that absence is a compliance feature, not a coverage failure. The only residual is list-sync latency (a person who opts out between two syncs), bounded by sync cadence and caught at the next output filter pass.
