# skills.md — UC-0C Number That Looks Right

skills:
  - name: load_dataset
    description: Reads the ward_budget CSV, validates required columns, and reports null actual_spend rows before returning data — null rows are surfaced, not hidden.
    input: csv_path (str) — path to ward_budget.csv
    output: tuple (rows, null_rows) — rows is list of dicts (all data), null_rows is list of dicts (period, ward, category, notes) for every row with missing actual_spend
    error_handling: Exits with an error if file not found; exits with an error listing missing column names if required columns are absent

  - name: compute_growth
    description: Filters the dataset to one ward and one category, then computes per-period growth with the formula shown alongside each result; null rows are flagged, not skipped.
    input: rows (list of dicts from load_dataset), ward (str), category (str), growth_type (str — "MoM" or "YoY")
    output: list of dicts with keys period, ward, category, actual_spend, growth (e.g. "+33.1%" or "NULL — FLAGGED"), formula (e.g. "(19.7 − 14.8) / 14.8 × 100"), null_reason
    error_handling: Returns empty list if no rows match ward+category; flags null prior-period as "NULL — FLAGGED" with formula explaining why; flags division-by-zero as "UNDEFINED"
