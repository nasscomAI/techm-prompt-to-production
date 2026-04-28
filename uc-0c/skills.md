# skills.md
  skills:
  - name: load_dataset
    description: Reads the ward_budget CSV, validates that all required columns
      are present, and reports the total null count and every null row with its
      reason before returning the dataset for downstream use.
    input:
      type: file_path
      format: String path to a CSV file expected to contain columns period,
        ward, category, budgeted_amount, actual_spend, and notes.
    output:
      type: object
      format: |
        {
          "data": array of row objects with all six columns,
          "null_report": [
            {
              "period": "YYYY-MM",
              "ward": "string",
              "category": "string",
              "null_reason": "string from notes column"
            }
          ],
          "null_count": integer,
          "row_count": integer
        }
    error_handling:
      missing_file: Halt immediately and return an error stating the file path
        could not be resolved; do not proceed to column validation.
      missing_columns: If any of the six expected columns are absent, halt and
        return a schema error listing every missing column name; do not return
        partial data.
      empty_file: If the CSV contains zero data rows, halt and report that the
        dataset is empty; do not return a null_report or null_count of zero
        without flagging this as anomalous.
      extra_nulls_discovered: If actual_spend nulls beyond the five known rows
        are found, include all of them in null_report and update null_count
        accordingly; never silently drop undocumented nulls.
      null_without_notes: If a null actual_spend row has no corresponding notes
        value, include the row in null_report with null_reason set to
        "no reason provided" and flag it for operator review.

  - name: compute_growth
    description: Accepts a single ward, a single category, and an explicit
      growth type, then returns a per-period growth table with the formula used
      printed alongside every computed value and null rows flagged rather than
      computed.
    input:
      type: object
      format: |
        {
          "data": array of row objects returned by load_dataset (required),
          "ward": "exact ward string e.g. Ward 1 – Kasba",
          "category": "exact category string e.g. Roads & Pothole Repair",
          "growth_type": "MoM or YoY"
        }
    output:
      type: object
      format: |
        {
          "ward": "string",
          "category": "string",
          "growth_type": "MoM or YoY",
          "rows": [
            {
              "period": "YYYY-MM",
              "actual_spend": float or null,
              "growth_value": float or null,
              "formula_used": "string e.g. (19.7 - 14.8) / 14.8 * 100" or null,
              "null_flag": boolean,
              "null_reason": "string or null"
            }
          ]
        }
    error_handling:
      growth_type_missing: If growth_type is not supplied or is any value other
        than MoM or YoY, refuse to execute, return an error asking the caller
        to specify growth_type explicitly, and never default to either option.
      ward_not_found: If the supplied ward string does not match any ward in the
        dataset, return an error listing the five valid ward names; do not
        compute on a partial or fuzzy match.
      category_not_found: If the supplied category string does not match any
        category in the dataset, return an error listing the five valid category
        names; do not compute on a partial or fuzzy match.
      null_row_encountered: For every row where actual_spend is null, set
        growth_value to null, formula_used to null, and null_flag to true with
        null_reason populated from the notes column; never interpolate, zero-
        fill, or skip the row.
      previous_period_null: If the immediately preceding period required for MoM
        calculation is itself a null row, set the current row growth_value to
        null, formula_used to null, and null_flag to true with null_reason
        stating "prior period is null"; never divide by or subtract a null value.
      aggregation_attempted: If ward or category is passed as a wildcard, "all",
        or any value that would cause computation across multiple wards or
        categories, refuse immediately and return an error stating that cross-
        ward and cross-category aggregation is not permitted.
      insufficient_periods: If fewer than two non-null periods exist for the
        given ward and category, return an error stating growth cannot be
        computed with fewer than two data points; do not return a partial table.