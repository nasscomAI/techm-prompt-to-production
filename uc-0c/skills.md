# skills.md

skills:
  - name: load_dataset
    description: Reads the CSV dataset, validates columns, and reports the null count and missing rows before returning.
    input: The file path to the ward_budget.csv (string).
    output: A list of dictionaries representing the budget rows, or an error if invalid.
    error_handling: Identifies null `actual_spend` values immediately and flags them for the downstream calculator.

  - name: compute_growth
    description: Takes the ward, category, and growth_type, and returns a per-period table with the exact formula shown.
    input: The filtered dataset (list of dicts), target ward (string), category (string), and growth-type (enum).
    output: A CSV file output containing Ward, Category, Period, Actual Spend, Growth, Formula, and Notes.
    error_handling: Raises an explicit refusal/error if ward, category, or growth-type are missing or if invalid aggregation is requested. Safely logs 'NULL_FOUND' for any period lacking an actual_spend without crashing.
