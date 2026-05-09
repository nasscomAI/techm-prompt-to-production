skills:

- name: load_dataset
  description: Load ward budget CSV, validate all required columns, detect and report null actual_spend values before returning.
  input: File path to ward_budget.csv; optionally filter by ward and category names (strings).
  output: Dict with keys: {'data': list of dicts, 'null_rows': list of dicts with period/notes, 'row_count': int, 'null_count': int}. Data is sorted by period (chronologically) within the filtered scope
  error_handling: If file not found, raise FileNotFoundError. If required columns missing, raise ValueError. If filter produces no rows, return empty data list and note it clearly. Never silently drop null rows — explicitly return them in null_rows.

- name: compute_growth
  description: Compute month-over-month (MoM) or year-over-year (YoY) growth for a single ward-category filtered from load_dataset output, showing formula and handling nulls.
  input: Dict from load_dataset (filtered to one ward-category); growth_type ('MoM' or 'YoY'); period column (YYYY-MM format).
  output: CSV-writable list of dicts with columns: period, previous_period, previous_spend, current_spend, growth_percent, formula. Include only rows where both previous and current actual_spend are non-null. If growth_type is YoY, compare Jan 2024 to Jan 2024 (impossible), return empty or flag [INSUFFICIENT_DATA].
  error_handling: If growth_type is not 'MoM' or 'YoY', raise ValueError("growth_type must be 'MoM' or 'YoY'"). If all values in the series are null, return empty. Never compute on null values — skip silently and flag those periods.
