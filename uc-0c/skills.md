# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads the CSV budget dataset, validates required columns, parses `period` to YYYY-MM dates, and coerces `actual_spend` to numeric.
    input: path to CSV file (string). Expected columns: `period, ward, category, budgeted_amount, actual_spend, notes`.
    output: pandas.DataFrame with parsed `period` (datetime) and `actual_spend` numeric (NaN for blanks).
    error_handling: Raises an error if required columns are missing. Returns DataFrame nonetheless and allows caller to detect/handle NaNs.

  - name: compute_growth
    description: Compute per-period growth for a single `ward` + `category` using the requested growth type (MoM or YoY). Includes formula text per output row and flags rows with NULL `actual_spend`.
    input:
      - df: pandas.DataFrame returned by `load_dataset`
      - ward: string (single ward only)
      - category: string (single category only)
      - growth_type: string, one of `MoM`, `YoY` (case-insensitive)
    output: pandas.DataFrame with columns: `period, actual_spend, notes, formula, growth_percent` (one row per period for the ward+category)
    error_handling:
      - If the ward+category subset is empty, raise a clear error.
      - If growth_type is unsupported, refuse with explicit error.
      - If required inputs indicate aggregation (e.g., `all`), refuse rather than guess.
