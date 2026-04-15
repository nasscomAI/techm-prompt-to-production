# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Read the ward budget CSV, validate presence of required columns, and identify rows with missing actual_spend values including their notes.
    input: Absolute path to the ward_budget.csv file.
    output: List of dictionaries (raw data) and a summary of null rows.
    error_handling: Fail with an error if required columns (period, ward, category, budgeted_amount, actual_spend) are missing.

  - name: compute_growth
    description: Filter data by ward and category, then calculate Month-on-Month or Year-on-Year growth while reporting the mathematical formula.
    input: Data list, ward name, category name, and growth_type.
    output: List of dictionaries with period, actual_spend, growth_value, and formula.
    error_handling: Return an error message if ward or category is not found, or if growth_type is invalid.
