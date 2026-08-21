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

## Next steps

1. Pull actual press releases / investor decks for the SEC-covered companies (start from the 8-K/6-K Item 7.01 filings)
2. Set up news/press-release tracking for the 7 private companies (no SEC filings to lean on)
3. Review `data/oa_pipeline_branded_assets.csv` for any remaining miscategorized entries
4. Build the "said vs. did" longitudinal tracking record
