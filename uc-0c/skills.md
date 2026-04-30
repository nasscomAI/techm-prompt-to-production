# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads the budget CSV, validates columns, and reports null count and which rows have nulls before returning the dataset.
    input: >
      A CSV file path (string) pointing to the budget dataset. Example:
        load_dataset(path="../data/budget/ward_budget.csv")
    output: >
      A dict/JSON object containing the parsed rows and a metadata block detailing nulls.
      Example:
        {
          "data": [{"period": "2024-01", "ward": "Ward 1...", ...}, ...],
          "null_report": {
            "total_nulls": 5,
            "null_rows": [{"period": "2024-03", "ward": "Ward 2...", "notes": "Data not submitted..."}]
          }
        }
    error_handling: >
      - If the input file is missing or unreadable, raise FileNotFoundError and halt.
      - If expected columns (period, ward, category, budgeted_amount, actual_spend, notes) are missing, raise ValueError with the missing columns listed.
      - Null `actual_spend` values must be explicitly preserved as nulls and not converted to 0.

  - name: compute_growth
    description: Takes the dataset, ward, category, and growth type, and returns a per-period table with the formula shown for each calculated row.
    input: >
      A dict containing the loaded dataset, and parameters for ward, category, and growth_type.
      Example:
        compute_growth(data=dataset, ward="Ward 1 – Kasba", category="Roads & Pothole Repair", growth_type="MoM")
    output: >
      A per-period list/table containing actual spend, the calculated growth, and the formula used.
      Example:
        [
          {"period": "2024-07", "actual_spend": 19.7, "growth": "+33.1%", "formula": "((19.7 - 14.8) / 14.8) * 100"},
          {"period": "2024-08", "actual_spend": null, "growth": "NULL", "formula": "NULL - Audit freeze"}
        ]
    error_handling: >
      - If `growth_type` is not provided or is invalid, raise a ValueError and refuse to compute — never guess.
      - If a row has a null `actual_spend`, it must not compute growth; instead, it must populate the formula/growth fields with the `notes` column reason.
      - If the request attempts to aggregate across multiple wards or categories without explicit instruction, raise an AggregationError and refuse.