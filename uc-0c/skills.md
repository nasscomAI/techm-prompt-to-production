skills:
  - name: load_dataset
    description: Reads the ward budget CSV, validates required columns, and reports null counts and specific null rows before returning the dataset.
    input:
      type: string
      format: file path to CSV (e.g., ../data/budget/ward_budget.csv)
    output:
      type: object
      format: >
        {
          "dataframe": tabular dataset with validated schema,
          "null_summary": {
            "count": integer,
            "rows": [
              { "period": YYYY-MM, "ward": string, "category": string, "notes": string }
            ]
          }
        }
    error_handling:
      - If the file path is invalid or file cannot be read, return an explicit error and stop execution.
      - If required columns (period, ward, category, budgeted_amount, actual_spend, notes) are missing or malformed, return a schema validation error.
      - If null values exist in actual_spend, they must be reported explicitly with row details and not ignored.
      - If dataset appears aggregated or missing expected 300-row structure, return an error indicating potential aggregation failure mode.

  - name: compute_growth
    description: Computes per-period growth for a specified ward and category using the given growth_type, returning results with formulas shown.
    input:
      type: object
      format: >
        {
          "dataframe": validated dataset,
          "ward": string,
          "category": string,
          "growth_type": string (e.g., MoM)
        }
    output:
      type: table
      format: >
        Per-period table with columns:
          period (YYYY-MM),
          actual_spend (float or NULL),
          growth_value (float or NULL),
          formula (string explaining calculation);
        excludes aggregation beyond specified ward and category.

    error_handling:
      - If ward or category is missing, invalid, or not found in dataset, return an explicit error.
      - If growth_type is not specified, refuse to compute and return an error requesting it explicitly.
      - If growth_type is unrecognized, return an explicit error and do not assume a formula.
      - If any row has null actual_spend, flag the row, include the notes reason, and do not compute growth for that period.
      - If computation attempt involves multiple wards or categories, refuse and return an aggregation violation error.
      - If prior period required for growth calculation is missing or null, set growth_value to NULL and explain in formula field.