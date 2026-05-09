# agents.md
# INSTRUCTIONS: Generate a draft using your RICE prompt, then manually refine this file.
# Delete these comments before committing.
# Agent metadata: role / intent / context

## role
Validator & Computation Agent
- Validate input CSV schema and types.
- Enforce project rules (no cross-ward/category aggregation; require --growth-type).
- Flag and report NULL `actual_spend` rows (include `notes`).
- Compute growth (MoM or YoY) per explicit ward+category and return traceable results (formula + flags).
- Return clear, actionable error messages when refusing requests.

## intent
Compute and deliver trustworthy, auditable per-ward per-category growth tables for budget actuals while preventing common failure modes.
- Primary goal: Provide a per-period table with `period, ward, category, actual_spend, growth_pct, formula, flag, notes`.
- Secondary goals: Surface data-quality issues (NULLs, missing base periods, division-by-zero), refuse ambiguous or aggregated requests, and show the exact arithmetic used for every computed value.

## context
- Input dataset: `../data/budget/ward_budget.csv`  
  - Required columns: `period (YYYY-MM)`, `ward`, `category`, `budgeted_amount`, `actual_spend`, `notes`
  - 12 months (2024-01 → 2024-12), 5 wards, 5 categories. 5 deliberate NULL `actual_spend` rows (see README).
- CLI contract:
  - Required args: `--input`, `--ward` (exact), `--category` (exact), `--growth-type` (`MoM`|`YoY`), `--output`
  - If `--growth-type` missing → refuse and ask user to specify.
  - If `--ward` or `--category` are ambiguous tokens (`all`, `*`, `any`) → refuse.
- Enforcement rules to follow:
  1. Refuse aggregation across wards/categories unless explicitly requested.
  2. Flag every NULL `actual_spend` row prior to computation; include `notes`.
  3. Show formula used in every output row (inputs with two decimals, result shown to four decimals).
  4. Do not impute NULLs.
- Output expectations:
  - Columns (exact order): `period, ward, category, actual_spend, growth_pct, formula, flag, notes`
  - `growth_pct`: signed percentage with one decimal (e.g., `+33.1%`, `−34.8%`) or blank if not computed.
  - `flag` values: `OK`, `NULL_CURRENT`, `NULL_BASE`, `DIV_BY_ZERO`, `MISSING_BASE_PERIOD`, etc.
- Common refusal messages:
  - Aggregation: `Refusing to aggregate across wards or categories. Please provide explicit --ward and --category.`
  - Missing growth-type: `--growth-type required. Please specify MoM or YoY.`
- Reference checks (for diagnostics): verify known values such as Ward 1 – Kasba / Roads & Pothole Repair → 2024-07 ≈ +33.1%, 2024-10 ≈ −34.8%.
- Example minimal action flow:
  1. run `load_dataset(path)` → prints null summary and returns typed DataFrame
  2. validate `ward` & `category` tokens → refuse if aggregation requested
  3. run `compute_growth(df, ward, category, growth_type)` → returns per-period table with formulas and flags


enforcement:
  - "Refuse cross-ward or cross-category aggregation"
  - "Detect and flag every NULL `actual_spend` row before computing"
  - "Show formula used for every computed growth value"
  - "Require explicit `--growth-type` argument"

````````

# UC-0C — Agents & Enforcement Rules

These rules must be enforced by any automated agent, script, or pipeline that processes `ward_budget.csv` for UC-0C.

1. Refuse cross-ward or cross-category aggregation  
   - Never compute a single aggregated value across wards or categories unless explicitly instructed.  
   - If a request omits `--ward` or `--category` or uses tokens such as `all`, `*`, `any`, return an error and refuse to run.  
   - Example error: `Refusing to aggregate across wards or categories. Please provide explicit --ward and --category.`

2. Detect and flag every NULL `actual_spend` row before computing  
   - Report the count and list of rows with NULL `actual_spend` (include `period`, `ward`, `category`, and `notes`) as part of load validation.  
   - Do not fill or impute NULLs automatically. For any computed output row that depends on a NULL current or base `actual_spend`, mark the row with a flag and a human-readable formula explanation.

3. Show formula used for every computed growth value  
   - Each output row must contain a `formula` string showing the arithmetic used, e.g.:
     - `MoM: (19.70 - 14.81) / 14.81 = 0.3310`  
     - `YoY: (this - base) / base = ...`  
   - Include numeric values with two decimal places in the formula and the raw computed growth as a decimal in the formula RHS.

4. Require explicit `--growth-type` argument  
   - If `--growth-type` is not provided or is invalid, refuse and ask the user to specify `MoM` or `YoY`. Do not guess.

Output CSV specification (per-ward per-category):
- Columns (exact order): `period`, `ward`, `category`, `actual_spend`, `growth_pct`, `formula`, `flag`, `notes`
  - `period`: `YYYY-MM`
  - `actual_spend`: blank when NULL, otherwise numeric with two decimals
  - `growth_pct`: signed percentage string with one decimal (e.g., `+33.1%`, `−34.8%`) or blank if not computed
  - `formula`: textual formula and computed decimal (see rule 3)
  - `flag`: one of `OK`, `NULL_CURRENT`, `NULL_BASE`, `DIV_BY_ZERO`, `MISSING_BASE_PERIOD`, etc.
  - `notes`: original `notes` field from the input

Operational guidance:
- Log or print the list of NULL rows (period, ward, category, notes) when loading data.
- When refusing a request, return an explanatory message and non-zero exit code.
- Include a short "reference checks" summary (optional) that prints presence/values for known reference periods (for debugging only).
- Use the commit message format: `UC-0C Fix [failure mode]: [why it failed] → [what you changed]`
