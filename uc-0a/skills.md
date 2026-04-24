skills:
  - name: classify_complaint
    description: Analyzes a single citizen complaint to determine its category and priority according to predefined rules.
    input: dictionary (a single row from CSV containing 'complaint_id', 'description', etc.)
    output: dictionary containing exactly 'complaint_id', 'category', 'priority', 'reason', and 'flag'.
    error_handling: Return category 'Other' and set flag to 'NEEDS_REVIEW' if the input description is blank or ambiguous. Do not throw an exception.

  - name: batch_classify
    description: Reads a batch of complaints from a CSV file, applies the classify_complaint skill to each row, and writes the results to a new output CSV file.
    input: file_path (string to the input CSV), output_path (string to the output CSV)
    output: Writes a CSV file containing columns: 'complaint_id', 'category', 'priority', 'reason', and 'flag'. Returns None.
    error_handling: Must not crash on malformed individual rows; instead continue processing other rows while setting 'NEEDS_REVIEW' flag for the bad rows. Must alert if the input file cannot be opened.
