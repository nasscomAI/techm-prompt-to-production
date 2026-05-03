# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: [reads the CSV file and returns a summary of the budget]
    input: [data/budget/ward_budget.csv]
    output: [uc-0c/growth_output.csv]
    error_handling: [flags null rows before computing]

  - name: compute_growth
    description: takes ward + category + growth_type, returns per-period table with formula shown
    input: [ward, category, growth_type]
    output: [summary of the budget with growth]
    error_handling: [refuses to compute when input is invalid or ambiguous]
