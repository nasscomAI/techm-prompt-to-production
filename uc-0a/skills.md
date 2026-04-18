# skills.md — UC-0A Complaint Classifier Skills

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row into a category and priority level with a cited reason.
    input: A single row of complaint data containing fields like description, location, and city.
    output: A structured object or row containing 'category', 'priority', 'reason', and 'flag'.
    error_handling: If the description is missing or empty, assign category 'Other' and set flag 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Processes a CSV file of complaints and generates a new CSV with classification results.
    input: Path to an input CSV file (e.g., `../data/city-test-files/test_pune.csv`).
    output: Generates an output CSV file (e.g., `results_pune.csv`) containing the original data plus classification columns.
    error_handling: Validates file existence and CSV format; skips malformed rows while logging the error.
