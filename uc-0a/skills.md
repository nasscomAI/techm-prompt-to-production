# skills.md

skills:
  - name: classify_complaint
    description: Classify a single complaint row by extracting category, priority, reason, and review flag from the complaint description.
    input: dict with keys {complaint_id, description, location} (from CSV row).
    output: dict with keys {complaint_id, category, priority, reason, flag}. All keys always present; flag may be empty string.
    error_handling: If description is empty or null, category=Other, reason="No description provided", flag=NEEDS_REVIEW. If description does not match any category clearly, category=Other, flag=NEEDS_REVIEW.

  - name: batch_classify
    description: Read input CSV file, apply classify_complaint to each row, write results to output CSV with category, priority, reason, flag columns appended.
    input: input_path (str, path to CSV with complaint_id and description columns), output_path (str, path to write results).
    output: None (writes CSV file). Output file contains all input columns plus category, priority, reason, flag columns.
    error_handling: Gracefully skip rows with parsing errors and log to stderr. Continue processing remaining rows. Write partial output even if some rows fail. Do not crash on malformed CSV or null descriptions.
