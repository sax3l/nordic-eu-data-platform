# Adversarial Verification — Southern Europe Data Sources (Italy, Spain, Portugal)

Date: 2026-06-24. Verifier: independent agent. Method: WebSearch + WebFetch against primary/official sources.

## Overall verdict: MOSTLY-SOLID

The inventory is unusually accurate for this class of document. The high-risk claims (UBO
suspension, vehicle-registry openness, free APIs) all hold up under independent checking. No
hallucinated registries found. A handful of small numeric overstatements and one understated
free dataset are the only real defects.

---

## ITALY — verified, minor NER overstatement

| Claim | Status | Evidence |
|---|---|---|
| Registro Imprese / InfoCamere / Chambers of Commerce | CONFIRMED | Official; ABDO + registroimprese.it live |
| Free search fields = name/office/PEC/main activity/status | CONFIRMED EXACTLY | registroimprese.it free profile returns exactly these (name, registered office, ATECO main activity, PEC, status); directors/shareholders/financials are NOT in free tier |
| EN mirror italianbusinessregister.it/en | CONFIRMED | Live, official InfoCamere mirror |
| Telemaco + ABDO (accessoallebanchedati.registroimprese.it) for paid/bulk | CONFIRMED | ABDO page live; InfoCamere data-access platform (directors, shareholdings, balances). Note: ABDO is broader than just "estrazione elenchi" but characterization is fair |
| OpenCorporates register #120 = Italy | CONFIRMED | Maps to Italian Business Register, jurisdiction Italy |
| UBO (Titolari Effettivi) public access SUSPENDED; Council of State 2024; CJEU referral; D.Lgs 210/2025 in force 2026-01-09; "relevant and differentiated legal interest" tiered model | CONFIRMED — all specifics accurate | Council of State suspended May + Oct 2024, referred to CJEU; D.Lgs 210/2025 (31 Dec 2025) in force 9 Jan 2026, replaced open access with legal-interest model. This is the single most-likely-to-be-wrong claim in the doc and it is correct. |
| INI-PEC national PEC index, bulk-searchable | MOSTLY CONFIRMED | inipec.gov.it consultable without auth for individual lookups; TRUE bulk is via SPCoop/application-cooperation for public administrations, not the open web portal. "bulk-searchable by company/professional" is mildly optimistic for ordinary users but the bulk channel exists. |
| ACI PRA per-plate visura PAID (Visurenet) | CONFIRMED | ACI/PRA per-plate is paid |
| ACI Open Data (LOD level 5, CC-BY 4.0) + Annuario Statistico | CONFIRMED | lod.aci.it; CC-BY 4.0; level-5 LOD with La Sapienza/Okkam |
| MIT 'Parco Circolante dei Veicoli' open per region/municipality | CONFIRMED | dati.mit.gov.it dataset live, open format |
| No per-owner data in open vehicle sets (owner stays paid via PRA) | CONFIRMED | Correct |
| spacy/it_core_news_lg ~0.91 NER F | **WRONG (overstated)** | HF model card reports ents_f = **0.884** (~0.88), not ~0.91 |

---

## SPAIN — verified, one understated free dataset

| Claim | Status | Evidence |
|---|---|---|
| Registro Mercantil Central + 52 provincial + CORPME; gazette = BORME | CONFIRMED | Correct structure |
| BORME open-data API: GET https://www.boe.es/datosabiertos/api/borme/sumario/{YYYYMMDD}, XML/JSON, free, no key | CONFIRMED EXACTLY | Official docs confirm endpoint `/datosabiertos/api/borme/sumario/{fecha}` (aaaammdd), returns application/xml AND application/json, public/no auth. Endpoint format in doc is exact. |
| BORME free legal edition since 2009; datos.gob.es catalogued | CONFIRMED | datos.gob.es ea0040819 dataset exists |
| Per-company notes via sede.registradores.org < EUR 5 | PLAUSIBLE/CONFIRMED-ish | sede mercantil "Publicidad Mercantil" exists and is low-cost paid; exact <EUR5 not independently price-checked but consistent with known fees |
| opendata.registradores.org WAF-protected | PARTIALLY MISLEADING | Portal is live and **offers FREE downloadable microdata** (company incorporations 2011-present, closures, account filings 2004-present, registered-office relocations, insolvency rulings). Doc frames it primarily as "WAF-protected, avoid via bots" and understates that it is a genuine FREE open dataset. WAF claim itself is plausible; the omission of its value as a free incorporations/closures feed is the gap. |
| New annual-accounts models 26 May 2025 (Law 11/2023) | CONFIRMED EXACTLY | BOE Resolutions of 26 May 2025 (BOE-A-2025-11004 / 11005), published 3 June 2025; IRUS code + CNAE 2025; mandatory from 3 June 2025 |
| UBO 'Consulta de Titularidades Reales' PAID/access-controlled | CONFIRMED | CORPME service, not open bulk |
| DGT 'Microdatos de parque de vehiculos (mensual)', anonymised, no owner | CONFIRMED | Live at dgt.es/dgt-en-cifras; vehicle type/fuel/reg year/displacement, anonymised |
| MATRABA tightened 2025-02-01 (no full chassis, legitimate-interest request) | CONFIRMED EXACTLY | From 1 Feb 2025 MATRABA files no longer contain full chassis info; chassis requires legitimate-interest form |
| Owner-level lookup NOT open (legitimate-interest gated) | CONFIRMED | Correct |
| spacy/es_core_news_lg ~0.90 NER F | CONFIRMED | HF reports ents_f = 0.897 (~0.90). Accurate. |

Note: doc gave OpenCorporates register numbers for IT (#120) and PT (#208) but NOT for Spain
(register #58). Minor inconsistency, not an error.

---

## PORTUGAL — verified, one shareholder-availability nuance

| Claim | Status | Evidence |
|---|---|---|
| Registo Comercial / IRN / Conservatorias; NIPC keyed; gov.pt/Empresa Online | CONFIRMED | Correct |
| Free MJ Publications search at https://publicacoes.mj.pt/Pesquisa.aspx by name or NIF/NIPC | CONFIRMED EXACTLY | Live, free, no registration; search by NIF/NIPC, firma, sede |
| Returns Date/NIF/Entity/Municipality/Activity HTML, no full address, not bulk-downloadable | MOSTLY CONFIRMED | Free, event-based, not a dump. BUT: the MJ notices DO surface shareholders (socios in constitution + capital-change acts) and directors — more than the doc's "events only / reconstruct shareholders where available" implies. Shareholder data is more retrievable from the free layer than the doc credits. |
| DRE gazette open-data feed | PLAUSIBLE | dre.pt is the official gazette; open-data feed exists. Not deeply re-verified but consistent. |
| OpenCorporates register #208 = Portugal | CONFIRMED | Maps to Portugal (Portal da Empresa) |
| RCBE (beneficial owner) NOT open bulk, access-controlled | CONFIRMED (consistent) | IRN-run, gated |
| IES single annual filing (tax+accounting+statistical), DL 8/2007, due 15th day of 7th month | CONFIRMED | IES is the single electronic annual submission; deadline framing standard |
| No free bulk IES portal; per-company via Racius / Informa | CONFIRMED | Correct |
| Racius ~960k companies | SLIGHTLY UNDERSTATED | Racius markets "more than 1 million" companies (active+closed+insolvent); ~960k is a plausible *active* count but Racius' own headline is 1M+. The doc's "~960k+ active" qualifier keeps it defensible. |
| BPLIM (bplim.bportugal.pt/datasets) firm-level microdata to accredited researchers | CONFIRMED EXACTLY | Banco de Portugal Microdata Research Lab; Central Balance Sheet based on IES (2006+); on-site/remote/remote-execution access for vetted researchers |

---

## Hallucinations / fabricated registries

NONE found. Every named registry, portal, API endpoint, and legal instrument resolves to a real,
live source. This is notably clean.

## Net assessment

- 0 hallucinated registries.
- 1 clear numeric error (Italy it_core_news_lg NER F: 0.91 -> 0.884).
- 2 soft overstatements (Racius 960k vs 1M+; INI-PEC "bulk-searchable" for ordinary users).
- 1 understated free dataset (Spain opendata.registradores.org free incorporations/closures
  microdata is framed mainly as a WAF obstacle).
- 1 nuance (Portugal MJ free layer exposes shareholders/directors more than the doc credits).

All confidence:"verified" labels in the source are largely justified.
