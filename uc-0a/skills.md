skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row into category, priority, reason, and flag fields.
    input: A dictionary representing one CSV row with at minimum a "description" and "complaint_id" key.
    output: A dictionary with keys: complaint_id (string), category (one of 10 allowed values), priority (Urgent or Standard), reason (one sentence citing description keywords), flag (NEEDS_REVIEW or blank string).
    error_handling: If the description is empty or missing, returns category Other, priority Standard, reason stating no description, flag NEEDS_REVIEW. If an unexpected error occurs during classification, returns category Other, priority Standard, reason with error text, flag NEEDS_REVIEW.

  - name: batch_classify
    description: Reads an input CSV of complaints, applies classify_complaint to each row, and writes a results CSV.
    input: Path to an input CSV file (with headers: complaint_id, description, etc.) and a path for the output CSV.
    output: A CSV file with columns: complaint_id, category, priority, reason, flag. One row per input complaint.
    error_handling: If any individual row fails classification, that row is written to the output with category Other, flag NEEDS_REVIEW, and the error message in reason. The batch continues processing remaining rows. If the input file cannot be opened, the function raises the exception to the caller.
