skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row into category, priority, reason, and flag using the municipal schema.
    input: A dict with at minimum a 'complaint_id' string and a 'description' string.
    output: A dict with keys complaint_id, category (exactly one of the 10 allowed values), priority (Urgent/Standard/Low), reason (one sentence citing specific words from the description), flag (NEEDS_REVIEW or blank string).
    error_handling: If description is empty or None, returns category Other, priority Low, reason "No description provided.", flag NEEDS_REVIEW. If the API response cannot be parsed or returns a disallowed category, falls back to Other with flag NEEDS_REVIEW.

  - name: batch_classify
    description: Reads an input CSV of complaints, applies classify_complaint to each row, and writes a results CSV.
    input: input_path (str) pointing to a CSV with columns including complaint_id and description; output_path (str) for the results file.
    output: A CSV file at output_path with columns complaint_id, category, priority, reason, flag — one row per input row.
    error_handling: Rows with missing descriptions are flagged NEEDS_REVIEW without crashing. Individual row API failures are caught, logged to stderr, and written as NEEDS_REVIEW rows so the batch always completes.
