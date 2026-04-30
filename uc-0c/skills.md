# skills.md

skills:
  - name: load_dataset
    description: Reads the budget CSV file, validates columns, and explicitly reports the total null count and which specific rows are null before returning the data.
    input: File path to the budget dataset CSV.
    output: Parsed dataset structure, accompanied by a report detailing the null actual_spend rows and their reasons.
    error_handling: If the file is missing or columns do not match the expected schema, raise a structural validation error.

  - name: compute_growth
    description: Calculates budget growth metrics, returning a per-period table with explicit formulas and null handling.
    input: Ward string, category string, growth_type string (e.g., MoM), and the parsed dataset.
    output: A per-period table showing the calculated growth, the exact formula used, and flagging any nulls with their corresponding notes.
    error_handling: If `growth_type` is missing or if asked to aggregate across wards/categories without explicit instruction, refuse the computation and raise an error.
