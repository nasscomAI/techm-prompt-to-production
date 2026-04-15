# skills.md

skills:
  - name: classify_complaint
    description: Classify a single complaint row into category, priority, reason, and flag.
    input: Dictionary with 'complaint_id', 'description', and other fields.
    output: Dictionary with 'complaint_id', 'category', 'priority', 'reason', and 'flag'.
    error_handling: Return category 'Other', flag 'NEEDS_REVIEW' and reason 'Parsing error' if classification fails.

  - name: batch_classify
    description: Read an input CSV file, apply classify_complaint per row, and write an output CSV.
    input: String input_path and String output_path.
    output: None (writes a CSV file to output_path).
    error_handling: Skips malformed rows, logs errors, and continues processing the rest of the file.
