skills:

- name: classify_complaint
  description: Classify a single complaint row into category, priority, reason, and flag fields according to RICE enforcement rules.
  input: Python dict with keys complaint_id and description (both strings).
  output: Python dict with keys complaint_id, category, priority, reason, flag (all strings; flag empty string if not NEEDS_REVIEW).
  error_handling: If description is empty or null, set category to Other and flag to NEEDS_REVIEW. If classification is ambiguous, always flag NEEDS_REVIEW. Do not return null or missing fields.

- name: batch_classify
  description: Read all complaint rows from input CSV, apply classify_complaint to each, and write results to output CSV.
  input: File path to input CSV with columns complaint_id, description; file path to output CSV to write (will be created or overwritten).
  output: CSV file with columns complaint_id, category, priority, reason, flag; prints summary of rows processed and flagged.
  error_handling: Skip rows with missing complaint_id or description but log them. Write all rows that can be classified, even if some fail. If file I/O fails, raise exception with clear message. Do not crash on individual row parsing errors.
