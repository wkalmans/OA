#!/usr/bin/env python3
"""
Pull osteoarthritis therapeutic trials from ClinicalTrials.gov.

Scope: industry-sponsored, interventional trials of drugs / biologics /
genetic therapies / combination products in osteoarthritis. Excludes
medical devices and surgical procedures.

Outputs:
  data/clinicaltrials_oa_trials_raw.json  - one record per trial
  data/oa_assets.csv                      - one row per unique asset
                                             (drug name + sponsor), aggregated
                                             across all trials it appears in
"""
import json
import re
import urllib.request
import urllib.parse
import csv
import time
from collections import defaultdict

# Control-arm / vehicle names that are not actual competitive assets.
NON_ASSET_PATTERN = re.compile(
    r"^\s*(placebo|vehicle|normal saline|saline|sham)\b", re.IGNORECASE
)

# Off-patent / generic molecule names (INN, lowercase) commonly used as
# active comparators or generic-formulation study drugs in OA trials. Trials
# testing these are kept, but bucketed separately from novel branded pipeline
# assets per project focus. Extend this list as new generics show up in the
# "review" bucket.
GENERIC_MOLECULES = {
    "acetaminophen", "paracetamol", "ibuprofen", "naproxen", "naproxen sodium",
    "diclofenac", "diclofenac sodium", "diclofenac potassium",
    "diclofenac epolamine", "indomethacin", "ketoprofen", "piroxicam",
    "nabumetone", "etodolac", "oxaprozin", "sulindac", "tolmetin",
    "meloxicam", "celecoxib", "etoricoxib", "aspirin", "acetylsalicylic acid",
    "tramadol", "duloxetine", "methylprednisolone", "methylprednisolone acetate",
    "triamcinolone", "triamcinolone acetonide", "betamethasone",
    "dexamethasone", "hydrocortisone", "prednisolone", "prednisone",
    "hyaluronic acid", "sodium hyaluronate", "glucosamine", "chondroitin",
    "glucosamine sulfate", "chondroitin sulfate", "capsaicin", "lidocaine",
    "morphine", "oxycodone", "codeine", "tapentadol", "gabapentin",
    "pregabalin", "collagenase", "amlodipine besylate", "famotidine",
    "esomeprazole magnesium", "misoprostol",
}

# Words/suffixes stripped when normalizing an intervention name for
# generic-molecule matching (dosage strengths, formulations, etc.).
_STRIP_PATTERN = re.compile(
    r"\b(\d+(\.\d+)?\s*(mg|mcg|g|%)\b|tablet(s)?|capsule(s)?|injection|"
    r"gel|cream|patch|solution|topical|oral|xr|er|extended release|"
    r"low[- ]dose|sodium|potassium|hydrochloride|hcl|sulfate|acetate)",
    re.IGNORECASE,
)


def normalize_name(name):
    n = _STRIP_PATTERN.sub(" ", name)
    n = re.sub(r"\s+", " ", n).strip().lower()
    return n


def is_generic_molecule(name):
    n = normalize_name(name)
    if n in GENERIC_MOLECULES:
        return True
    # combination products like "Naproxen and Esomeprazole" - generic if
    # every component is a known generic molecule
    parts = re.split(r"\s+and\s+|/|\+", n)
    if len(parts) > 1 and all(p.strip() in GENERIC_MOLECULES for p in parts if p.strip()):
        return True
    return False

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

FIELDS = [
    "NCTId", "BriefTitle", "Acronym", "OverallStatus", "WhyStopped",
    "Phase", "InterventionName", "InterventionType", "LeadSponsorName",
    "CollaboratorName", "Condition", "StudyType",
    "StartDate", "PrimaryCompletionDate", "CompletionDate",
    "StudyFirstPostDate", "LastUpdatePostDate",
]

QUERY_COND = "osteoarthritis"
FILTER_ADVANCED = (
    "AREA[LeadSponsorClass]INDUSTRY AND "
    "AREA[InterventionType](DRUG OR BIOLOGICAL OR GENETIC OR COMBINATION_PRODUCT)"
)


def fetch_all():
    studies = []
    params = {
        "query.cond": QUERY_COND,
        "filter.advanced": FILTER_ADVANCED,
        "fields": ",".join(FIELDS),
        "pageSize": "100",
    }
    page_token = None
    page_num = 0
    while True:
        if page_token:
            params["pageToken"] = page_token
        else:
            params.pop("pageToken", None)
        url = BASE_URL + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())
        studies.extend(data.get("studies", []))
        page_num += 1
        print(f"  page {page_num}: {len(data.get('studies', []))} studies "
              f"(total so far: {len(studies)})")
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.2)
    return studies


def get(d, *path):
    cur = d
    for p in path:
        if cur is None:
            return None
        cur = cur.get(p)
    return cur


def flatten_study(s):
    ps = s.get("protocolSection", {})
    idm = ps.get("identificationModule", {})
    sm = ps.get("statusModule", {})
    spm = ps.get("sponsorCollaboratorsModule", {})
    dm = ps.get("designModule", {})
    aim = ps.get("armsInterventionsModule", {})
    cm = ps.get("conditionsModule", {})

    interventions = aim.get("interventions", []) or []
    collaborators = spm.get("collaborators", []) or []

    return {
        "nct_id": idm.get("nctId"),
        "title": idm.get("briefTitle"),
        "acronym": idm.get("acronym"),
        "status": sm.get("overallStatus"),
        "why_stopped": sm.get("whyStopped"),
        "start_date": get(sm, "startDateStruct", "date"),
        "primary_completion_date": get(sm, "primaryCompletionDateStruct", "date"),
        "completion_date": get(sm, "completionDateStruct", "date"),
        "first_posted": get(sm, "studyFirstPostDateStruct", "date"),
        "last_updated": get(sm, "lastUpdatePostDateStruct", "date"),
        "phases": ",".join(dm.get("phases", []) or []),
        "study_type": dm.get("studyType"),
        "lead_sponsor": get(spm, "leadSponsor", "name"),
        "collaborators": ",".join(c.get("name", "") for c in collaborators),
        "conditions": ",".join(cm.get("conditions", []) or []),
        "interventions": [
            {"name": i.get("name"), "type": i.get("type")} for i in interventions
            if i.get("type") in ("DRUG", "BIOLOGICAL", "GENETIC", "COMBINATION_PRODUCT")
            and not NON_ASSET_PATTERN.match(i.get("name") or "")
        ],
    }


def load_marketed_brand_names():
    """Brand names from data/oa_marketed_drugs.csv, normalized, for matching
    CT.gov interventions that use a brand name directly (e.g. 'Zilretta')."""
    names = set()
    try:
        with open("data/oa_marketed_drugs.csv") as f:
            for row in csv.DictReader(f):
                brand = (row.get("brand_name") or "").strip().lower()
                if not brand:
                    continue
                norm = normalize_name(brand)
                # skip non-distinctive "brands" that are just the generic
                # molecule name (e.g. an NDA literally titled "Naproxen") -
                # those belong in the generic bucket, not branded-marketed.
                if norm in GENERIC_MOLECULES or brand in GENERIC_MOLECULES:
                    continue
                names.add(brand)
                names.add(norm)
    except FileNotFoundError:
        pass
    return names


def build_asset_table(trials):
    assets = defaultdict(lambda: {
        "trial_count": 0,
        "sponsors": set(),
        "phases": set(),
        "statuses": set(),
        "nct_ids": [],
        "earliest_start": None,
        "latest_update": None,
        "titles": [],
    })

    for t in trials:
        for interv in t["interventions"]:
            name = (interv["name"] or "").strip()
            if not name:
                continue
            key = name.lower()
            a = assets[key]
            a["asset_name"] = name
            a["trial_count"] += 1
            if t["lead_sponsor"]:
                a["sponsors"].add(t["lead_sponsor"])
            if t["phases"]:
                a["phases"].add(t["phases"])
            if t["status"]:
                a["statuses"].add(t["status"])
            a["nct_ids"].append(t["nct_id"])
            a["titles"].append(t["title"])
            if t["start_date"]:
                if not a["earliest_start"] or t["start_date"] < a["earliest_start"]:
                    a["earliest_start"] = t["start_date"]
            if t["last_updated"]:
                if not a["latest_update"] or t["last_updated"] > a["latest_update"]:
                    a["latest_update"] = t["last_updated"]

    return assets


def main():
    print("Fetching osteoarthritis therapeutic trials from ClinicalTrials.gov...")
    raw_studies = fetch_all()
    print(f"Total trials fetched: {len(raw_studies)}")

    trials = [flatten_study(s) for s in raw_studies]
    # keep only trials that actually have a drug/biologic/genetic/combo intervention
    trials = [t for t in trials if t["interventions"]]
    print(f"Trials with a therapeutic (drug/biologic/genetic/combo) intervention: {len(trials)}")

    with open("data/clinicaltrials_oa_trials_raw.json", "w") as f:
        json.dump(trials, f, indent=2)

    assets = build_asset_table(trials)
    print(f"Unique assets identified: {len(assets)}")

    marketed_brand_names = load_marketed_brand_names()

    pipeline_rows, marketed_rows, generic_rows = [], [], []
    for a in assets.values():
        name = a["asset_name"]
        row = {
            "asset_name": name,
            "sponsor(s)": "; ".join(sorted(a["sponsors"])),
            "trial_count": a["trial_count"],
            "phases_seen": "; ".join(sorted(a["phases"])),
            "statuses_seen": "; ".join(sorted(a["statuses"])),
            "earliest_trial_start": a["earliest_start"] or "",
            "most_recent_update": a["latest_update"] or "",
            "nct_ids": "; ".join(a["nct_ids"]),
        }
        if normalize_name(name) in marketed_brand_names or name.strip().lower() in marketed_brand_names:
            marketed_rows.append(row)
        elif is_generic_molecule(name):
            generic_rows.append(row)
        else:
            pipeline_rows.append(row)

    for rows in (pipeline_rows, marketed_rows, generic_rows):
        rows.sort(key=lambda r: (r["most_recent_update"] or ""), reverse=True)

    fieldnames = list(pipeline_rows[0].keys()) if pipeline_rows else [
        "asset_name", "sponsor(s)", "trial_count", "phases_seen",
        "statuses_seen", "earliest_trial_start", "most_recent_update", "nct_ids",
    ]

    def write_csv(path, rows):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {path} ({len(rows)} assets)")

    write_csv("data/oa_pipeline_branded_assets.csv", pipeline_rows)
    write_csv("data/oa_marketed_branded_in_trials.csv", marketed_rows)
    write_csv("data/oa_generic_reference.csv", generic_rows)

    print("Wrote data/clinicaltrials_oa_trials_raw.json")


if __name__ == "__main__":
    main()
