# skills.md

skills:
  - name: load_dataset
    description: Reads CSV, validates columns, reports null count and which rows before returning.
    input: File path string pointing to the CSV dataset.
    output: A validated data structure (e.g. list of dictionaries) and a summary log of all null rows found.
    error_handling: Halt execution explicitly with a clear error if the file is missing or improperly formatted.

  - name: compute_growth
    description: Takes ward + category + growth_type, returns per-period table with formula shown.
    input: Validated dataset, along with strict filter constraints for ward, category, and growth_type (e.g., MoM).
    output: Formatted CSV string detailing period, actual spend, calculated growth, and the precise formula utilized.
    error_handling: Trigger a strict refusal asking for clarification if any filter parameter is ambiguous, unsupplied, or implies cross-ward/category aggregation without explicit permission.
