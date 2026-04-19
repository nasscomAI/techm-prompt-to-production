skills:
  - name: load_dataset
    description: Reads the CSV data, validates columns, and reports any null records with their reasons.
    input: Filepath to the CSV dataset (string).
    output: Validated dataset (dataframe) and a report of null counts including which rows contain null actual_spend and the notes explaining why.
    error_handling: If file is missing or columns are malformed, halt execution and report the error. If nulls are present, flag them but return the dataset for further processing.

  - name: compute_growth
    description: Calculates growth for a specific ward and category based on the specified growth type (e.g. MoM), explicitly adding the formula used.
    input: Validated dataset (dataframe), ward (string), category (string), and growth_type (string).
    output: Per-period table (dataframe/CSV format) with the formula shown alongside the result.
    error_handling: If --growth-type is not specified, refuse to guess and prompt the user. If asked to aggregate across wards or categories, refuse unless explicitly instructed. If data for a period is null, flag the row and do not compute growth.
