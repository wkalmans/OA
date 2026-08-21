#!/usr/bin/env python3
"""
Pull FDA-approved (NDA/BLA) branded drugs whose label indications mention
osteoarthritis, from openFDA's drug label database.

This captures prescription branded small-molecule / biologic drugs. It does
NOT capture: OTC-monograph products, intra-articular hyaluronic acid
viscosupplements (FDA-regulated as devices, out of scope per project focus),
or every branded product (openFDA's label index has gaps/older entries that
don't always resolve by brand-name lookup). Treat this as a strong first
draft — review and add to data/oa_marketed_drugs.csv by hand as needed.

Output: data/oa_marketed_drugs.csv
"""
import json
import csv
import urllib.request
import urllib.parse

BASE_URL = "https://api.fda.gov/drug/label.json"

# Known branded OA-indicated drugs that don't reliably resolve via the
# openFDA label API (OTC monograph, combination products, or indexing gaps).
# source="manual" so it's obvious these weren't auto-verified against openFDA.
MANUAL_SUPPLEMENT = [
    {"brand_name": "Voltaren Gel / Voltaren Arthritis", "generic_name": "DICLOFENAC SODIUM (TOPICAL GEL)",
     "application_number": "NDA022122 (Rx) / OTC monograph", "route": "TOPICAL",
     "pharm_class": "Nonsteroidal Anti-inflammatory Drug", "manufacturers": "GSK (OTC); various"},
    {"brand_name": "Pennsaid", "generic_name": "DICLOFENAC SODIUM (TOPICAL SOLUTION)",
     "application_number": "NDA204623", "route": "TOPICAL",
     "pharm_class": "Nonsteroidal Anti-inflammatory Drug", "manufacturers": "Mitsubishi Tanabe / Horizon Therapeutics"},
    {"brand_name": "Duexis", "generic_name": "IBUPROFEN AND FAMOTIDINE",
     "application_number": "NDA202770", "route": "ORAL",
     "pharm_class": "NSAID + H2 blocker combination", "manufacturers": "Horizon Therapeutics"},
    {"brand_name": "Vimovo", "generic_name": "NAPROXEN AND ESOMEPRAZOLE MAGNESIUM",
     "application_number": "NDA022511", "route": "ORAL",
     "pharm_class": "NSAID + PPI combination", "manufacturers": "Horizon Therapeutics / Kowa"},
    {"brand_name": "Consensi", "generic_name": "CELECOXIB AND AMLODIPINE BESYLATE",
     "application_number": "NDA210975", "route": "ORAL",
     "pharm_class": "NSAID + calcium channel blocker combination", "manufacturers": "Cadence / Kye Pharmaceuticals"},
    {"brand_name": "Feldene", "generic_name": "PIROXICAM",
     "application_number": "NDA018068", "route": "ORAL",
     "pharm_class": "Nonsteroidal Anti-inflammatory Drug", "manufacturers": "Pfizer (mostly genericized)"},
    {"brand_name": "Mobic", "generic_name": "MELOXICAM",
     "application_number": "NDA020938", "route": "ORAL",
     "pharm_class": "Nonsteroidal Anti-inflammatory Drug", "manufacturers": "Boehringer Ingelheim (mostly genericized)"},
    {"brand_name": "Cymbalta", "generic_name": "DULOXETINE HYDROCHLORIDE",
     "application_number": "NDA021427", "route": "ORAL",
     "pharm_class": "SNRI - approved for chronic musculoskeletal/OA pain", "manufacturers": "Eli Lilly (mostly genericized)"},
    {"brand_name": "Zorvolex", "generic_name": "DICLOFENAC (LOW-DOSE, SoluMatrix)",
     "application_number": "NDA204592", "route": "ORAL",
     "pharm_class": "Nonsteroidal Anti-inflammatory Drug", "manufacturers": "Iroko Pharmaceuticals"},
]


def fetch_nda_bla_oa_labels():
    params = {
        "search": 'indications_and_usage:"osteoarthritis" AND '
                  '(openfda.application_number:NDA* OR openfda.application_number:BLA*)',
        "limit": "99",
    }
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
    return data.get("results", [])


def build_rows():
    results = fetch_nda_bla_oa_labels()
    by_app = {}
    for r in results:
        of = r.get("openfda", {})
        app = (of.get("application_number") or [None])[0]
        if not app:
            continue
        brand = (of.get("brand_name") or [None])[0]
        generic = (of.get("generic_name") or [None])[0]
        mfr = (of.get("manufacturer_name") or [None])[0]
        route = (of.get("route") or [None])[0]
        pharm = of.get("pharm_class_epc") or []
        entry = by_app.setdefault(app, {
            "brands": set(), "generics": set(), "mfrs": set(),
            "route": route, "pharm": set(pharm),
        })
        if brand:
            entry["brands"].add(brand)
        if generic:
            entry["generics"].add(generic)
        if mfr:
            entry["mfrs"].add(mfr)

    rows = []
    for app, e in sorted(by_app.items()):
        # prefer a brand name that isn't just the generic name re-cased
        generics_upper = {g.upper() for g in e["generics"]}
        brand_candidates = [b for b in e["brands"] if b.upper() not in generics_upper]
        brand = sorted(brand_candidates)[0] if brand_candidates else sorted(e["brands"])[0] if e["brands"] else ""
        rows.append({
            "brand_name": brand,
            "generic_name": "; ".join(sorted(e["generics"])),
            "application_number": app,
            "route": e["route"] or "",
            "pharm_class": "; ".join(sorted(e["pharm"])),
            "manufacturers": "; ".join(sorted(e["mfrs"])),
            "source": "openFDA",
        })

    for m in MANUAL_SUPPLEMENT:
        m = dict(m)
        m["source"] = "manual"
        rows.append(m)

    return rows


def main():
    rows = build_rows()
    fieldnames = ["brand_name", "generic_name", "application_number", "route",
                  "pharm_class", "manufacturers", "source"]
    with open("data/oa_marketed_drugs.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"Wrote data/oa_marketed_drugs.csv ({len(rows)} branded marketed drugs)")


if __name__ == "__main__":
    main()
