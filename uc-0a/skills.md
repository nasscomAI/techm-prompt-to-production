skills:
  - name: classify_complaint
    description: Processes a single citizen complaint row and classifies it, returning category, priority, reason, and flag fields.
    input: A single complaint row (usually containing a description).
    output: Structured classification containing category, priority, reason, and flag according to the schema.
    error_handling: Flags as NEEDS_REVIEW if the text is entirely indecipherable or genuinely ambiguous.

  - name: batch_classify
    description: Reads an input CSV file containing multiple complaints, applies the classify_complaint skill to each row, and writes the results to an output CSV file.
    input: File path to the input CSV (e.g., ../data/city-test-files/test_[your-city].csv).
    output: A completed output CSV file (e.g., results_[your-city].csv) containing all processed rows with their classifications.
    error_handling: Skips malformed rows and logs the error, continuing batch processing.
