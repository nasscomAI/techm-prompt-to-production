skills:
  - name: load_dataset
    description: Reads the budget CSV file, validates the required columns (period, ward, category, actual_spend), and identifies/reports all null rows with their reasons from the notes column.
    input: File path (string) to the ward_budget.csv file.
    output: A validated Pandas DataFrame and a summary report of null rows (count and reasons).
    error_handling: Refuses to proceed if required columns are missing or if the file cannot be read.

  - name: compute_growth
    description: Computes Month-over-Month (MoM) growth for a specific ward and category, generating a table that includes the formula for each row.
    input: Ward name (string), category name (string), and growth_type (string, e.g., 'MoM').
    output: A table/DataFrame containing period, actual_spend, growth_value, and the calculation formula used.
    error_handling: Refuses and asks for clarification if growth_type is missing or if the ward/category combination is not found in the dataset. Flags null values as non-computable.
