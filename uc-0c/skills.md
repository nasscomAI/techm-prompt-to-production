# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Loads and validates the budget CSV dataset, reporting null counts and specific null rows.
    input: File path to CSV (string).
    output: Pandas DataFrame with validated columns.
    error_handling: Raises error if required columns missing or file not found; reports null details.

  - name: compute_growth
    description: Computes growth rates for a specific ward and category, handling nulls and showing formulas.
    input: DataFrame, ward (string), category (string), growth_type ('MoM' or 'YoY').
    output: List of dicts with period, actual_spend, growth_percentage, formula_used, flag.
    error_handling: Flags null rows, skips growth calculation for nulls, refuses invalid growth_type.
