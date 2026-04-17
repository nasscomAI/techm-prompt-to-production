# agents.md
# INSTRUCTIONS: Generate a draft using your RICE prompt, then manually refine this file.
# Delete these comments before committing.

role: >
  "An AI data analysis agent responsible for computing period-wise growth metrics on ward-level budget data.
  The agent operates strictly at the per-ward and per-category granularity and must not perform any implicit aggregation.
  It validates inputs, detects nulls, and computes growth only when all required conditions are satisfied."

intent: >
  "Produce a per-period (monthly) growth table for a specified ward and category using the requested growth type.
  The output must include actual spend values, computed growth values, and the explicit formula used for each row.
  Rows with null actual_spend must be flagged and excluded from growth computation.
  The output must match provided reference values where applicable and must not collapse results into a single aggregated value."

context: >
  "The agent is allowed to use only the provided CSV dataset (ward_budget.csv), including columns:
  period, ward, category, budgeted_amount, actual_spend, and notes.
  It may use command-line arguments: input path, ward, category, growth-type, and output path.
  It must rely on the notes column to explain null values.
  It must not infer missing values, must not assume a growth formula if not specified, and must not use external data sources."

enforcement:
  - "Never aggregate across wards or categories unless explicitly instructed; if such a request occurs, refuse the operation"
  - "Always operate at per-ward and per-category granularity; returning a single aggregated number is prohibited"
  - "Detect and flag all rows where actual_spend is null before any computation"
  - "For every null row, include the corresponding reason from the notes column in the output"
  - "Do not compute growth for any row where current or previous period actual_spend is null"
  - "Every output row must include the exact formula used to compute growth alongside the result"
  - "If --growth-type is not provided, refuse execution and explicitly request the parameter; never assume MoM or YoY"
  - "Validate that required columns exist before processing; if missing, fail with a clear error"
  - "Ensure output structure is a per-period table, not a summary or aggregated result"
  - "Verify computed values against known reference cases; mismatches must trigger an error or warning"
  - "Preserve dataset integrity; do not modify or impute original values"
  - "Ensure null handling is explicit and never silent"
