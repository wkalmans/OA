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
    r'^\s*"*\s*(placebo|vehicle|normal saline|saline|sham|drug/placebo)\b',
    re.IGNORECASE,
)

# Trailing "or placebo" / "and placebo" qualifiers on an otherwise-real
# asset name (e.g. "UBX0101 or placebo") - strip the qualifier, keep the
# asset. Distinct from NON_ASSET_PATTERN / "-matching placebo", which mean
# the whole entry IS the placebo arm and should be dropped entirely.
_TRAILING_PLACEBO_PATTERN = re.compile(
    r"\s*[-\s](or|and|with)\s+placebo\s*$", re.IGNORECASE
)
_PURE_PLACEBO_QUALIFIER_PATTERN = re.compile(
    r"matching placebo|placebo\s*\(matched|placebo control", re.IGNORECASE
)

# Known cases where ClinicalTrials.gov data alone can't tell you a company
# code name and an INN refer to the same asset (no shared substring to key
# off of). Add to this as more are confirmed. Maps normalize_name(raw) ->
# normalize_name(canonical display name).
MANUAL_ALIASES = {
    "sm04690": "lorecivivint",
}

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

# Words/suffixes stripped when normalizing a name for matching/grouping:
# dosage strengths (leading or trailing), formulations, routes, salts.
# Note: '%' is punctuation (non-word), so a trailing \b never matches after
# it - that case is split out from the \b...\b(mg|mcg|g|ml) branch.
_STRIP_PATTERN = re.compile(
    r"(\d+(\.\d+)?\s*%|\b\d+(\.\d+)?\s*(mg|mcg|[μu]g|g|ml)\b|/\s*\d+(\.\d+)?\s*ml\b|\b\d+\s*x\b|"
    r"\btablet(s)?\b|\bcapsule(s)?\b|\binjection(s)?\b|\bsuspension\b|\bspray\b|\bmesylate\b|"
    r"\bgel\b|\bcream\b|\bpatch\b|\bsolution\b|\btopical\b|\boral\b|\bxr\b|\ber\b|extended release|"
    r"low[- ]dose|mid[- ]dose|high[- ]dose|\blow\b|\bmid\b|\bhigh\b|"
    r"\bsodium\b|\bpotassium\b|\bhydrochloride\b|\bhcl\b|\bsulfate\b|\bacetate\b|"
    r"\biv\b|\bsc\b|\bim\b|\bai\b|\bpfs\b|"
    r"\bcohort\s*[a-z0-9]+\b|\bcohort\b|\bpart\s+[a-z0-9]+\b|\bgroup\b|"
    r"\bdose\s+[ivx]+\b|\bfasted\b|\bfed\b|"
    r"\bonce\b|\btwice\b|\bbid\b|\btid\b|\bdaily\b|\bweekly\b|for\s+\d+\s+weeks?)",
    re.IGNORECASE,
)

_COMPARATOR_PREFIX_PATTERN = re.compile(r"^\s*comparators?\s*:?\s*", re.IGNORECASE)
_DURATION_SUFFIX_PATTERN = re.compile(r"\s*/\s*duration of treatment.*$", re.IGNORECASE)


def normalize_name(name):
    n = _COMPARATOR_PREFIX_PATTERN.sub("", name)
    n = _DURATION_SUFFIX_PATTERN.sub("", n)
    n = _STRIP_PATTERN.sub(" ", n)
    n = n.replace("/", " ").replace(",", " ")
    n = re.sub(r"\s+", " ", n).strip().lower().strip("- ")
    n = MANUAL_ALIASES.get(n, n)
    return n


def clean_asset_name(name):
    """Strip a trailing '... or placebo' qualifier from an otherwise-real
    asset name. Returns None if the whole name is just a placebo/control
    arm (caller should drop it)."""
    if _PURE_PLACEBO_QUALIFIER_PATTERN.search(name):
        return None
    cleaned = _TRAILING_PLACEBO_PATTERN.sub("", name).strip()
    return cleaned if cleaned else None


def is_generic_molecule(name):
    n = normalize_name(name)
    if n in GENERIC_MOLECULES:
        return True
    # combination products like "Naproxen and Esomeprazole" or
    # "Ibuprofen/Famotidine" - generic if every component is a known
    # generic molecule. Split the ORIGINAL name (normalize_name converts
    # '/' to a space, so splitting must happen first).
    parts = re.split(r"\s+and\s+|/|\+", name)
    if len(parts) > 1:
        norm_parts = [normalize_name(p) for p in parts if p.strip()]
        if norm_parts and all(p in GENERIC_MOLECULES for p in norm_parts):
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

    raw_interventions = aim.get("interventions", []) or []
    collaborators = spm.get("collaborators", []) or []

    interventions = []
    for i in raw_interventions:
        if i.get("type") not in ("DRUG", "BIOLOGICAL", "GENETIC", "COMBINATION_PRODUCT"):
            continue
        raw_name = (i.get("name") or "").strip()
        if not raw_name or NON_ASSET_PATTERN.match(raw_name):
            continue
        cleaned = clean_asset_name(raw_name)
        if not cleaned:
            continue
        interventions.append({"name": cleaned, "type": i.get("type")})

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
        "interventions": interventions,
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


_PAREN_PATTERN = re.compile(r"\(([^)]+)\)\s*$")


def strip_trailing_paren(name):
    return _PAREN_PATTERN.sub("", name).strip()


_SUFFIX_MERGE_PATTERN = re.compile(r"^(.{4,}?)-\d{1,3}$")


def canonicalize_asset_key(name, all_base_keys):
    """Resolve a display name to a grouping key. When a name has a trailing
    parenthetical (e.g. 'PF-04383119 (tanezumab)') and the parenthetical
    text is itself the base name of some OTHER intervention in this
    dataset, treat that as the same asset and key off the parenthetical
    (the shared name is the link). Otherwise a parenthetical is treated as
    a descriptive note, not an identifier, and is ignored for keying."""
    base_key = normalize_name(strip_trailing_paren(name))
    m = _PAREN_PATTERN.search(name)
    if m:
        paren_key = normalize_name(m.group(1))
        if paren_key in all_base_keys and paren_key != base_key:
            return paren_key
    return base_key


def merge_suffix_variants(groups):
    """Second pass: merge keys that differ only by a trailing '-NN' numeric
    suffix (e.g. 'cntx-4975-05' -> 'cntx-4975') into the shorter base key,
    when that base key also exists as its own group."""
    for key in list(groups.keys()):
        if key not in groups:
            continue
        m = _SUFFIX_MERGE_PATTERN.match(key)
        if not m:
            continue
        base = m.group(1)
        if base in groups and base != key:
            target, source = groups[base], groups[key]
            target["trial_count"] += source["trial_count"]
            target["sponsors"] |= source["sponsors"]
            target["phases"] |= source["phases"]
            target["statuses"] |= source["statuses"]
            target["nct_ids"] += source["nct_ids"]
            target["raw_names"] |= source["raw_names"]
            if source["earliest_start"] and (not target["earliest_start"] or source["earliest_start"] < target["earliest_start"]):
                target["earliest_start"] = source["earliest_start"]
            if source["latest_update"] and (not target["latest_update"] or source["latest_update"] > target["latest_update"]):
                target["latest_update"] = source["latest_update"]
            del groups[key]
    return groups


def pick_display_name(raw_names):
    """Prefer an INN-looking name (letters/spaces/hyphens only, mixed or
    lowercase case, no digits) over a sponsor code name (contains digits or
    is all-caps); among ties, prefer the shortest."""
    inn_like = [n for n in raw_names if re.match(r"^[A-Za-z][A-Za-z \-]*$", n) and not n.isupper()]
    pool = inn_like if inn_like else list(raw_names)
    return min(pool, key=len)


def build_asset_table(trials):
    # first pass: every cleaned intervention name's base (paren-stripped) key,
    # needed so canonicalize_asset_key can tell a real INN-link apart from a
    # merely descriptive parenthetical.
    all_base_keys = set()
    for t in trials:
        for interv in t["interventions"]:
            name = (interv["name"] or "").strip()
            if name:
                all_base_keys.add(normalize_name(strip_trailing_paren(name)))

    assets = defaultdict(lambda: {
        "trial_count": 0,
        "sponsors": set(),
        "phases": set(),
        "statuses": set(),
        "nct_ids": [],
        "raw_names": set(),
        "earliest_start": None,
        "latest_update": None,
    })

    for t in trials:
        for interv in t["interventions"]:
            name = (interv["name"] or "").strip()
            if not name:
                continue
            key = canonicalize_asset_key(name, all_base_keys)
            a = assets[key]
            a["raw_names"].add(name)
            a["trial_count"] += 1
            if t["lead_sponsor"]:
                a["sponsors"].add(t["lead_sponsor"])
            if t["phases"]:
                a["phases"].add(t["phases"])
            if t["status"]:
                a["statuses"].add(t["status"])
            a["nct_ids"].append(t["nct_id"])
            if t["start_date"]:
                if not a["earliest_start"] or t["start_date"] < a["earliest_start"]:
                    a["earliest_start"] = t["start_date"]
            if t["last_updated"]:
                if not a["latest_update"] or t["last_updated"] > a["latest_update"]:
                    a["latest_update"] = t["last_updated"]

    assets = merge_suffix_variants(assets)

    for a in assets.values():
        a["asset_name"] = pick_display_name(a["raw_names"])

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
        other_variants = sorted(v for v in a["raw_names"] if v != name)
        row = {
            "asset_name": name,
            "name_variants_merged": "; ".join(other_variants),
            "sponsor(s)": "; ".join(sorted(a["sponsors"])),
            "trial_count": a["trial_count"],
            "phases_seen": "; ".join(sorted(a["phases"])),
            "statuses_seen": "; ".join(sorted(a["statuses"])),
            "earliest_trial_start": a["earliest_start"] or "",
            "most_recent_update": a["latest_update"] or "",
            "nct_ids": "; ".join(a["nct_ids"]),
        }
        is_marketed = any(
            normalize_name(v) in marketed_brand_names or v.strip().lower() in marketed_brand_names
            for v in a["raw_names"]
        )
        is_generic = any(is_generic_molecule(v) for v in a["raw_names"])
        if is_marketed:
            marketed_rows.append(row)
        elif is_generic:
            generic_rows.append(row)
        else:
            pipeline_rows.append(row)

    for rows in (pipeline_rows, marketed_rows, generic_rows):
        rows.sort(key=lambda r: (r["most_recent_update"] or ""), reverse=True)

    fieldnames = [
        "asset_name", "name_variants_merged", "sponsor(s)", "trial_count",
        "phases_seen", "statuses_seen", "earliest_trial_start",
        "most_recent_update", "nct_ids",
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
