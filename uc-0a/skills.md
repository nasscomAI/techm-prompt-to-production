skills:
  - name: classify_complaint
    description: Classify a single citizen complaint into a category and priority level based on RICE rules.
    input: Dictionary containing 'complaint_id' and 'description'.
    output: Dictionary with keys 'complaint_id', 'category', 'priority', 'reason', 'flag'.
    error_handling: Return 'Other' and 'NEEDS_REVIEW' if the description is null or category cannot be safely determined.

  - name: batch_classify
    description: Read a CSV of complaints and process each row through the classify_complaint skill, then write to an output CSV.
    input: Path to Input CSV and Path to Output CSV.
    output: None (writes to file).
    error_handling: Catch row-level errors and ensure the process continues for remaining rows; flag nulls.
