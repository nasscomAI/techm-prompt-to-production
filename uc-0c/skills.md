# skills.md — UC-0C Financial Growth Calculator

skills:
  - name: load_dataset
    description: Read the CSV dataset, filter by ward and category, and report nulls.
    input: String path to the dataset, String ward, String category.
    output: List of dictionary records filtered for the specific ward and category.
    error_handling: Return an error if the dataset is missing or malformed. Refuse if 'Any' ward or category is passed without explicit multi-ward aggregation permission.

  - name: compute_growth
    description: Calculate MoM or YoY growth for the filtered dataset, ensuring nulls are flagged and formulas are shown.
    input: List of dictionary records, String growth_type (MoM or YoY).
    output: List of dictionary records containing period, actual_spend, growth percentage, and formula/flags.
    error_handling: Return an error if growth_type is missing or invalid.
