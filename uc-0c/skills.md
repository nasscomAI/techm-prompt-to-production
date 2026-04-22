
skills:
  - name: load_dataset
    description: Reads the budget CSV file, validates columns (period, ward, category, budgeted_amount, actual_spend), and identifies rows with null actual_spend values.
    input: CSV file path (string).
    output: pandas DataFrame.
    error_handling: Raises error for missing columns or file issues.

  - name: compute_growth
    description: Calculates MoM or YoY growth for a specific ward and category, flagging nulls and showing the formula used.
    input: DataFrame, ward (string), category (string), growth_type (string).
    output: Growth analysis table (DataFrame/List).
    error_handling: Errors on missing ward/category or invalid growth_type.
