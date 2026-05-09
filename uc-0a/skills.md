skills:
  - name: classify_complaint
    description: Classify a single complaint row into the UC-0A schema.
    input: A single complaint row object or record containing the complaint description and any other relevant row fields.
    output: An object with exact category, priority, reason, and flag values.
    error_handling: If input is invalid or missing description, return an error or fallback with category Other and flag NEEDS_REVIEW; if complaint is ambiguous, set flag to NEEDS_REVIEW and avoid overconfident categorization.

  - name: batch_classify
    description: Read an input CSV of complaint rows and apply classify_complaint to each row.
    input: A path to a CSV file with complaint rows, where category and priority_flag are stripped.
    output: A CSV file written to the specified output path containing category, priority, reason, and flag for each row.
    error_handling: If the input CSV is invalid or unreadable, return an error; for invalid rows, mark them with category Other and flag NEEDS_REVIEW while processing other rows normally.
