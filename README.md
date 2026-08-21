# OA Competitive Intelligence

A tracker for osteoarthritis (OA) therapeutics — what competitors are developing,
what's already on the market, and (longer-term) a record of what each company
said it would do versus what it actually did.

Scope: **drug and biologic therapeutics only** — no surgeries, medical devices,
or hyaluronic acid viscosupplements (regulated as devices, not drugs).

## What's in here so far

### `data/` — the asset lists (Phase 1)

Pulled from ClinicalTrials.gov (pipeline trials) and the FDA's drug label
database (marketed drugs), then sorted into three files:

| File | What it is |
|---|---|
| `oa_pipeline_branded_assets.csv` | Branded/investigational OA drugs currently in clinical development — the main list to watch |
| `oa_marketed_branded_in_trials.csv` | Already-FDA-approved branded OA drugs that are still showing up in new trials (e.g. new formulations, new populations) |
| `oa_generic_reference.csv` | Off-patent generic molecules (ibuprofen, celecoxib, etc.) used mostly as comparators — kept for completeness but deprioritized |
| `oa_marketed_drugs.csv` | Reference list of FDA-approved branded OA drugs (brand name, generic name, manufacturer, route) |
| `companies.csv` | Every company sponsoring an OA drug trial, ranked by how many assets they have — a starting point for deciding which competitors to actively track |
| `clinicaltrials_oa_trials_raw.json` | The full raw trial data behind the asset lists |

**These lists are a first draft, not a finished answer.** ClinicalTrials.gov
and FDA data are pulled by keyword/rule matching, so some entries may be
miscategorized or missing. Treat these CSVs as living documents — add,
correct, or delete rows as we confirm details.

**Name consolidation:** ClinicalTrials.gov records the same real-world drug
under many different literal strings across trials — dose variants
("Tanezumab 5 mg" vs "Tanezumab 10 mg"), sponsor code names before an INN is
assigned ("SM04690" vs "Lorecivivint"), formulation/route noise, and
placebo-comparator arms mislabeled with the drug's name. The pull script
merges these into one row per real asset and records what got merged in the
`name_variants_merged` column, so nothing is silently dropped — check that
column if a row's trial count looks off. Some free-text dosing-regimen
variants (e.g. "TPX-100 200mg, Once weekly for 4 weeks") aren't fully
merged and may still appear as separate rows; this is a known limitation of
rule-based matching, not a data error.

### `scripts/` — how the data gets refreshed

- `pull_clinicaltrials.py` — re-pulls the ClinicalTrials.gov pipeline data and rebuilds the three classified asset lists
- `pull_openfda_marketed.py` — re-pulls the FDA marketed-drug reference list (run this one first, since the trial pull uses it to spot brand names)

Re-run both any time to refresh with the latest trial data:
```
python3 scripts/pull_openfda_marketed.py
python3 scripts/pull_clinicaltrials.py
```

### `companies/` — per-company tracking (Phase 2, in progress)

One folder per shortlisted competitor (the 20 marked in `data/companies.csv`),
each containing:

- `company_profile.md` — ticker, SEC CIK, filer type, filing count
- `sec_filings.csv` — indexed 10-K / 10-Q / S-1 / 20-F / 40-F / 6-K / 8-K filings with direct links
- `press_releases/`, `decks/`, `filing_documents/`, `pipeline_updates/` — empty, for documents pulled next

Run `python3 scripts/pull_sec_filings.py` to (re)build these.

**Why 8-K/6-K filings matter here:** there's no separate SEC form for
"investor deck" or "JPM presentation" — companies typically furnish these
as *exhibits* to an 8-K (US filers) or 6-K (foreign filers), usually under
Item 7.01 (Reg FD disclosure). The filing index captures all of these; the
exhibit-level slide decks themselves still need to be pulled per filing.

**SEC coverage summary** (`data/sec_filer_summary.csv`):

| Filer type | Companies |
|---|---|
| US domestic (10-K/10-Q) | Eli Lilly, Pfizer, Regeneron, Pacira, Organon, J&J, Merck, Unity Biotechnology |
| Foreign private issuer (20-F/6-K) | Novartis, Novo Nordisk, GSK, AstraZeneca |
| Canadian MJDS (40-F/6-K) | Eupraxia |
| No SEC record (private) | Biosplice, Kolon TissueGene, Boehringer Ingelheim, Grünenthal, Centrexion, Genascence, Levicept |

Seven of the twenty shortlisted companies are privately held (or, like
Kolon TissueGene, only file exempt-offering notices) — no 10-K/10-Q/S-1
will ever exist for these. They still need tracking, just through press
releases and news rather than SEC filings.

### `companies/<name>/oa_profile.md` — the "said vs. did" record (Phase 3, first pass complete)

Every one of the 20 shortlisted companies now has an `oa_profile.md`: asset
overview, a dated timeline of what the company publicly said, a dated
timeline of what actually happened, an explicit discrepancies section, and
a full sourced reference list (SEC filings, PubMed, press releases, company
websites). The top 6 (Pfizer, Eli Lilly, Novartis, Pacira, Biosplice, Novo
Nordisk) got a deep-dive treatment reading actual SEC filing content; the
other 14 got a lighter web/press/PubMed pull.

**This first pass already surfaced a genuinely high "said vs. did" gap rate
across the field** — several programs framed in this project's own initial
research notes as "promising" or "active" turned out, on actual
verification, to have failed or been quietly discontinued:

- **Novartis LNA043** — assumed promising; actually failed its pivotal Phase 2b (ONWARDS) with no dose-response signal, discontinued 2024
- **Biosplice lorecivivint** — missed all three pivotal Phase 3 trials on the intent-to-treat population, yet an NDA was filed in Jan 2026 anyway, leaning on subgroup/extension data
- **Centrexion CNTX-4975** — both pivotal Phase 3 trials missed their individual primary endpoints (a pooled post-hoc analysis was positive); no confirmed path forward since 2023
- **Pfizer tanezumab** and **Regeneron fasinumab** — the entire anti-NGF drug class (also AstraZeneca's MEDI7352/MEDI-578, J&J's fulranumab) has now been discontinued industry-wide over joint-safety findings
- **GSK GSK3858279**, **AstraZeneca MEDI7352**, **Grünenthal RTX-GRT7039** — recently discontinued or inferred-discontinued (evidence-based, not company-confirmed in Grünenthal's case)
- **Kolon TissueGene TG-C** — pivotal trial ACTiVION-II missed both co-primary endpoints (July 2026), triggering a large stock drop; a second pivotal trial's readout (Oct 2026) is described by the company as make-or-break
- **Unity Biotechnology UBX0101** — failed Phase 2 (2020), company later delisted and formally dissolved (2025-2026)
- By contrast, **Eli Lilly retatrutide** (positive Phase 3 topline Dec 2025), **Genascence GNSC-001**, and **Levicept LEVI-04** (positive Phase 2, published in The Lancet) show real forward momentum

A data-quality bug was also found and fixed during this pass: a malformed
"Comparator: placebo / Duration of Treatment..." trial name was incorrectly
merging unrelated drugs (Novo Nordisk's semaglutide OA trial, a Merck
comparator trial, and a Nordic Bioscience calcitonin trial) into one row -
see `scripts/pull_clinicaltrials.py` for the fix.

## Next steps

1. Pull actual press-release/deck documents for the SEC-covered companies (start from the 8-K/6-K Item 7.01 filings already indexed)
2. Set a recurring cadence to re-check the open/unresolved items flagged in each profile (e.g. Kolon TissueGene's Oct 2026 readout, Genascence's Phase 2b/3 start, Eupraxia's partnership search)
3. Review `data/oa_pipeline_branded_assets.csv` for any remaining miscategorized entries
4. Decide on a standing format for updating `oa_profile.md` files over time as new news breaks (append vs. rewrite)
