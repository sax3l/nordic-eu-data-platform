# Adversarial Verification — Nordic Data-Source Inventory

Verified: 2026-06-24. Method: independent WebSearch/WebFetch against official sources.
Scope: Sweden, Norway, Denmark, Finland, Iceland.

## Overall verdict: MOSTLY-SOLID

The inventory is unusually accurate. No hallucinated registries. Every named
registry, API base URL, bulk endpoint, GitHub sample client, and "free" claim that
I could check held up against primary sources. The few issues are minor freshness
drifts and one slightly-overstated "no WAF" claim. None of the error-prone areas
(vehicle registries, free-bulk claims) contained fabrications.

---

## CONFIRMED (high confidence)

### Sweden
- Bolagsverket + SCB high-value datasets FREE since **3 Feb 2025**, no contract — CONFIRMED
  (Bolagsverket press release + valuable-datasets page).
- Bulk file naming `bolagsverket_bulkfil.zip` (.txt inside) — CONFIRMED.
- iXBRL annual reports: **FREE weekly zip bulk, coverage 2020→** — CONFIRMED exactly
  (a new zip each week of the prior week's digitally-filed iXBRL reports, no cost/agreement).
- iXBRL **MANDATORY for all AB from FY starting after 31 Dec 2025** — CONFIRMED exactly.
- UBO "verklig huvudman" register at Bolagsverket, person-level access gated post-CJEU — CONFIRMED.
- Vehicle: Transportstyrelsen tsopendata portal (azure-api.net), PDM, free — CONFIRMED exists.
  NUANCE: the open dataset is largely **historical** vehicle data (annual snapshots
  extracted once/year per National Archives rules), explicitly NOT usable to verify
  current vehicle matters. Inventory's "limited" is fair but could be more explicit
  that the open feed is historical, not live.

### Norway
- Brønnøysund Enhetsregisteret open API + bulk, FREE (NLOD), nightly rebuild — CONFIRMED.
- Bulk endpoints `/api/enheter/lastned` (+/csv, /regneark) and `/api/underenheter/lastned` — CONFIRMED exactly.
- Roles bulk `/api/roller/totalbestand` free; `/autorisert-api/roller/totalbestand`
  with personal ID numbers requires Maskinporten — CONFIRMED exactly (incl. JWT resource
  claim + scopes; public-sector orgs get automatic access).
- Vehicle: Autosys Kjøretøy API at autosys-kjoretoy-api.atlas.vegvesen.no; anyone can
  apply for key; **max 50,000 calls/key/day**; full technical data, **NO owner info** — CONFIRMED exactly.

### Denmark
- CVR / Erhvervsstyrelsen — CONFIRMED.
- S2S Elasticsearch bulk at `http://distribution.virk.dk/cvr-permanent`, FREE but requires
  emailing `cvrselvbetjening@erst.dk` + signing data-conditions declaration — CONFIRMED exactly
  (also: takes ~couple weeks; must accept advertising-protection terms).
- Catalog page data.virk.dk/datakatalog/.../system-til-system-adgang-til-cvr-data — CONFIRMED.
- OSS client `gronlund/cvrdata` (Python, Elasticsearch, needs ERST credentials) — CONFIRMED exists.
- Vehicle: DMR public anonymous single lookup at motorregister.skat.dk ("Fremsøg/Vis køretøj",
  path visKoeretoej) — CONFIRMED. B2B SOAP gateway w/ cert auth — CONFIRMED.
- DMR B2B sample client `github.com/skat/dmr-b2b-ws-sample-client-java` — CONFIRMED exists,
  owned by skat org, Apache CXF/Spring, explicitly "example not production," no support.

### Finland
- PRH Trade Register + YTJ open data — CONFIRMED.
- API v3 base `https://avoindata.prh.fi/opendata-ytj-api/v3` + schema?lang=en — CONFIRMED.
- Bulk: all valid Trade Register companies as one compressed JSON, free, CC-BY, daily — CONFIRMED.
- Vehicle: Traficom "ajoneuvojen-avoin-data", fully open ZIP-CSV (ISO8859-1), CC BY 4.0,
  owner anonymised — CONFIRMED, easiest fully-open national fleet file claim holds.

### Iceland
- Fyrirtækjaskrá run by Skatturinn (Iceland Revenue & Customs) — CONFIRMED.
- No open API/bulk; free search UI; scrape-only — CONFIRMED (no open feed found).
- Ársreikningaskrá (Annual Accounts Register) under Skatturinn — CONFIRMED.
- UBO "raunverulegir eigendur" register (Act 82/2019) per-company lookup — CONFIRMED plausible.

---

## CORRECTIONS / NUANCES

1. **Finland vehicle figures are stale.** Inventory: "latest 30.9.2025, ~5,255,047 rows,
   ~930MB/202MB zipped." Current dataset (as of checks): **31.3.2026, 5,147,217 rows,
   892MB / 196MB zipped.** Row count and date are a refresh behind. Not an error — the
   dataset is a moving target — but the specific numbers should be treated as "approx,
   refreshed quarterly," not pinned.

2. **Sweden "Registry is open API/bulk = no WAF concern" is slightly overstated.** The
   human-facing download HTML page (nedladdningsbarafiler.2517.html) is itself behind a
   CAPTCHA/anti-bot when fetched programmatically. The DATA files and APIs are the open
   path; the marketing/landing HTML is gated. Minor, but "no WAF concern" should be scoped
   to the actual API/file endpoints, not the whole bolagsverket.se site.

3. **Sweden vehicle open data is historical, not current.** tsopendata's vehicle dataset is
   an annual snapshot and explicitly cannot verify current vehicle status. Inventory's
   "By-vehicle/owner bulk = paid file delivery" for live data is correct; the free open
   portion is historical only. Worth stating explicitly.

4. **Denmark vehicle public lookup shows owner/user info.** The anonymous motorregister
   lookup returns owner/user details (not just technical data), slightly more than the
   inventory implies. Inventory's core claim ("no fully-open owner BULK") still correct —
   only single lookups, no bulk owner feed.

5. **CJEU UBO ruling date.** Inventory says "post-CJEU 2022" — correct (22 Nov 2022,
   Joined Cases C-37/20 & C-601/20, Sovim). Worth noting the legitimate-interest framework
   has since been codified in AMLD6/AMLR, so "gated by legitimate interest" remains current.

---

## NO HALLUCINATIONS FOUND
Every registry, API, endpoint, and GitHub repo named in the inventory was independently
confirmed to exist. No invented APIs, no dead-on-arrival URLs detected in the checks run.

## POSSIBLE MISSED SOURCES (minor, not gaps in correctness)
- Sweden: Lantmäteriet also publishes "värdefulla datamängder" (geodata) — adjacent, not company.
- Denmark: cvrapi.dk and the public Virk REST (cvrapi) — lighter free alternatives to S2S
  for low-volume lookups; inventory only lists the heavyweight S2S path.
- Finland: financial statements are also in the v3 'xbrl' service (inventory notes this for
  PRH but frames it under "financial filings" only).
- Norway: Regnskapsregisteret now has an open API for key figures (regnskap) — inventory says
  "some via API" which is accurate but understated; the open accounts API is real and free.
