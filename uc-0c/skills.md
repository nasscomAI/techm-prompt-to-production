# skills.md — UC-0C Budget Growth Analyst

skills:
  - name: load_dataset
    description: Reads the ward_budget CSV, validates all required columns are present, and reports the total null count and the specific rows with missing actual_spend before returning the data.
    input: String file_path — path to ward_budget.csv.
    output: Tuple of (List[dict] rows, List[dict] null_rows) where null_rows contains period, ward, category, and notes for every row where actual_spend is blank.
    error_handling: If required columns (period, ward, category, budgeted_amount, actual_spend, notes) are missing, raise a ColumnValidationError listing absent columns. If the file cannot be opened, raise FileNotFoundError.

  - name: compute_growth
    description: Filters the dataset to one ward and one category, then computes per-period MoM or YoY growth with the formula shown for every row, flagging nulls explicitly.
    input: List[dict] rows from load_dataset, String ward, String category, String growth_type (must be 'MoM' or 'YoY').
    output: List[dict] — one entry per period with keys 'period', 'actual_spend', 'growth_pct', 'formula', 'null_flag'. Rows with null actual_spend have growth_pct = 'NULL_FLAGGED' and formula = 'N/A — actual_spend missing: <reason>'.
    error_handling: If growth_type is not 'MoM' or 'YoY', raise ValueError and ask caller to specify. If no rows match the given ward + category, raise LookupError listing available wards and categories. If a prior period needed for growth computation is itself null, mark the current row as 'PRIOR_NULL' and skip the calculation.
