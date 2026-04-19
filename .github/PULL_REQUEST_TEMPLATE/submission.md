# Vibe Coding Workshop — Submission PR

**Name:**  
**Session / Group:**  *(e.g. TechM · RICE · CRAFT · Civic Tech)*  
**Date:**  
**AI tool(s) used:**  

---

## Checklist — Complete Before Opening This PR

- [ ] `agents.md` committed for all 4 UCs
- [ ] `skills.md` committed for all 4 UCs
- [ ] `classifier.py` runs on `test_[city].csv` without crash
- [ ] `results_[city].csv` present in `uc-0a/`
- [ ] `app.py` for UC-0B, UC-0C, UC-X — all run without crash
- [ ] `summary_hr_leave.txt` present in `uc-0b/`
- [ ] `growth_output.csv` present in `uc-0c/`
- [ ] 4+ commits with meaningful messages following the formula
- [ ] All sections below are filled in

---

## UC-0A — Complaint Classifier

**Which failure mode did you encounter first?**
*(taxonomy drift / severity blindness / missing justification / hallucinated sub-categories / false confidence)*

> [Your answer]

**What enforcement rule fixed it? Quote the rule exactly as it appears in your agents.md:**

> [Your answer]

**How many rows in your results CSV match the answer key?**
*(Tutor will release answer key after session)*

> [Your answer] out of 15

**Did all severity signal rows (injury/child/school/hospital) return Urgent?**

> Yes / No — [explain any exceptions]

**Your git commit message for UC-0A:**

> [paste your commit message here]

---

## UC-0B — Summary That Changes Meaning

**Which failure mode did you encounter?**
*(clause omission / scope bleed / obligation softening)*

> [Your answer]

**List any clauses that were missing or weakened in the naive output (before your RICE fix):**

> [Your answer — reference clause numbers]

**After your fix — are all 10 critical clauses present in summary_hr_leave.txt?**

> Yes / No — [which are still missing or wrong]

**Did the naive prompt add any information not in the source document (scope bleed)?**

> Yes / No — [quote any bleed you found]

**Your git commit message for UC-0B:**

> [paste your commit message here]

---

## UC-0C — Number That Looks Right

**What did the naive prompt return when you ran "Calculate growth from the data."?**

> The naive prompt returned a single aggregated growth number across all wards and categories combined, with no breakdown by ward or category, no mention of null rows, and a silently assumed MoM formula — no refusal, no formula shown, no null report.

**Did it aggregate across all wards? Did it mention the 5 null rows?**

> Yes — it aggregated across all 5 wards and all 5 categories into one number. It did not mention any of the 5 null `actual_spend` rows. The null values were silently dropped or zero-filled without any warning.

**After your fix — does your system refuse all-ward aggregation?**

> Yes — `compute_growth` requires exactly one ward and one category passed via `--ward` and `--category` CLI flags. Passing multiple values raises an explicit refusal.

**Does your system report all null `actual_spend` rows (period, ward, category, notes) before computing any growth?**

> Yes — `load_dataset` scans the full dataset and prints a NULL REPORT before any computation. All 5 null rows are flagged:
> - 2024-03 · Ward 2 – Shivajinagar · Drainage & Flooding
> - 2024-07 · Ward 4 – Warje · Roads & Pothole Repair
> - 2024-11 · Ward 1 – Kasba · Waste Management
> - 2024-08 · Ward 3 – Kothrud · Parks & Greening
> - 2024-05 · Ward 5 – Hadapsar · Streetlight Maintenance

**Does your system refuse to proceed if `--growth-type` is not explicitly provided (MoM or YoY)?**

> Yes — running without `--growth-type` returns:
> `[REFUSED] --growth-type was not specified. Please provide --growth-type MoM or --growth-type YoY. This system never guesses the growth formula.`

**Does your system show the formula used alongside every computed result row?**

> Yes — every row in the output table includes the formula column:
> `MoM = (current − previous) / previous × 100`
> SKIPPED rows also carry the formula template for reference.

**Does your output match the reference values (Ward 1 Roads +33.1% in July, −34.8% in October)?**

> Yes — `growth_output.csv` confirms:
> - 2024-07 · actual_spend = 19.7 · growth = **+33.1%** ✓
> - 2024-10 · actual_spend = 13.1 · growth = **−34.8%** ✓

**Your git commit message for UC-0C:**

> `UC-0C Fix wrong aggregation + silent null handling + formula assumption: naive prompt aggregated all wards, dropped nulls silently, and guessed MoM → added load_dataset null report, compute_growth single-ward enforcement, --growth-type refusal, and per-row formula column`

---

## UC-X — Ask My Documents

**What did the naive prompt return for the cross-document test question?**
*(Question: "Can I use my personal phone to access work files when working from home?")*

> [Quote the actual output]

**Did it blend the IT and HR policies?**

> Yes / No — [explain]

**After your fix — what does your system return for this question?**

> [Quote the actual output]

**Did your system use any hedging phrases in any answer?**
*("while not explicitly covered", "typically", "generally understood")*

> Yes / No — [quote any you found]

**Did all 7 test questions produce either a single-source cited answer or the exact refusal template?**

> Yes / No — [list any that failed]

**Your git commit message for UC-X:**

> [paste your commit message here]

---

## CRAFT Loop Reflection

**Which CRAFT step was hardest across all UCs, and why?**

> [Your answer — 2–3 sentences]

**What is the single most important thing you added manually to an agents.md that the AI did not generate on its own?**

> [Your answer — be specific, quote the rule]

**Name one real task in your work where you will apply RICE + CRAFT within the next two weeks:**

> [Your answer]

---

## Reviewer Notes *(tutor fills this section)*

| Criterion | Score /4 | Notes |
|---|---|---|
| RICE prompt quality | | |
| agents.md quality | | |
| skills.md quality | | |
| CRAFT loop evidence | | |
| Test coverage | | |
| **Total** | **/20** | |

**Session:**  *(tutor fills — e.g. TechM · Cohort A · April 2026)*

**Badge decision:**
- [ ] Standard badge — meets pass threshold (score 11+/20 on this review, full rubric 22+/40)
- [ ] Distinction badge — meets distinction threshold (score 17+/20 on this review, full rubric 34+/40)
- [ ] Not yet — resubmit after addressing: _______________
