# skills.md — UC-0A Complaint Classifier

skills:
  - name: classify_complaint
    description: >
      Classifies a single citizen complaint row into one of the 10 allowed categories,
      assigns a priority level (Urgent/Standard/Low) based on severity keywords, and
      returns a reason sentence citing specific words from the description, plus a
      NEEDS_REVIEW flag if the category is ambiguous.
    input: >
      dict — a single CSV row with at minimum a 'description' field (string).
      Additional fields (e.g. complaint_id, ward, date) may be present but must not
      influence classification.
    output: >
      dict with exactly four keys:
        - complaint_id (string): passed through from input, or generated if missing
        - category (string): exactly one of: Pothole, Flooding, Streetlight, Waste,
          Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other
        - priority (string): Urgent | Standard | Low
        - reason (string): one sentence citing specific words from the description
        - flag (string): "NEEDS_REVIEW" if ambiguous, else empty string ""
    error_handling: >
      - If 'description' field is missing or empty: return category=Other, priority=Low,
        reason="No description provided", flag=NEEDS_REVIEW.
      - If description text maps to multiple categories with equal confidence: return
        category=Other, flag=NEEDS_REVIEW, and note ambiguous terms in reason.
      - Never raise an exception for a single row — always return a valid dict.
      - Never invent a category outside the 10 allowed values, even if no category fits well.

  - name: batch_classify
    description: >
      Reads an input CSV of citizen complaints (with the 'category' and 'priority_flag'
      columns stripped), applies classify_complaint to each row, and writes the
      classified results to an output CSV.
    input: >
      Two file path strings:
        - input_path (str): absolute or relative path to the input CSV file
          (columns include at minimum: complaint_id, description)
        - output_path (str): path where the results CSV will be written
    output: >
      A CSV file written to output_path containing all original input columns plus:
        - category (string)
        - priority (string)
        - reason (string)
        - flag (string)
      One row per input complaint. Rows that fail classification individually are still
      written with error-safe defaults (category=Other, flag=NEEDS_REVIEW) rather than
      being dropped.
    error_handling: >
      - If input_path does not exist: print a clear error message and exit with a
        non-zero code. Do not create an empty output file.
      - If a required column (e.g. 'description') is missing from the CSV header:
        print a column-missing error and exit.
      - If an individual row fails to classify (e.g. encoding error, null values):
        log the row number and error, write that row with defaults, and continue
        processing remaining rows — never crash the entire batch.
      - If output directory does not exist: attempt to create it; if creation fails,
        print a clear error and exit.
      - Print a summary on completion: total rows processed, Urgent count, rows flagged
        NEEDS_REVIEW, and path of the output file.
