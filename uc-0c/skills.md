# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads a CSV file, validates its columns, and reports the count and specific rows of any null values before returning the dataset.
    input: CSV file path (string)
    output: Validated dataset (structured object/dataframe) and a summary of null rows.
    error_handling: Flags every null row and reports the null reason from the notes column. Refuses to proceed silently if nulls are present.

  - name: compute_growth
    description: Computes growth metrics for a specific ward and category, returning a per-period table that includes the exact formula used.
    input: ward (string), category (string), growth_type (string: MoM/YoY), dataset (structured object)
    output: Per-period growth table (CSV format/structured object) with growth values and formula strings.
    error_handling: Refuses to guess the formula if growth_type is missing. Refuses to aggregate across wards or categories unless explicitly instructed. Does not compute metrics on flagged null rows.
