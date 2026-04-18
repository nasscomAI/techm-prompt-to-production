skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row to output a category, priority, reason, and flag.
    input: String description of the citizen complaint.
    output: Dictionary containing category (string), priority (string), reason (string), and flag (string).
    error_handling: If the category is genuinely ambiguous, set the flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads an input CSV of complaints, applies classify_complaint to each row, and writes the results to an output CSV.
    input: File path to the input CSV containing complaints.
    output: File path to the output CSV containing classified complaints.
    error_handling: If a row is malformed or missing, log an error and continue to the next row.
