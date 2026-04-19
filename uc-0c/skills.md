# skills.md

skills:
  - name: load_dataset
    description: Reads the ward budget CSV, validates required columns are present, and reports null actual_spend rows before returning the data.
    input: File path (string) to the CSV; expected columns — period, ward, category, budgeted_amount, actual_spend, notes.
    output: Validated dataframe plus a null-report list of objects {period, ward, category, reason} for every row where actual_spend is blank.
    error_handling: >
      Raises an error if the file is missing or any required column is absent.
      If null rows are found, prints the full null-report to stdout and waits —
      does not proceed silently. If the CSV is empty, refuses and reports.

  - name: compute_growth
    description: Computes MoM or YoY growth for a single ward + category combination and returns a per-period table with the formula shown on every row.
    input: >
      Validated dataframe (from load_dataset), ward (string), category (string),
      growth_type (string — must be exactly "MoM" or "YoY", never inferred).
    output: >
      Table with columns: period, actual_spend, growth_pct, formula, status.
      status is "OK" for computed rows and "SKIPPED — null: <reason>" for null rows.
    error_handling: >
      If ward or category is not found in the data, refuses and lists valid options.
      If growth_type is missing or unrecognised, refuses and asks the user to specify.
      If fewer than two non-null periods exist, refuses — cannot compute growth with
      insufficient data points.
      Never aggregates across wards or categories; if the caller passes multiple
      values, raises an explicit refusal.
