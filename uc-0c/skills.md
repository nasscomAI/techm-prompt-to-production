skills:
  - name: load_dataset
    description: Reads CSV, validates columns, reports null count and which rows before returning.
    input: A file path string pointing to a CSV file containing budget data with columns period, ward, category, budgeted_amount, actual_spend, notes.
    output: A list of dictionaries representing the validated dataset, with a report of null rows including reasons from notes.
    error_handling: If the CSV file is unreadable or missing required columns, return an error message; if nulls are present, explicitly report them with reasons to avoid silent null handling.

  - name: compute_growth
    description: Takes ward, category, and growth_type, returns per-period table with formula shown.
    input: Ward name string, category string, growth_type string (e.g., MoM), and the loaded dataset list of dictionaries.
    output: A list of dictionaries for the per-period growth table, including period, actual_spend, growth_percentage, and formula_used columns.
    error_handling: If ward or category is not found in the dataset, return an error; if growth_type is invalid or unspecified, refuse and ask; flag null rows and avoid aggregating across wards or categories to prevent wrong aggregation level.
