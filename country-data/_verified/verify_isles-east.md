# Verification: Isles-East data-source inventory (UK, IE, PL, CZ, HU)

Date: 2026-06-24. Method: independent WebSearch/WebFetch confirmation of registry names, free/bulk claims, API existence, vehicle-registry access, and UBO status. Focus on the error-prone classes (vehicle registries, "free bulk" claims, UBO public access).

Overall verdict: **mostly-solid**. No hallucinated registries. Every named registry, API, and bulk endpoint exists and is correctly characterized. The substantive issues are (1) one MISSED time-bomb on Poland CRBR public access ending 2026-07-01, and (2) several small precision nuances (access-gating, SOAP vs REST, "monthly" vs "5 working days"). The "verified" confidence label is largely justified.

---

## United Kingdom — CONFIRMED (solid)
- Companies House Public Data REST API at developer.company-information.service.gov.uk — confirmed official "Developer Hub, Built by Companies House." Free with registered key (well-established).
- Free monthly bulk CSV (en_output.html): CONFIRMED. 7-part ZIP (~470MB), CSV. NUANCE: page says updated "within 5 working days of the previous month end," not a strict monthly snapshot. Page also carries a notice that this product "will not be supported" (data quality caveat worth recording, not a blocker).
- PSC daily bulk JSON (en_pscdata.html): CONFIRMED. Free, overwritten daily before 10am GMT, newline-delimited JSON, single-file or ~500k-record chunks.
- Accounts Data Product (en_accountsdata.html): CONFIRMED. Free iXBRL/XBRL, daily (60-day rolling window) + historic monthly. The "~75% filed electronically" figure matches the page's own statement.
- DVLA VES API: CONFIRMED, including the "not accepting new registrations while we make system upgrades" note. Per-plate, free, x-api-key, JSON.
- DVSA MOT History API: CONFIRMED free. NUANCE: access requires DVSA *approval of an application form* (not pure self-service), and it additionally offers a full DB extract + by-date + by-vehicle-id methods — richer than the inventory's "full MOT history" phrasing. MOT data back to 2005 (GB).

## Ireland — CONFIRMED (solid)
- CRO Open Data Portal (opendata.cro.ie), daily bulk + API, CC-BY-4.0, current + dissolved: CONFIRMED. Mirrored on data.gov.ie; DCAT-AP-HVD compliant.
- Free Financial Statements dataset on the portal; fuller docs via CORE pay-per-call: CONFIRMED.
- RBO public access restricted since Nov-2022 CJEU, legislated 2023, legitimate-interest only, not open/bulk: CONFIRMED — and in practice even stronger (reportedly no legitimate-interest requests approved since public access ended).
- NVDF: owner data restricted to approved third parties under S.I. 287/2015 / Finance Act 1993 s.60(3); aggregate registration stats open (CSO PxStat): CONFIRMED. (Inventory cites TDM01/TDA01 table codes — plausible CSO codes; the open-aggregate-only characterization is correct regardless.)

## Poland — CONFIRMED with one MISSED time-bomb (mostly-solid)
- KRS open REST API (prs.ms.gov.pl/krs/openApi), free, full + current excerpts, dane.gov.pl card 27606: CONFIRMED. NUANCE: natural-person data is anonymized (names/PESEL) per the API — the inventory's "GDPR-trimmed" is correct but vague.
- REGON/GUS BIR1 API (api.stat.gov.pl/Home/RegonApi): CONFIRMED free, key by request. NUANCE: it is a SOAP/BIR1 web service, not a REST API; the inventory just labels it "API" (fine), but "REST" should not be assumed.
- CEIDG data warehouse + API (dane.biznes.gov.pl): CONFIRMED free/open-data. NUANCE: programmatic Data-Warehouse API access requires identity verification (National Node application), so "free APIs, plain fetch" is slightly optimistic for CEIDG specifically.
- RDF financial-statements repository (ekrs.ms.gov.pl/rdf/rd/, viewer rdf-przegladarka.ms.gov.pl): CONFIRMED free per-company search + download (XML/PDF), KRS number required.
- CRBR (crbr.podatki.gov.pl): free public search, no registration/fee, no bulk API: CONFIRMED as of today. **MISSED / TIME-BOMB:** CRBR public access is scheduled to END on 2026-07-01 (AML Act amendment implementing the CJEU ruling). The inventory presents CRBR as a currently-open free public source without flagging that public access expires in ~one week. This should be corrected — after 1 July 2026 CRBR drops to the same restricted (authorities/AML/legitimate-interest) tier as IE/CZ.
- CEPiK vehicle register, owners restricted, statistical open data dataset 1558 (CC-BY-4.0): CONFIRMED.

## Czech Republic — CONFIRMED (solid)
- ARES (ares.gov.cz) free REST API + open-data XML bulk, aggregates Commercial/Trade/RES registers, ~millions of subjects, daily: CONFIRMED. (Coverage of "~2.8M+ entities" is plausible/in-range; some sources cite up to ~5M economic subjects — count is approximate, not wrong in spirit.)
- Public register or.justice.cz free; Sbírka listin financial statements/articles/resolutions as free PDFs, no account: CONFIRMED.
- ESM (esm.justice.cz) UBO: PUBLIC ACCESS ENDED 17 Dec 2025 post-CJEU + Czech Supreme/Supreme-Administrative court rulings: CONFIRMED EXACTLY (date and rationale match the Ministry of Justice announcement).
- Central Register of Road Vehicles: owner/operator extract on request, CZK 100/request, via municipal offices, portal.gov.cz service S7198: CONFIRMED (cost, channel, and service ID all match). NUANCE: the exact URL slug is .../sluzby-vs/data-output-from-the-road-vehicle-register-S7198 (the inventory's "request-for-data-output-...S7198" resolves to the same service; the S7198 id is the stable anchor).

## Hungary — CONFIRMED (solid)
- e-Cégjegyzék (e-cegjegyzek.hu) free basic per-company lookup, no registration; no official free bulk/open API; bulk = paid (OPTEN, Bisnode/D&B, companyapi.hu): CONFIRMED. Free basic data is the Directive-2009/101/EC minimum; deeper extracts charged via Ministry-of-Justice Company Information Service contract.
- companyapi.hu: CONFIRMED real — third-party reseller of Ministry of Justice Company Information Service data, ~31 fields incl. officers/owners. Not a hallucination.
- UBO register exists under AML, public access limited post-CJEU, not an open bulk source: CONFIRMED in spirit (consistent with the EU-wide post-CJEU pattern).

---

## Hallucinations found
None. Every registry, portal, API, and bulk endpoint named is real and correctly attributed.

## Missed sources / context
1. Poland CRBR public-access SUNSET 2026-07-01 (the single most important miss — converts a "free public UBO source" into a restricted one within days).
2. UK: bulk CSV product carries an official "will not be supported" deprecation-style notice (data-quality caveat).
3. UK DVSA MOT API also offers a full-database extract (bulk) option, not only per-plate — an under-stated capability.

## Net
The inventory is accurate and free of fabrication. Downgrade from "verified→solid" only because of the CRBR timing miss and a handful of access-gating precision points. Recommended: re-label Poland CRBR and add the 2026-07-01 cutoff; soften "free APIs, plain fetch" for CEIDG (identity-verification gate) and REGON (SOAP, key-by-email); note REGON is SOAP not REST.
