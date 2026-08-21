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

### `sources/` and `companies/` — where future documents will live (Phase 2, not yet populated)

Folders are set up to hold the documents the full competitive intelligence
agent will gather per company/asset:

- `sources/press_releases/`
- `sources/investor_decks/` (corporate & investor day decks)
- `sources/sec_filings/` (10-K, 10-Q, S-1)
- `sources/investor_days/`
- `sources/jpm_healthcare_conference/`
- `sources/pipeline_updates/`
- `companies/` — will hold a per-company folder once we've prioritized which competitors to track closely

## Next steps

1. Review `data/companies.csv` and mark which competitors matter most (`track_priority` column)
2. Review `data/oa_pipeline_branded_assets.csv` for miscategorized entries
3. Start pulling source documents (press releases, filings, decks) for the prioritized companies
4. Build the "said vs. did" longitudinal tracking record
