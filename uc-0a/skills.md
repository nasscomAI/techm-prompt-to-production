# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint into category, priority, reason, and flag
    input: JSON object with 'description' (string) field containing complaint text
    output: JSON object with 'category' (string), 'priority' (string), 'reason' (string), 'flag' (string or null)
    error_handling: If category cannot be determined from description, set category to 'Other' and flag to 'NEEDS_REVIEW'

  - name: batch_classify
    description: Reads input CSV, applies classify_complaint to each row, writes output CSV
    input: Path to input CSV file with 'description' column, path to output CSV file
    output: CSV file with 'category', 'priority', 'reason', 'flag' columns added
    error_handling: Skip rows with missing description, log warning, continue processing remaining rows