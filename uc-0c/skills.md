# skills.md

skills:
  - name: load_dataset
    description: Reads ward_budget.csv, validates required columns, and reports null count and which rows are null before returning the dataset.
    input: File path (string) pointing to ward_budget.csv.
    output: Validated dataframe plus a null-report list — each entry contains period, ward, category, and null reason from the notes column.
    error_handling: Refuse and raise an error if any required column (period, ward, category, budgeted_amount, actual_spend, notes) is missing; report exact column names found vs expected.

  - name: compute_growth
    description: Computes per-period MoM or YoY growth for a single ward and category, showing the formula alongside each result.
    input: ward (string), category (string), growth_type (string — must be "MoM" or "YoY"), validated dataframe from load_dataset.
    output: Per-period table with columns: period, ward, category, actual_spend, growth_value, formula (e.g. "(19.7 - 14.8) / 14.8 × 100"). Null rows are included as flagged entries with growth_value = NULL and a reason note — not computed.
    error_handling: Refuse if growth_type is not explicitly "MoM" or "YoY" — ask the user to specify; refuse if ward or category does not match dataset values exactly; never aggregate across multiple wards or categories.
