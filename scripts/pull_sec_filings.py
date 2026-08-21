#!/usr/bin/env python3
"""
Build a per-company SEC filings index for the shortlisted OA competitors
in data/companies.csv (rows with track_priority set).

For each company, resolves an SEC EDGAR CIK (via the ticker file, with a
manual override table for companies that don't resolve cleanly - e.g.
foreign issuers, delisted companies) and pulls its recent 10-K/10-Q/S-1/
20-F/6-K/8-K filing history. 8-Ks and 6-Ks are included in full because
companies frequently furnish press releases, investor-day slides, and JPM
Healthcare Conference presentations as exhibits to these rather than as
their own filing type - there's no separate SEC form for "investor deck."

Privately-held companies (no SEC filer registration) are recorded as such
in company_profile.md rather than silently skipped.

Output per company: companies/<slug>/sec_filings.csv, company_profile.md
"""
import csv
import json
import re
import time
import urllib.request
import urllib.error

HEADERS = {"User-Agent": "OA Competitive Intel research@lontraventures.com"}

RELEVANT_FORMS = {
    "10-K", "10-Q", "S-1", "S-1/A", "20-F", "6-K", "8-K", "424B4", "424B5",
    "40-F", "F-10", "F-10/A",  # Canadian MJDS equivalents of S-1/annual report
}

# name -> (folder slug, EDGAR search string or None if known-private,
#          manual CIK override or None to resolve via ticker file)
COMPANIES = [
    ("Eli Lilly and Company", "eli_lilly", "eli lilly", None),
    ("Pfizer", "pfizer", "pfizer", None),
    ("Novartis Pharmaceuticals", "novartis", "novartis", None),
    ("Novo Nordisk A/S", "novo_nordisk", "novo nordisk", None),
    ("Regeneron Pharmaceuticals", "regeneron", "regeneron", None),
    ("Pacira Pharmaceuticals, Inc", "pacira", "pacira", None),
    ("Biosplice Therapeutics, Inc.", "biosplice", None, None),  # private
    ("Kolon TissueGene, Inc.", "kolon_tissuegene", None, None),  # Reg D filer only, not a reporting company
    ("Organon and Co", "organon", "organon", None),
    ("Johnson & Johnson Pharmaceutical Research & Development, L.L.C.", "jnj", "johnson & johnson", None),
    ("GlaxoSmithKline", "gsk", "gsk plc", None),
    ("AstraZeneca", "astrazeneca", "astrazeneca", None),
    ("Boehringer Ingelheim", "boehringer_ingelheim", None, None),  # private
    ("Grünenthal GmbH", "grunenthal", None, None),  # private
    ("Centrexion Therapeutics", "centrexion", None, None),  # private
    ("Eupraxia Pharmaceuticals Inc.", "eupraxia", "eupraxia", None),
    ("Genascence Corporation", "genascence", None, None),  # private
    ("Levicept", "levicept", None, None),  # private (UK)
    ("Unity Biotechnology, Inc.", "unity_biotechnology", None, 1463361),
    ("Merck Sharp & Dohme LLC", "merck_msd", "merck & co", None),
]


def load_ticker_file():
    with open("/tmp/company_tickers.json") as f:
        return list(json.load(f).values())


def resolve_cik(search_str, ticker_entries):
    if not search_str:
        return None, None, None
    ql = search_str.lower()
    matches = [e for e in ticker_entries if ql in e["title"].lower()]
    if not matches:
        return None, None, None
    m = matches[0]
    return m["cik_str"], m["ticker"], m["title"]


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_filings(cik):
    cik10 = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik10}.json"
    data = fetch_json(url)
    recent = data.get("filings", {}).get("recent", {})
    filings = []
    n = len(recent.get("form", []))
    for i in range(n):
        form = recent["form"][i]
        if form not in RELEVANT_FORMS:
            continue
        accession = recent["accessionNumber"][i]
        primary_doc = recent["primaryDocument"][i]
        accession_nodash = accession.replace("-", "")
        filings.append({
            "form": form,
            "filing_date": recent["filingDate"][i],
            "report_date": recent.get("reportDate", [""] * n)[i],
            "items": recent.get("items", [""] * n)[i],
            "accession_number": accession,
            "primary_doc_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{primary_doc}",
            "filing_index_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/",
        })
    return data, filings


def slugify_ok(s):
    return re.sub(r"[^a-z0-9_]", "", s.lower().replace(" ", "_"))


def main():
    ticker_entries = load_ticker_file()
    profile_lines_summary = []

    for name, slug, search_str, manual_cik in COMPANIES:
        folder = f"companies/{slug}"
        import os
        os.makedirs(folder, exist_ok=True)
        for sub in ("press_releases", "decks", "filing_documents", "pipeline_updates"):
            os.makedirs(f"{folder}/{sub}", exist_ok=True)
            open(f"{folder}/{sub}/.gitkeep", "a").close()

        if manual_cik:
            cik, ticker, edgar_title = manual_cik, None, name
        else:
            cik, ticker, edgar_title = resolve_cik(search_str, ticker_entries)

        if not cik:
            print(f"{name}: no SEC filer found (likely private)")
            with open(f"{folder}/company_profile.md", "w") as f:
                f.write(f"# {name}\n\n")
                f.write("**SEC filer status:** No SEC registration found — appears to be "
                        "privately held (or files exempt-offering forms only, e.g. Form D). "
                        "Track via press releases and news instead of SEC filings.\n")
            profile_lines_summary.append((name, "private / no SEC record", "-", 0))
            continue

        try:
            company_data, filings = get_filings(cik)
        except urllib.error.HTTPError as e:
            print(f"{name}: SEC lookup failed ({e})")
            profile_lines_summary.append((name, "lookup failed", "-", 0))
            continue

        filer_forms = set(f["form"] for f in filings)
        if "10-K" in filer_forms:
            filer_type = "US domestic filer (10-K/10-Q)"
        elif "20-F" in filer_forms:
            filer_type = "Foreign private issuer (20-F/6-K)"
        elif "40-F" in filer_forms:
            filer_type = "Canadian MJDS filer (40-F/6-K)"
        else:
            filer_type = "SEC filer, no annual report in recent window"

        filings.sort(key=lambda f: f["filing_date"], reverse=True)

        with open(f"{folder}/sec_filings.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "form", "filing_date", "report_date", "items",
                "accession_number", "primary_doc_url", "filing_index_url",
            ])
            writer.writeheader()
            writer.writerows(filings)

        with open(f"{folder}/company_profile.md", "w") as f:
            f.write(f"# {name}\n\n")
            f.write(f"**Ticker:** {ticker or 'n/a'}  \n")
            f.write(f"**SEC CIK:** {cik}  \n")
            f.write(f"**EDGAR registrant name:** {edgar_title}  \n")
            f.write(f"**Filer type:** {filer_type}  \n")
            f.write(f"**Filings indexed:** {len(filings)} (see sec_filings.csv)\n\n")
            f.write("8-K / 6-K filings are included because companies commonly furnish "
                    "press releases, investor-day slides, and JPM Healthcare Conference "
                    "presentations as exhibits to these rather than filing them separately - "
                    "check `items` for the type (e.g. Item 7.01 = Reg FD disclosure, often a "
                    "press release or slide deck).\n")

        print(f"{name}: CIK {cik} ({ticker}), {filer_type}, {len(filings)} filings indexed")
        profile_lines_summary.append((name, filer_type, ticker or "-", len(filings)))
        time.sleep(0.15)

    with open("data/sec_filer_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["company_name", "filer_type", "ticker", "filings_indexed"])
        writer.writerows(profile_lines_summary)
    print("\nWrote data/sec_filer_summary.csv")


if __name__ == "__main__":
    main()
