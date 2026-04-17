# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads the ward budget CSV file, validates schema, and identifies null actual_spend rows with reasons.
    input: type: string
           format: file path to CSV (e.g., ../data/budget/ward_budget.csv)
    output: type: object
format: >
{
"dataframe": tabular dataset,
"null_summary": {
"count": integer,
"rows": [
{
"period": string,
"ward": string,
"category": string,
"notes": string
}
]
}
}
    error_handling: 
    If file path is invalid or file cannot be read, return an explicit file access error and halt execution
    If required columns (period, ward, category, budgeted_amount, actual_spend, notes) are missing, return schema validation error and halt
    If dataset is empty or malformed, return data validation error and halt
    If null values exist in actual_spend, do not fail but explicitly report all such rows with reasons from notes column
    Do not perform any aggregation or transformation beyond validation and null detection

  - name: compute_growth
    description: Computes per-period growth for a specified ward and category using the given growth type, including formula and null handling.
    input: type: object
format: >
{
"dataframe": tabular dataset,
"ward": string,
"category": string,
"growth_type": string (e.g., MoM or YoY)
}
    output: type: table
format: >
Per-period table with columns:
period, ward, category, actual_spend, growth_value, formula, null_flag, null_reason
    error_handling: 
    If ward or category is missing or does not exist in dataset, return validation error and halt
    If growth_type is not provided, return error requesting explicit specification and halt without computation
    If growth_type is ambiguous or unsupported, return error and halt
    If input attempts aggregation across multiple wards or categories, refuse execution with explicit error
    For any row where actual_spend is null, flag the row, include null_reason from notes, and skip growth computation for that row
    If previous period value required for growth is null or missing, skip computation for that row and flag appropriately
    Ensure no silent null handling; all null-related skips must be explicitly marked in output
    If computation results deviate from known reference values, return warning or error indicating mismatch
    Ensure output is strictly per-period and not aggregated; otherwise return error




