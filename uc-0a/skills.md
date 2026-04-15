# skills.md

skills:
  - name: classify_complaint
    description: Processes one complaint row to determine its category, priority, reason, and review flag.
    input: Single row containing a citizen complaint description (Dictionary/Row).
    output: Classified output containing category, priority, reason, and flag (Dictionary/Record).
    error_handling: If the complaint description is ambiguous, it assigns the best match or 'Other' and sets the flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads an input CSV of citizen complaints, applies the classify_complaint skill per row, and writes the results to an output CSV.
    input: Input CSV file path containing the dataset of complaints (String).
    output: Writes out a CSV file to the output path containing the classified results.
    error_handling: If a row is missing essential fields, it notes the failure in the output file and continues processing other rows.
