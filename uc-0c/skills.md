# skills.md — UC-0C Number That Looks Right

skills:
  - name: load_dataset
    description: >
      Reads the ward_budget.csv file, validates required columns, identifies and reports
      all null actual_spend rows (with their period, ward, category, and notes reason)
      before returning the full dataset as a list of records.
    input: >
      file_path (str): absolute or relative path to the ward_budget.csv file.
    output: >
      dict with two keys:
        - records (list of dicts): all CSV rows, each with keys:
            period, ward, category, budgeted_amount, actual_spend (float or None), notes
        - null_rows (list of dicts): rows where actual_spend is blank/null, each with:
            period, ward, category, budgeted_amount, null_reason (from notes column)
      Null rows are reported first before the caller proceeds to compute_growth.
    error_handling: >
      - If file_path does not exist: print clear error and exit (sys.exit(1)).
      - If required columns (period, ward, category, actual_spend, notes) are missing:
        print column-missing error listing found vs required columns and exit.
      - If dataset is empty after header: print error and exit.
      - Never silently drop null rows — always surface them in the null_rows list.
      - If actual_spend value is non-numeric and non-blank: treat as null, add to null_rows
        with null_reason = "Non-numeric value: <value>".

  - name: compute_growth
    description: >
      For a specified ward, category, and growth type (MoM or YoY), computes the
      per-period growth rate table from loaded dataset records, flags null rows,
      shows the formula used for every computed row, and writes the result to a CSV.
    input: >
      records (list of dicts): output of load_dataset — full dataset records.
      null_rows (list of dicts): output of load_dataset — pre-identified null rows.
      ward (str): exact ward name to filter on (e.g. "Ward 1 – Kasba").
      category (str): exact category name to filter on (e.g. "Roads & Pothole Repair").
      growth_type (str): "MoM" or "YoY" — MUST be explicitly provided; never guessed.
      output_path (str): path to write the growth_output.csv.
    output: >
      CSV file at output_path with columns:
        ward, category, period, actual_spend, growth_pct, formula_used, null_flag, null_reason
      Where:
        - growth_pct: float rounded to 1 decimal place, or "N/A" for first period, or
          "NULL_FLAGGED" if actual_spend is null for this row or its reference period.
        - formula_used: e.g. "((14.8 - 13.3) / 13.3) * 100" for MoM, or "N/A" / "NULL_FLAGGED".
        - null_flag: "NULL" if this row has no actual_spend, else blank.
        - null_reason: the notes text if null_flag="NULL", else blank.
      Also prints a null-row report to stdout before writing the CSV.
    error_handling: >
      - If ward does not exist in records: print "Ward not found" with list of valid wards
        and exit without writing output.
      - If category does not exist in records: print "Category not found" with valid list
        and exit without writing output.
      - If growth_type is not "MoM" or "YoY": print refusal message
        "Growth type not specified. Please provide --growth-type MoM or --growth-type YoY."
        and exit without writing output.
      - If a row's reference period (prior month for MoM, same month prior year for YoY)
        is null or missing: mark growth_pct as "NULL_FLAGGED" and formula_used as
        "NULL_FLAGGED — reference period has no actual_spend".
      - If filtered records for the ward+category combination are empty: print error and exit.
      - Print a completion summary: ward, category, growth_type, total periods, null count,
        and output file path.
