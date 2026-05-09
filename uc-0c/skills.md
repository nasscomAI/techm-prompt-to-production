# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: `load_dataset`
    description: Read the input CSV, validate required columns, report NULL `actual_spend` rows (with `notes`), and return a typed DataFrame.
    input: path: str
    output: pandas.DataFrame
    error_handling: If required columns are missing → raise error with clear message.

  - name: `compute_growth`
    description: Compute per-period growth (MoM or YoY) for a single `ward` + `category` and return a table that includes formulas and flags.
    input: df: pandas.DataFrame, ward: str, category: str, growth_type: Literal["MoM","YoY"]
    output: pandas.DataFrame
    error_handling: If no rows for the requested `ward`+`category`, raise an explanatory error.

````````

This is the code block that represents the suggested code change:

````````markdown
# UC-0C — Skills

This file documents the two primary skills required by UC-0C implementations.

## `load_dataset`
- Purpose: Read the input CSV, validate required columns, report NULL `actual_spend` rows (with `notes`), and return a typed DataFrame.
- Signature (pseudo):
  - Python: `def load_dataset(path: str) -> pandas.DataFrame`
- Required columns:
  - `period`, `ward`, `category`, `budgeted_amount`, `actual_spend`, `notes`
- Behavior:
  - Parse `period` as `YYYY-MM` → `datetime` (first day of month).
  - Parse `budgeted_amount` and `actual_spend` to numeric; leave `notes`, `ward`, `category` as strings.
  - If required columns are missing → raise error with clear message.
  - Print a summary: number of rows, number of NULL `actual_spend` rows.
  - For each NULL `actual_spend` row, print: `- {period} · {ward} · {category} · notes: {notes}`
- Return:
  - `pandas.DataFrame` with typed columns and original `notes` preserved.

## `compute_growth`
- Purpose: Compute per-period growth (MoM or YoY) for a single `ward` + `category` and return a table that includes formulas and flags.
- Signature (pseudo):
  - Python: `def compute_growth(df: pandas.DataFrame, ward: str, category: str, growth_type: Literal["MoM","YoY"]) -> pandas.DataFrame`
- Pre-conditions:
  - `df` must contain parsed `period` and numeric `actual_spend`.
  - `ward` and `category` must be explicit (no `all`/`*`/`any`).
- Behavior:
  - Filter to rows matching the exact `ward` and `category`.
  - Sort by `period` ascending.
  - For each row compute:
    - Base period:
      - `MoM` → previous calendar month
      - `YoY` → same month previous year
    - If current or base `actual_spend` is NULL → set `growth` blank, `formula` explains NULL, `flag` = `NULL_CURRENT` or `NULL_BASE`.
    - If base value = 0 → flag `DIV_BY_ZERO` and do not compute numeric growth.
    - Else compute growth = (current - base) / base, store numeric and format `growth_pct` as signed percent string with one decimal.
    - Populate `formula` with numeric values and computed decimal RHS (two decimals for inputs, four decimals for result).
- Return columns (exact order): `period`, `ward`, `category`, `actual_spend`, `growth_pct`, `formula`, `flag`, `notes`
- Errors:
  - If no rows for the requested `ward`+`category`, raise an explanatory error.

## Examples (pseudo)
- Load: `df = load_dataset("../data/budget/ward_budget.csv")`
- Compute: `out = compute_growth(df, "Ward 1 – Kasba", "Roads & Pothole Repair", "MoM")`
````````


# Response
````````markdown