# skills.md

skills:
  - name: load_dataset
    description: Reads the budget CSV, validates required columns, and identifies rows with null 'actual_spend' values.
    input: File path (string) to the budget CSV.
    output: A list of dictionaries representing the dataset rows, plus a summary of null rows found.
    error_handling: Reports specific rows and reasons for any missing or null 'actual_spend' values.

  - name: compute_growth
    description: Calculates period-over-period growth for a specific ward and category, strictly enforcing RICE rules for granularity and formula transparency.
    input: Dataset (list), ward (string), category (string), and growth_type (MoM or YoY).
    output: A list of results including period, actual spend, calculated growth, and the formula used.
    error_handling: Refuses to calculate if ward/category is missing or if growth_type is not specified; flags null rows as NOT_COMPUTED.
