skills:
  - name: load_dataset
    description: >
      Reads a ward budget CSV file, validates that all required columns are
      present, detects every null actual_spend row, and reports the null count
      and details before returning the validated dataset.
    input:
      type: string
      format: >
        File path (absolute or relative) pointing to a CSV file with the
        required columns: period (YYYY-MM), ward (string), category (string),
        budgeted_amount (float), actual_spend (float or blank), notes (string).
    output:
      type: object
      format: >
        An object containing:
          - data: the full dataset as a list of row objects or DataFrame
          - null_report: a list of objects for every row where actual_spend is
            null, each containing period, ward, category, and reason (from the
            notes column)
          - null_count: integer count of null actual_spend rows
          - row_count: total number of rows loaded
          - wards: list of distinct ward values found
          - categories: list of distinct category values found
    error_handling:
      file_not_found: >
        Raise a FileNotFoundError with the attempted path; do not proceed to
        computation.
      missing_columns: >
        If any of the required columns (period, ward, category,
        budgeted_amount, actual_spend, notes) are missing from the CSV header,
        raise a ValueError listing every missing column name; do not return a
        partial dataset.
      empty_file: >
        If the file exists but contains no data rows (only a header or is
        completely empty), raise an IOError stating the file is empty; do not
        return an empty dataset.
      unreadable: >
        If the file cannot be parsed as CSV or decoded as UTF-8, raise an
        IOError with the decode or parse error message.
      nulls_detected: >
        Do not raise an error for null actual_spend values; instead, populate
        the null_report list with period, ward, category, and reason for every
        null row. Print the null report to stdout as a warning before returning
        so the caller is informed before any computation begins.

  - name: compute_growth
    description: >
      Filters the dataset to a specific ward, category, and growth type, then
      computes the growth rate for each period with the formula shown alongside
      each result, flagging null rows and null-dependent rows instead of
      computing values for them.
    input:
      type: object
      format: >
        An object containing:
          - data: the validated dataset returned by load_dataset
          - null_report: the null report list returned by load_dataset
          - ward: string — the exact ward name to filter on
          - category: string — the exact category name to filter on
          - growth_type: string — "MoM" (month-over-month) or "YoY"
            (year-over-year); must be explicitly provided, never defaulted
    output:
      type: object
      format: >
        A list of row objects (or CSV-ready table), one per period for the
        selected ward and category, each containing:
          - period: string (YYYY-MM)
          - ward: string
          - category: string
          - actual_spend: float or "NULL"
          - previous_period_spend: float, "NULL", or "N/A" (for the first row)
          - growth_pct: float formatted to one decimal place, or a flag string
          - formula: string showing the exact calculation, e.g.
            "((19.7 - 14.8) / 14.8) * 100 = +33.1%", or a flag explaining why
            growth cannot be computed
          - flag: null if computable, or a string such as
            "NULL — [reason from notes]" or
            "SKIP — prior period actual_spend is null"
    error_handling:
      ward_not_found: >
        If the specified ward does not exist in the dataset, raise a
        ValueError listing all valid ward names found in the data.
      category_not_found: >
        If the specified category does not exist in the dataset, raise a
        ValueError listing all valid category names found in the data.
      growth_type_missing: >
        If growth_type is not provided, is empty, or is not one of "MoM" or
        "YoY", raise a ValueError stating that --growth-type must be
        explicitly specified as "MoM" or "YoY"; never default to either.
      null_actual_spend: >
        For any period where actual_spend is null, do not compute a growth
        value. Set growth_pct to null, set formula to "N/A — actual_spend is
        null", and set flag to "NULL — [reason from notes column]".
      null_prior_period: >
        For any period where the prior period's actual_spend is null (making
        the MoM denominator undefined), do not compute a growth value. Set
        growth_pct to null, set formula to "N/A — prior period actual_spend
        is null", and set flag to "SKIP — prior period actual_spend is null".
      first_period: >
        For the earliest period in the filtered series, there is no prior
        period. Set growth_pct to null, set formula to "N/A — no prior
        period", and set flag to "N/A — first period".
      aggregation_attempt: >
        If ward is set to "ALL" or category is set to "ALL" or any value
        implying cross-ward or cross-category aggregation, raise a ValueError
        stating that aggregation across wards or categories is not permitted
        unless explicitly instructed. The system must refuse, not comply.
      insufficient_data: >
        If the filtered dataset for the given ward and category contains fewer
        than 2 rows, raise a ValueError stating that at least 2 periods are
        required to compute growth.
