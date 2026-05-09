skills:
  - name: load_dataset
    description: Reads CSV, validates columns, reports null count and which rows before returning
    input: File path (string) to the CSV file
    output: Pandas DataFrame with loaded data and a string report detailing null count and specific null rows
    error_handling: Raises ValueError if required columns are missing or file cannot be read; explicitly reports null count and rows to prevent silent null handling
  - name: compute_growth
    description: Takes ward + category + growth_type, returns per-period table with formula shown
    input: Ward (string), category (string), growth_type (string), dataset (Pandas DataFrame)
    output: List of dictionaries, each containing period, actual_spend, growth, and formula; null rows flagged with reason
    error_handling: Raises ValueError if ward or category not found, or growth_type invalid; refuses to aggregate across wards/categories or assume growth_type; flags nulls and reports reasons without computing growth
