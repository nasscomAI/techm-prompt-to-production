skills:
  - name: load_dataset
    description: Reads the CSV dataset, validates columns, and reports null count with row identification before returning the data.
    input: File path to the dataset (string).
    output: A list of dicts representing valid rows and a summary of null rows metadata.
    error_handling: Raises an exception if columns are missing or incorrectly formatted, and loudly flags missing actual_spend rows including their associated notes.

  - name: compute_growth
    description: Calculates growth (like MoM) strictly per-period using explicit ward and category assignments without cross-aggregation.
    input: Validated dataset (list of dicts), target ward (string), target category (string), and growth_type (string).
    output: A per-period table (list of dicts) with computed growth, spending metrics, and the literal formula used.
    error_handling: Refuses calculation if growth_type is missing or if asked to aggregate across any ward or category silently. Skips and flags calculation explicitly when period data is functionally null.
