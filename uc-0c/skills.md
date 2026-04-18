skills:
  - name: load_dataset
    description: Reads the budget CSV file, validates columns, and reports the total null count along with the specific rows that contain them.
    input: File path to the budget CSV (e.g., ward_budget.csv)
    output: A validated dataset object/dataframe and a pre-computation report of null values and reasons.
    error_handling: Halts execution and logs an error if expected columns are missing or data format is corrupt.

  - name: compute_growth
    description: Calculates per-period growth for a specific ward and category based on the requested growth type, explicitly detailing the formula used.
    input: Validated dataset, target ward, target category, and specified growth_type (e.g., MoM, YoY).
    output: A per-period table (CSV/DataFrame) containing growth metrics, flagging null rows without computing them, and displaying the formula.
    error_handling: Refuses calculation if growth_type is missing, or if asked to aggregate across multiple wards/categories.
