# UC-0C — Number That Looks Right

**Core failure modes:** Wrong aggregation level · Silent null handling · Formula assumption

---

## Your Input File
```
../data/budget/ward_budget.csv
```
300 rows · 5 wards · 5 categories · 12 months (Jan–Dec 2024) · **5 deliberate null actual_spend values**

## Your Output File
```
uc-0c/growth_output.csv
```
Must be a per-ward per-category table — not a single aggregated number.

## Run Command
```bash
python app.py \
  --input ../data/budget/ward_budget.csv \
  --ward "Ward 1 – Kasba" \
  --category "Roads & Pothole Repair" \
  --growth-type MoM \
  --output growth_output.csv
```

---

## Dataset Structure
| Column | Type | Notes |
|---|---|---|
| period | YYYY-MM | 2024-01 through 2024-12 |
| ward | string | 5 wards |
| category | string | 5 categories |
| budgeted_amount | float | Always present |
| actual_spend | float or blank | **5 rows are deliberately null** |
| notes | string | Explains null reason |

**The 5 null rows:**
- 2024-03 · Ward 2 – Shivajinagar · Drainage & Flooding
- 2024-07 · Ward 4 – Warje · Roads & Pothole Repair
- 2024-11 · Ward 1 – Kasba · Waste Management
- 2024-08 · Ward 3 – Kothrud · Parks & Greening
- 2024-05 · Ward 5 – Hadapsar · Streetlight Maintenance

---

## Reference Values — Verify Your Output Against These

| Ward | Category | Period | Actual Spend (₹ lakh) | MoM Growth |
|---|---|---|---|---|
| Ward 1 – Kasba | Roads & Pothole Repair | 2024-07 | 19.7 | +33.1% (monsoon spike) |
| Ward 1 – Kasba | Roads & Pothole Repair | 2024-10 | 13.1 | −34.8% (post-monsoon) |
| Ward 2 – Shivajinagar | Drainage & Flooding | 2024-03 | NULL | Must be flagged — not computed |
| Ward 4 – Warje | Roads & Pothole Repair | 2024-07 | NULL | Must be flagged — not computed |
| Any | Any | Any | n/a | All-ward aggregation → system must REFUSE |

---

## Agents & Enforcement

Follow these project-level rules when implementing agents, scripts, or pipelines:

- Never aggregate across wards or categories unless explicitly instructed — refuse and return an error message if a user requests an all-ward or all-category aggregation.
- Flag every null `actual_spend` row before computing and include the `notes` column reason in the report.
- Show the formula used for each computed growth value in every output row (e.g., "MoM: (this_month - last_month) / last_month").
- If the `--growth-type` argument is not provided, refuse to run and return a clear message asking the user to specify `MoM` or `YoY`.

---

## Skills to Define in skills.md
- `load_dataset` — reads CSV, validates required columns (`period`, `ward`, `category`, `budgeted_amount`, `actual_spend`, `notes`), reports null count and the rows with nulls (including the `notes` field) before returning the dataset.
- `compute_growth` — takes ward + category + growth_type (`MoM` or `YoY`), returns a per-period table filtered to that ward+category with the computed growth column, the formula string per row, and explicit flags for any rows with missing `actual_spend`.

---

## What Will Fail From the Naive Prompt
Run `"Calculate growth from the data."` on the full CSV first.
Watch for: one single number returned for all wards combined; no mention of the 5 null rows; formula chosen silently (MoM or YoY picked without being asked).

---

## Commit Formula
```
UC-0C Fix [failure mode]: [why it failed] → [what you changed]
```
