skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row into category, priority, reason, and flag using the enforcement rules defined in agents.md.
    input: >
      A dict representing one CSV row with keys: complaint_id, date_raised, city,
      ward, location, description, reported_by, days_open. The description field
      is the primary input for classification.
    output: >
      A dict with exactly four keys:
        - category: one of Pothole · Flooding · Streetlight · Waste · Noise · Road Damage · Heritage Damage · Heat Hazard · Drain Blockage · Other
        - priority: one of Urgent · Standard · Low
        - reason: one sentence citing specific words from the description
        - flag: "NEEDS_REVIEW" or blank string
    error_handling: >
      If description is missing or empty, set category: Other, priority: Standard,
      reason: "Description field is empty — cannot classify.", flag: NEEDS_REVIEW.
      Never raise an exception; always return a valid output dict.

  - name: batch_classify
    description: Reads an input CSV of complaint rows, applies classify_complaint to each row, and writes a results CSV with the original fields plus classification output.
    input: >
      Two file paths as strings:
        - input_path: path to a CSV file with columns complaint_id, date_raised, city,
          ward, location, description, reported_by, days_open
        - output_path: path where the results CSV will be written
    output: >
      A CSV file at output_path containing all original columns plus:
      category, priority, reason, flag. One row per input complaint.
      Rows that fail classification are written with category: Other,
      priority: Standard, and flag: NEEDS_REVIEW rather than being skipped.
    error_handling: >
      If a row is malformed or missing required fields, write it to output with
      flag: NEEDS_REVIEW and a reason explaining the issue. If the input file
      cannot be read, raise FileNotFoundError with a clear message. Never silently
      drop rows — output row count must equal input row count.
