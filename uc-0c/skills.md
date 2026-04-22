# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: load_dataset
    description: Reads the ward_budget CSV, validates required columns, and reports null rows before returning the data.
    input: A file path to the ward_budget.csv file. The CSV must contain columns: period, ward, category, budgeted_amount, actual_spend, notes.
    output: An in-memory list of row dictionaries or similar structure with the validated data, plus a summary of how many rows have null actual_spend and which period/ward/category they correspond to.
    error_handling: If the file cannot be opened or the required columns are missing, raise a clear error and refuse to proceed. If rows are malformed, skip them with a warning and do not crash. All rows with null actual_spend must be included in the returned data but clearly marked so that compute_growth can flag them instead of silently ignoring them.

  - name: compute_growth
    description: Filters the dataset by ward and category and computes growth for each period using the requested growth_type, showing the formula used.
    input: The loaded dataset, a specific ward string, a specific category string, and a growth_type string (e.g. 'MoM' for month-over-month growth).
    output: A per-period table for the given ward and category containing, for each period: period, ward, category, actual_spend, growth_value (or blank when not computable), growth_formula (text explaining how the value was computed), and a flag field indicating when growth was not computed due to null actual_spend or missing prior period.
    error_handling: If the requested ward and category combination has no data, return an empty table with a clear message rather than guessing or aggregating other wards. If growth_type is missing or not recognised, refuse to compute and ask for a valid growth_type. For any period where actual_spend is null or the previous period's actual_spend is null, do not compute growth: leave the growth value blank, copy the null reason from notes, and mark the row as flagged for review.