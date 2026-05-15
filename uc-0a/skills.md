# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint based on its text description into a predefined category and priority, extracting a specific reason.
    input: Dictionary containing the row data, including a 'description' string.
    output: Dictionary with keys 'complaint_id', 'category', 'priority', 'reason', and 'flag'.
    error_handling: If input description is missing, empty, or unparseable, output category as 'Other', priority as 'Standard', and flag as 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads a CSV file of complaints, applies the classify_complaint skill to each row, and writes the results to a new CSV file.
    input: String input_path to the input CSV and String output_path for the output CSV.
    output: None (writes a CSV file to disk).
    error_handling: Must flag nulls, skip completely malformed rows without crashing, and continue processing the rest of the valid rows to ensure partial output is generated.
