# Strategy — Bulk-First Sourcing

**Cluster:** Sourcing & Coverage · **Status:** Executable · **Date:** 2026-06-24
**Composes the Tier -1 Bulk Ingestion Plane** of `docs/architecture/MASTER_BLUEPRINT_FULL.md §2, §4.2`. Closes critic gap **P0-1**.

---

## The mechanism

Most of the work in a 50M-entity build is work we should never do. Before a single
socket opens, we **download whole national company registers** and load them into a
canonical store + a `registry_bulk_index` + an entity Bloom filter. The intake gate
then answers every entity that already exists in that index with **zero fetches**.
Bulk-first is Tier **-1** — strictly cheaper than the Tier-0 "fire a registry API to
confirm one entity" path, because one download settles *millions* of entities at once.

Each bulk source is a row in a per-country `BulkSource` registry seeded directly from
`country-data/_verified/*.md`: `{url, format, cadence, license, parser, policy}`. The
plane schedules each on its **native cadence** and subscribes to **delta/change feeds**
so the index stays fresh without re-pulling the whole file:

- **SE** Bolagsverket bulkfil (`bolagsverket_bulkfil.zip`) + **weekly iXBRL** annual-report bulk (free, no contract since 3 Feb 2025).
- **NO** Brønnøysund `/api/enheter/lastned` + `/api/underenheter/lastned` + roles `/api/roller/totalbestand` (NLOD, nightly rebuild).
- **DK** CVR S2S Elasticsearch (`distribution.virk.dk/cvr-permanent`, free after ERST data-conditions declaration).
- **FI** PRH/YTJ all-companies JSON (CC-BY, daily).
- **FR** SIRENE / INPI SFTP (Parquet). **BE** KBO daily full + SFTP. **NL** KVK + RDW.
- **UK** Companies House + PSC + accounts XBRL. **IE** CRO. **CZ** ARES XML. **PL** KRS/REGON. **CH** Zefix/LINDAS.
- **AT/DE** HVD / OffeneRegister. **GLEIF** golden copy (the cross-border `LEI ↔ reg-id` key, free daily).

Structured financials ride the same plane: SE weekly **iXBRL** is parsed with `arelle`
(not OCR — critic P1-7), turning a per-company scrape into a bulk load.

## Tools / repos it uses

- **Ingestion fabric:** `Arq` (download workers), `Faust`/Kafka for the delta-feed firehose (`MASTER_BLUEPRINT_FULL §4.3`).
- **Parsing:** `arelle` (iXBRL/XBRL fast path), `selectolax`/`lxml` for HTML register dumps, `orjson` for JSON bulk.
- **Index/dedup:** Redis/`datasketch` entity **Bloom filter**, `xxhash`/`blake3` content-hash dedup, `hishel` HTTP cache with ETag/`Last-Modified` so re-pulls return `304`.
- **Store:** Fabric/Postgres columnar canonical store + DuckDB resolution graph (`MASTER_BLUEPRINT_FULL §2`).
- **Country registry:** the machine-readable `BulkSource` table built from `country-data/_verified/`.

## Failure mode it eliminates

**Scrape-first myopia** — the single biggest speed-and-coverage regression. Without
bulk-first, the platform would re-discover, re-fetch, and re-parse company-level fields
(legal name, reg-id, address, status, SNI/NACE, officers) one host at a time, paying a
full anti-bot cost ladder for data a government already publishes as a free flat file.
Bulk-first removes **30–60 % of all company-level fetches** outright (`MASTER_BLUEPRINT_FULL §4.2`),
which is also what keeps the politeness budget, proxy bandwidth, and licensed seats free
for the residual that genuinely needs them. It also eliminates a **compliance** failure:
ingesting the open bulk means we never hammer a register's interactive UI (e.g. DE
Handelsregister's 60/h cap, ES CORPME's WAF) when a lawful flat file exists.

## Strategies it composes with

- **Multi-source redundancy** (`sourcing-multi-source-redundancy.md`): each bulk register is one of the ≥2 independent sources per field; bulk-first makes the *primary* source the cheapest one.
- **Cross-source confirmation** (`sourcing-cross-confirmation.md`): a bulk-index hit is a high-reliability confirmer (`r_s`≈0.99 for Bolagsverket/legal_name) that lets the slow scrape be skipped entirely.
- **Coverage-completion loop** (`coverage-completion-loop.md`): gap detection runs *against* the bulk index — "what's in the country universe but missing a contact field?" is the loop's seed.
- **Residual-tail handling** (`residual-tail-handling.md`): the no-bulk markets (IS, HU, IT, ES, PT, LU) and contact-level fields registries don't carry are exactly what bulk-first *cannot* solve and hands downstream.

## Success contribution

Bulk-first does not improve per-target extraction probability `pᵢ`; it **removes targets
from the fetch population**. If a fraction `b` of the universe (≈0.30–0.60 of
company-level fields) is bulk-settled at confidence ≥ target, then the expensive cascade
only ever runs on `(1−b)`. The effect on the program is multiplicative with everything
downstream: every later layer's cost, block-exposure, and identity-burn is scaled by
`(1−b)`. It is the layer that makes "50M in a day on ~33 IO workers" arithmetically
possible (`MASTER_BLUEPRINT_FULL §4.9`) — compute is never the wall once bulk-first has
shrunk the fetch set. Crucially, bulk-first raises **coverage** (more entities settled
lawfully) and **speed** (fewer fetches) with the *same* action — the two goals do not
trade off here.

## Compliance envelope

Bulk-first is the **most** compliant lane and the platform's default, exactly because it
uses **T1 primary-official open bulk** (`docs/COMPLIANCE.md` source tiers). Preconditions:

- **License is honored per source.** DK CVR S2S requires emailing `cvrselvbetjening@erst.dk` and signing the data-conditions declaration (and accepting advertising-protection terms) *before* ingest; FI is CC-BY (attribution carried in provenance); NO is NLOD. The `BulkSource.license` field gates ingestion.
- **Reuse restrictions travel with the data.** BE KBO contact fields and DE directory data are tagged `reuse=no_direct_marketing` at load; the output `lawful_basis` filter enforces it (critic P0-4).
- **Personal-data fields** carry `{source, lawful_basis, last_verified}` from the moment of bulk load; NO roles bulk with personal ID numbers (`/autorisert-api/...`) is **out of scope** — we take only the open `/api/roller/totalbestand`.
- **No WAF brute-through.** We fetch the open **API/file endpoints**, never the gated human landing pages (SE `nedladdningsbarafiler` HTML is CAPTCHA-walled — we use the file/API path, per verify_nordic correction #2).
- **NL caveat honored:** the free KVK bulk is anonymised (no name, no KVK number); bulk-first does **not** claim it as a deterministic key (critic P0-4) — that gap is flagged honestly, not fabricated.

**Honesty note:** bulk-first maximizes the lawfully-reachable company set; it cannot reach
data the law closes (UBO person-level, owner-PII) or markets with no open bulk. Those are
an explicit, quantified residual handed to `residual-tail-handling.md`, never papered over
as "100 % coverage."
