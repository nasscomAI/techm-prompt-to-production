skills:
  - name: load_dataset
    description: Reads the ward_budget CSV, validates required columns, and reports null actual_spend rows before returning data.
    input: input_path (str) — absolute or relative path to the CSV file.
    output: A tuple (all_rows, null_rows) where all_rows is a list of dicts (one per CSV row) and null_rows is the subset where actual_spend is blank; also prints a null summary to stdout listing each null row's period, ward, category, and notes reason.
    error_handling: Raises FileNotFoundError if the path does not exist. Raises ValueError if any required column (period, ward, category, budgeted_amount, actual_spend, notes) is missing. Never silently returns partial data.

  - name: compute_growth
    description: Filters the loaded dataset to a single ward and category, then computes the requested growth rate for each period with the formula shown.
    input: rows (list[dict] from load_dataset), ward (str), category (str), growth_type (str — one of MoM, YoY, QoQ).
    output: A list of dicts with keys period, ward, category, actual_spend, growth_type, formula, growth_pct, flag — one dict per period. Null periods and periods whose prior comparison period is null carry growth_pct=NULL and a flag explaining the reason. The first period(s) with no prior comparison period carry growth_pct=N/A.
    error_handling: Raises ValueError if growth_type is not MoM, YoY, or QoQ. Raises ValueError if no rows match the ward+category combination. Never aggregates across multiple wards or categories — caller must supply exactly one of each.
