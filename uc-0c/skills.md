# skills.md

skills:
  - name: load_dataset
    description: Read CSV budget file, validate required columns, identify and report all null actual_spend rows before returning data structure.
    input: |
      Parameters:
      - csv_file: path to ward_budget.csv (string)
      Returns: structured dataset object with:
      - rows: list of all records (dicts)
      - columns: list of column names present
      - column_validation: pass/fail for required columns
      - null_summary: count of null actual_spend values
      - null_details: list of null rows with [period, ward, category, notes columns]
    output: |
      Dataset object (dict/JSON) with:
      - filename: string (e.g., "ward_budget.csv")
      - total_rows: integer count
      - columns: list of actual column names from CSV header
      - validation_status: "PASS" or "FAIL"
      - required_columns: ["period", "ward", "category", "budgeted_amount", "actual_spend", "notes"]
      - null_count: integer count of rows where actual_spend is null or empty
      - null_rows: list of objects with [period, ward, category, notes, reason="null in actual_spend"]
      - data: list of all row records as dictionaries (including null rows)
      - load_timestamp: ISO datetime of load
    error_handling: |
      If CSV file not found: return error "File not found: [path]" and halt.
      If required columns missing: return validation_status="FAIL" with list of missing columns; do not process data.
      If file is empty: return total_rows=0 and null_count=0; proceed with empty data list.
      If period column values are malformed (not YYYY-MM format): log warning for each row and flag as validation issue but continue loading.
      If ward or category values are empty strings: flag as data quality issue in validation_status but include in output.
      After loading, always report null_count and null_rows prominently before returning — zero silent nulls.

  - name: compute_growth
    description: Calculate Month-over-Month or Year-over-Year growth for a specific ward and budget category across all available periods.
    input: |
      Parameters:
      - dataset: structured dataset object (output of load_dataset)
      - ward: specific ward name (string, must match exactly a value in dataset)
      - category: specific budget category (string, must match exactly a value in dataset)
      - growth_type: "MoM" (Month-over-Month) or "YoY" (Year-over-Year), required, no default
      Returns: growth calculation table object with:
      - ward: echoed from input
      - category: echoed from input
      - growth_type: echoed from input
      - growth_rows: list of growth calculation objects for each period
    output: |
      Growth calculation object (dict/JSON) with:
      - ward: string (user-specified)
      - category: string (user-specified)
      - growth_type: "MoM" or "YoY" (as specified)
      - calculation_formula: string explaining the formula used (e.g., "MoM: (current_spend − previous_spend) / previous_spend × 100")
      - growth_rows: list of period calculation objects, each containing:
        - period: YYYY-MM (current period)
        - actual_spend: float or null
        - previous_period: YYYY-MM (prior month for MoM, prior year for YoY)
        - previous_spend: float or null
        - growth_percent: float (percent change) or string "N/A" if cannot compute
        - formula_applied: string showing exact values used (e.g., "(45.2 − 38.1) / 38.1 = +18.5%")
        - flags: list of flags (e.g., "#FLAG: NULL DATA in current period" or "#FLAG: Cannot compute — NULL in previous period")
      - null_flagged_periods: list of periods where actual_spend is null (copied from dataset.null_rows)
      - computation_status: "SUCCESS" if growth computed for all valid periods, "PARTIAL" if some N/A due to nulls, "FAILED" if no growth computed
    error_handling: |
      If ward not found in dataset: return error "Ward not found: [input]. Available wards: [list]".
      If category not found in dataset: return error "Category not found: [input]. Available categories: [list]".
      If growth_type not in ["MoM", "YoY"]: return error "Invalid growth_type: [input]. Must be 'MoM' or 'YoY'".
      If growth_type is missing: return error "growth_type required. Specify --growth-type MoM or --growth-type YoY".
      If selected ward+category has no data rows: return error "No data found for ward=[ward] category=[category]".
      If actual_spend is NULL in current period: set growth_percent="N/A", add flag "#FLAG: NULL in current period: [reason from notes]", do not compute.
      If actual_spend is NULL in previous period (required by formula): set growth_percent="N/A", add flag "#FLAG: Cannot compute growth — NULL in required previous period", do not compute.
      If first period in dataset (no previous month for MoM, no prior year data for YoY): set growth_percent="N/A", reason="No prior period available".
      After computation: validate that all null_rows from dataset are flagged in output; report computation_status and count of computable vs. non-computable periods.
