# skills.md — UC-0A Complaint Classifier

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row into category, priority, reason, and flag.
    input: A single complaint record containing a text description field (string).
    output: A dict with four fields — category (string, one of the ten allowed values),
      priority (Urgent / Standard / Low), reason (one sentence citing words from the
      description), and flag (NEEDS_REVIEW or blank string).
    error_handling: If the description is empty or unparseable, output category: Other,
      priority: Low, reason: "Description could not be parsed.", flag: NEEDS_REVIEW.
      If the category is ambiguous but a description is present, output the best-fit
      category and set flag: NEEDS_REVIEW.

  - name: batch_classify
    description: Reads an input CSV of complaint rows, applies classify_complaint to each row, and writes the results to an output CSV.
    input: Path to a CSV file (string) with at least a description column; rows may contain
      additional metadata columns that must be preserved in output.
    output: A CSV file written to the specified output path containing all original columns
      plus the four classification fields (category, priority, reason, flag).
    error_handling: If the input file is missing or malformed, raise a descriptive error
      and exit without writing output. Rows where classify_complaint returns NEEDS_REVIEW
      are included in the output file with the flag set; processing continues for all rows.
