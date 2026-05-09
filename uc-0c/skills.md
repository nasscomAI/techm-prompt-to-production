# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads CSV, validates required columns, and reports null rows before processing.
    input: CSV file path
    output: Validated dataset and null row report
    error_handling: Return error if required columns are missing

  - name: compute_growth
    description: Computes per-period growth for a given ward, category, and growth type.
    input: Dataset + ward + category + growth_type
    output: Per-period growth table with formula shown
    error_handling: Flag null rows and refuse if growth_type missing
