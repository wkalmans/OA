# Merck & Co. / Merck Sharp & Dohme (MSD) — Osteoarthritis Pipeline Profile

*Light-touch pull, compiled 2026-08-21. Sources: company website/pipeline PDF, press releases, ClinicalTrials.gov API, PubMed. Not a deep-dive SEC review.*

## Bottom line

Merck has **no active osteoarthritis drug pipeline today**. Its OA-relevant history is almost entirely historical: **rofecoxib (Vioxx)**, one of the most consequential drug-safety stories in modern pharma, and **odanacatib**, a cathepsin K inhibitor developed for osteoporosis (with some OA-adjacent bone/cartilage biology interest) that was killed in 2016 over stroke risk. The "semaglutide + Merck Sharp & Dohme" trial record flagged in our data turns out to be a **data-merging artifact in this project's own pull script**, not a real Merck program — details below. Merck's current pipeline PDF (immunology, cardiovascular, endocrinology, oncology, neuroscience, ophthalmology, respiratory, antiviral, vaccines) lists no osteoarthritis or musculoskeletal-cartilage program. [Merck pipeline page](https://www.merck.com/research/product-pipeline/)

## Asset Overview

### MK0966 / Rofecoxib (Vioxx) — historical case study
- A selective COX-2 inhibitor NSAID, approved by the FDA on May 20, 1999 for osteoarthritis pain and inflammation (later also rheumatoid arthritis, acute pain, migraine). Marketed as **Vioxx**. [NEJM: "Failing the Public Health — Rofecoxib, Merck, and the FDA"](https://www.nejm.org/doi/full/10.1056/NEJMp048286)
- Vioxx's selling point over older NSAIDs (ibuprofen, naproxen) was a lower rate of GI ulcers/bleeding, since it spared COX-1. It became a blockbuster, reaching roughly 80 million patients treated worldwide and ~$2.5 billion in 2003 sales at peak. [NEJM](https://www.nejm.org/doi/full/10.1056/NEJMp048286)
- **Historical arc:** Cardiovascular risk signals emerged from Merck's own VIGOR trial (comparing rofecoxib to naproxen) as early as 2000, but the company continued marketing while disputing the interpretation. The APPROVe trial — a long-term colorectal-polyp-prevention study, not an OA trial — was stopped roughly two months early in September 2004 after data showed rofecoxib users had roughly double the risk of heart attack/stroke versus placebo when used continuously for 18+ months. Merck voluntarily withdrew Vioxx from the global market on **September 30, 2004**. Subsequent analysis estimated the drug had caused an estimated 88,000–140,000 cases of serious heart disease in the US, and litigation/settlement costs ran into the billions. It remains a textbook case study in post-market drug safety and regulatory failure. [NEJM](https://www.nejm.org/doi/full/10.1056/NEJMp048286); [EMA statement](https://www.ema.europa.eu/en/news/european-medicines-agency-statement-following-withdrawal-vioxx-rofecoxib)

### MK0822 / Odanacatib — verified, developed primarily for osteoporosis
- Confirmed: odanacatib (MK-0822) is a selective, reversible inhibitor of cathepsin K, the collagenase osteoclasts use to break down bone matrix during resorption. It was developed primarily as an **osteoporosis** drug (to reduce fracture risk), not a primary OA program. [PubMed 19943223](https://pubmed.ncbi.nlm.nih.gov/19943223/); [Merck.com program update](https://www.merck.com/news/merck-provides-update-on-odanacatib-development-program/)
- OA connection: cathepsin K biology (cartilage/bone matrix turnover) is scientifically relevant to OA joint degeneration, which is why cathepsin K inhibitors (including GSK's relacatib, see the separate GSK profile) were explored across both osteoporosis and OA/joint-disease research — but odanacatib's own pivotal program (the LOFT trial, >16,700 postmenopausal women) was an osteoporosis fracture-outcomes trial, not an OA efficacy trial. No dedicated Merck Phase 2/3 OA trial for odanacatib was found in this pull.
- **Confirmed discontinued in 2016**: Merck halted the program after its Phase 3 LOFT extension data showed an increased risk of stroke (and irregular heart rhythm/atrial fibrillation) in patients on odanacatib versus placebo. Merck announced it would not file for regulatory approval anywhere. [Merck.com press update](https://www.merck.com/news/merck-provides-update-on-odanacatib-development-program/); [Pharmacy Times](https://www.pharmacytimes.com/view/merck-discontinues-development-of-osteoporosis-drug-due-to-stroke-risk); [Nature Reviews Drug Discovery](https://www.nature.com/articles/nrd.2016.207)

### The "semaglutide + Merck Sharp & Dohme" trial record — investigated and resolved
This was flagged as puzzling because semaglutide is Novo Nordisk's drug (Ozempic/Wegovy/Rybelsus), not Merck's. **Root cause found: this is a data-merging error in this project's own ClinicalTrials.gov pull/consolidation script, not a real Merck program, licensing deal, or investigator trial.**

Tracing the row in `data/oa_pipeline_branded_assets.csv` back to its source NCT numbers (NCT00140894, NCT05064735, NCT00704847) via the ClinicalTrials.gov API shows it is actually **three unrelated trials that got incorrectly merged into a single "asset" row**, apparently because the pull script's name-matching logic collided on similar-looking placebo-arm labels:

| NCT ID | Actual trial | Actual sponsor | Actual drug/condition |
|---|---|---|---|
| NCT00140894 | "A Study of Rofecoxib in Familial Adenomatous Polyposis (FAP)" (TERMINATED) | **Merck Sharp & Dohme LLC** | This is a **rofecoxib** trial in colon-polyp patients (FAP), not an OA trial and not semaglutide at all. This is where the "Merck Sharp & Dohme LLC" sponsor name in the merged row actually comes from. |
| NCT05064735 | "Research Study Looking at How Well Semaglutide Works in People Suffering From Obesity and Knee Osteoarthritis" (the real STEP 9 trial, COMPLETED) | **Novo Nordisk A/S** | This is the genuine semaglutide + knee OA trial — legitimate, published in NEJM (see literature below) — but it has nothing to do with Merck. |
| NCT00704847 | "Efficacy and Safety of Oral Salmon Calcitonin in Patients With Knee Osteoarthritis (OA 2 Study)" (TERMINATED) | Nordic Bioscience A/S (collaborator: Novartis) | An unrelated oral salmon calcitonin knee-OA trial, also not Merck or semaglutide. |

In short: the row's combined sponsor list ("Merck Sharp & Dohme LLC; Nordic Bioscience A/S; Novo Nordisk A/S") and combined drug/arm labels are an artifact of three separate, unrelated trials being merged under one row by the pull script — not evidence of any real Merck–Novo Nordisk collaboration, a Merck-sponsored semaglutide trial, or Merck testing semaglutide as a comparator. **Recommendation: fix the consolidation logic in `scripts/pull_clinicaltrials.py` so it doesn't merge trials across different lead sponsors/drugs based on superficial arm-label text matches, and split this row into its three real, unrelated trials.** Verified directly via the ClinicalTrials.gov API on each NCT ID individually (see Sources).

## Current Status (as of most recent data found)

| Asset | Status | Source |
|---|---|---|
| Rofecoxib (Vioxx) | **Withdrawn from market worldwide since Sept 30, 2004.** Never returned; historical/legal case study only. | [EMA](https://www.ema.europa.eu/en/news/european-medicines-agency-statement-following-withdrawal-vioxx-rofecoxib) |
| Odanacatib | **Discontinued globally in 2016**, no regulatory filings anywhere; program fully closed. | [Merck.com](https://www.merck.com/news/merck-provides-update-on-odanacatib-development-program/) |
| "Semaglutide (Merck-sponsored)" | **Not a real Merck asset** — data artifact, see investigation above. No action needed other than correcting the dataset. | This pull, cross-checked against ClinicalTrials.gov API |

**Company-wide:** Merck's current pipeline document (checked live) covers antiviral, cardiovascular, endocrinology, immunology (including rheumatoid arthritis and psoriatic arthritis — inflammatory autoimmune joint disease, not degenerative OA), neuroscience, oncology, ophthalmology, respiratory, and vaccines. No osteoarthritis, cartilage, or degenerative joint-disease program appears. [Merck pipeline page](https://www.merck.com/research/product-pipeline/); [Q1 2026 pipeline PDF](https://www.merck.com/wp-content/uploads/sites/124/2026/02/Public-Pipeline-1Q2026-Merck.pdf)

## Recent News

- **Sept 30, 2004** — Merck announces voluntary worldwide withdrawal of Vioxx (rofecoxib) after the APPROVe trial showed doubled cardiovascular risk with long-term use; the single most consequential event in this drug's history. [EMA statement](https://www.ema.europa.eu/en/news/european-medicines-agency-statement-following-withdrawal-vioxx-rofecoxib)
- **2016** — Merck discontinues odanacatib development after Phase 3 LOFT data show elevated stroke risk; company states it will not seek approval in any market. [Merck.com](https://www.merck.com/news/merck-provides-update-on-odanacatib-development-program/); [Nature Reviews Drug Discovery](https://www.nature.com/articles/nrd.2016.207)
- No dated Merck press release or pipeline update in the last 2 years mentions any new osteoarthritis program; Merck's recent news flow (checked via merck.com/news) is concentrated on oncology (ASCO 2026), cardio-pulmonary (ACC.26), and its "One Pipeline" strategy, none of which reference OA. [Merck.com stories](https://www.merck.com/stories/what-is-one-pipeline/)

## Key Scientific Literature

- Nussmeier NA, et al. / VIGOR and APPROVe trial literature — for the historical cardiovascular safety signal, see: "Failing the Public Health — Rofecoxib, Merck, and the FDA," *N Engl J Med* 2004. [Full text](https://www.nejm.org/doi/full/10.1056/NEJMp048286) (perspective piece, not a primary PubMed-ID'd trial report, but the standard citation for the regulatory history)
- Rofecoxib has 327 PubMed results tagged with osteoarthritis (searched "rofecoxib AND osteoarthritis" on PubMed) — far too many for this light pull to individually vet; representative recent ones include a 2026 real-world pharmacovigilance study on NSAID adverse events in OA (PMID [41656471](https://pubmed.ncbi.nlm.nih.gov/41656471/)) and a 2022 network meta-analysis of NSAID cardiorenal safety in arthritis (PMID [36660678](https://pubmed.ncbi.nlm.nih.gov/36660678/)), both of which still reference rofecoxib as the classic cautionary comparator two decades after withdrawal.
- Yamada S, Ochi Y, et al. "Cathepsin K: The Action in and Beyond Bone." *Front Cell Dev Biol.* 2020. PMID: [32582709](https://pubmed.ncbi.nlm.nih.gov/32582709/) — reviews odanacatib's mechanism and bone/cartilage biology.
- "Design, synthesis and biological evaluation of inhibitors of cathepsin K on dedifferentiated chondrocytes." *Bioorg Med Chem.* 2019 Mar 15. PMID: [30773420](https://pubmed.ncbi.nlm.nih.gov/30773420/) — cathepsin K inhibition specifically in cartilage/chondrocyte context, relevant to why odanacatib's target class was of OA interest even though odanacatib itself was an osteoporosis drug.
- For context on the *actual* semaglutide-OA science (which is Novo Nordisk's, not Merck's): Bliddal H, et al. "Once-Weekly Semaglutide in Persons with Obesity and Knee Osteoarthritis." *N Engl J Med.* 2024. PMID: [39476339](https://pubmed.ncbi.nlm.nih.gov/39476339/) — the genuine STEP 9 trial (NCT05064735) result, sponsored by Novo Nordisk, showing semaglutide reduced knee OA pain and body weight in patients with obesity.

## Sources

- https://www.merck.com/research/product-pipeline/
- https://www.merck.com/wp-content/uploads/sites/124/2026/02/Public-Pipeline-1Q2026-Merck.pdf
- https://www.nejm.org/doi/full/10.1056/NEJMp048286
- https://www.ema.europa.eu/en/news/european-medicines-agency-statement-following-withdrawal-vioxx-rofecoxib
- https://www.merck.com/news/merck-provides-update-on-odanacatib-development-program/
- https://www.pharmacytimes.com/view/merck-discontinues-development-of-osteoporosis-drug-due-to-stroke-risk
- https://www.nature.com/articles/nrd.2016.207
- https://clinicaltrials.gov/study/NCT00140894 (verified via ClinicalTrials.gov API)
- https://clinicaltrials.gov/study/NCT05064735 (verified via ClinicalTrials.gov API)
- https://clinicaltrials.gov/study/NCT00704847 (verified via ClinicalTrials.gov API)
- https://pubmed.ncbi.nlm.nih.gov/41656471/
- https://pubmed.ncbi.nlm.nih.gov/36660678/
- https://pubmed.ncbi.nlm.nih.gov/32582709/
- https://pubmed.ncbi.nlm.nih.gov/30773420/
- https://pubmed.ncbi.nlm.nih.gov/39476339/
- /Users/wkalmans/OA/data/oa_pipeline_branded_assets.csv (this project's own data, cross-checked as part of the semaglutide investigation)
