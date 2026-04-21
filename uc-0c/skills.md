# skills.md

skills:
  - name: load_dataset
    description: Reads the CSV budget data file, validates the required columns, and reports the total null count and details of which rows have null actual_spend values before returning the data.
    input: File path to the CSV file (string).
    output: Pandas DataFrame with validated columns, plus a report of null rows including period, ward, category, and notes.
    error_handling: Raises an error if required columns are missing or if the file cannot be read, with a descriptive message.

  - name: compute_growth
    description: Takes a specific ward, category, and growth type, filters the data accordingly, and computes growth rates for each period, showing the formula used.
    input: DataFrame from load_dataset, ward name (string), category name (string), growth_type ('MoM' or 'YoY').
    output: DataFrame with columns for period, actual_spend, growth_rate, and formula, where null values are flagged instead of computed.
    error_handling: Refuses to compute if ward or category is not found in the data, or if growth_type is invalid, with a clear error message.
