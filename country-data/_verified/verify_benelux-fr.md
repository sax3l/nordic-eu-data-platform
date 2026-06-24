# Adversarial Verification — Benelux + France Data-Source Inventory
Date: 2026-06-24
Scope: Netherlands, Belgium, Luxembourg, France
Method: independent WebSearch/WebFetch against official + reputable sources.

## Overall verdict: mostly-solid
The inventory is unusually accurate. No fabricated registries. No dead/wrong primary
URLs found. The most error-prone areas (vehicle registries, "free bulk" claims) were
handled correctly and conservatively. A handful of nuance corrections below; only one
materially-misleading URL (France actes/bilans pointing at the admin-gated API Entreprise
catalogue rather than the public data.inpi.fr route).

---

## NETHERLANDS — VERIFIED (solid)
- KVK open dataset is anonymised (no name, no KVK number, postcode 2-digit, BV/NV only);
  names require paid Handelsregister API (Zoeken/Basisprofiel). CONFIRMED on
  developers.kvk.nl + kvk.nl. Accurate.
- KVK Financial Statements Open Dataset (Jaarrekeningen) free + API. CONFIRMED.
- UBO register: access restricted; Dutch Amendment Act entered into force **15 July 2025**;
  UBO API expected **Q2 2026**. CONFIRMED almost verbatim (KVK, NautaDutilh, Greenberg
  Traurig). Underlying CJEU ruling is C-37/20 (22 Nov 2022) — citation correct.
- RDW Open Data: opendata.rdw.nl, Socrata SODA, no key, dataset Gekentekende_voertuigen
  **m9d7-ebf2**, owner personal data excluded. CONFIRMED (dev.socrata.com foundry). Accurate.
- Verdict: claims hold. "verified" confidence justified.

## BELGIUM — VERIFIED (solid)
- KBO/CBE open data free, registration required, SFTP via kbo-bce-webservice@economie.fgov.be.
  **Since 3 Nov 2025 complete files available DAILY** (was monthly) + daily delta, kept 31 days.
  CONFIRMED verbatim on economie.fgov.be. Very accurate (this is a recent change the agent
  got right).
- Minor URL nuance: agent's URL has ".../services-everyone/public-data-available-reuse/cbe-open-data";
  the official also resolves at ".../services-everyone/cbe-open-data". Both live; not an error.
- NBB CBSO web services: developer.cbso.nbb.be, XBRL/PDF/JSON, **JSON since 4 Apr 2022**,
  XBRL since 2007. CONFIRMED verbatim. Accurate.
- DIV vehicle registry: NO public open bulk; owner data NOT public; only Statbel/FPS aggregate
  parc stats. CONFIRMED (belgium.be, Statbel). Correct and appropriately cautious — this is the
  kind of claim that is usually wrong elsewhere; here it is right.
- Verdict: claims hold. "verified" justified.

## LUXEMBOURG — MOSTLY VERIFIED (likely; correctly hedged)
- RCS via LBR (lbr.lu): free basic search + free PDF document download; certified extracts fee.
  CONFIRMED. Accurate.
- "LBR open-data REST API could NOT be confirmed on official site -> treat as uncertain."
  THIS HEDGE IS CORRECT AND SHOULD STAY. An LBR API does exist (private-sector XML API,
  introduced Oct 2022 per i-Hub; ABBL confirms LBR introduced an API for RCS e-services), but
  there is NO confirmed FREE OPEN-DATA BULK REST endpoint with no auth for the full register.
  Third-party guides (Kyckr, Topograph, businessdataguide) assert an "open data REST API, no auth
  for basic reads" — but that is not corroborated by the official LBR site (JS-redirect, not
  machine-readable; could not independently confirm). Do not upgrade this claim to "verified."
- Annual accounts filed with RCS, publicly downloadable free; eCDF/PCN. CONFIRMED.
- RBE (UBO) access-restricted post-CJEU Nov 2022 + LU reform. CONFIRMED.
- SNCA vehicle dataset "Parc Automobile du Luxembourg" on data.public.lu: EXISTS, CC0, monthly,
  **latest snapshot 4 June 2026**, 224 files. CONFIRMED via WebFetch.
  NUANCE: dataset is described officially as "a snapshot of ALL the registered vehicles currently
  running in Luxembourg" — i.e. PER-VEHICLE records, not merely "technical/fleet aggregate" as the
  inventory phrases it. No per-owner data (correct). The "aggregate" framing slightly understates it.
- Verdict: claims hold with the hedge intact. "likely" confidence justified.

## FRANCE — VERIFIED with one URL correction (mostly-solid)
- SIRENE: free bulk on data.gouv.fr, 6 stock files + daily delta, **Parquet since June 2025**,
  **CSV discontinued 1 Jan 2027**. CONFIRMED verbatim. Accurate.
- API Sirene via **portail-api.insee.fr** (account+subscribe). CONFIRMED (old portal closed
  10 Sep 2025; new portal correct).
- API Recherche d'Entreprises: recherche-entreprises.api.gouv.fr, no auth, **7 req/s/IP**
  (also 30 req/s/ASN). CONFIRMED verbatim. Accurate.
- INPI RNE free API + SFTP bulk for dirigeants/actes/bilans; data.inpi.fr. CONFIRMED.
  CORRECTION: the inventory cites the actes/bilans URL as
  https://entreprise.api.gouv.fr/catalogue/inpi/rne/actes_bilans . That endpoint (API Entreprise)
  is **restricted to public administrations & local authorities** — NOT the public/reuser route.
  The FREE public route for reusers is **data.inpi.fr** (direct API + SFTP, technical identifiers).
  The data IS free; the cited URL points at the gated channel and is misleading for a scraping/
  enrichment use case.
- SME confidential accounts caveat (comptes confidentiels not all public). CONFIRMED — good catch.
- UBO (bénéficiaires effectifs in RNE) access narrowed post-CJEU; dirigeants bulk-free, full UBO
  gated. CONFIRMED.
- SIV: owner data NOT public; HistoVec free but only to current owner/seller; commercial
  plate->tech-spec APIs exist (no owner). CONFIRMED verbatim. Accurate.
- Verdict: claims hold; fix the actes/bilans URL to data.inpi.fr.

---

## HALLUCINATIONS: none found.
All named registries (KVK, RDW, KBO/CBE, NBB CBSO, LBR/RCS/RBE, SNCA, INSEE SIRENE, INPI RNE,
SIV/HistoVec) are real and described accurately. No invented APIs, no fake dataset IDs.
The one not-fully-confirmed item (LBR open-data REST API) was ALREADY flagged uncertain by the
author — that is correct behaviour, not a hallucination.

## MISSED SOURCES (minor, optional adds)
- NL: Open KvK / OpenKVK-style reconciliation + **BRIS / EBR** (European Business Register) is
  mentioned for NL but could be listed as a cross-border source for all four (Business Registers
  Interconnection System via e-justice.europa.eu).
- BE: **data.gov.be** federal portal and **Fedict/Smals lod-cbe + cbe-download** tooling (GitHub)
  for ready-made CBE bulk loaders.
- FR: **annuaire-entreprises.data.gouv.fr** (DINUM front-end over SIRENE+RNE) and the
  **API Avis de Situation SIRENE** are adjacent free resources not listed.
- LU: **RESA** (official electronic gazette, free, no auth) for company filings/notices is a real
  additional free source not explicitly listed.

## NET ASSESSMENT
High-quality inventory. The author was appropriately skeptical exactly where skepticism was
warranted (vehicle owner data in BE/FR; LU bulk API). Only one URL needs swapping (FR actes/bilans
-> data.inpi.fr) and two phrasings could be tightened (LU SNCA "aggregate" -> per-vehicle; keep LU
LBR API uncertain). Recommend: accept with the noted corrections.
