# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads the budget CSV, validates the presence of required columns, and reports the count and locations of null values in actual_spend.
    input: File path string to the budget CSV.
    output: Validated dataset object and a summary report of null entries with their associated notes.
    error_handling: Raises an error if mandatory columns (period, ward, category, actual_spend) are missing or if the file is inaccessible.

  - name: compute_growth
    description: Calculates growth (MoM or YoY) for a specific ward and category, returning a detailed table including the formula used.
    input: Object containing ward name, category name, and growth_type (MoM/YoY).
    output: A per-period table (CSV/JSON) containing original actual_spend, growth value, and the calculation formula.
    error_handling: Refuses to compute if growth_type is missing or if the requested ward/category combination contains no valid data.
