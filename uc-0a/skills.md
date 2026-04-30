# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single complaint into a category, priority, reason, and flag based on description content.
    input: A dictionary containing 'description' and other complaint details.
    output: A dictionary with 'category', 'priority', 'reason', and 'flag'.
    error_handling: Defaults to 'Other' category and 'NEEDS_REVIEW' flag if classification is ambiguous or fails.

  - name: batch_classify
    description: Reads complaints from an input CSV, applies classify_complaint to each row, and writes results to an output CSV.
    input: Path to input CSV file and path to output CSV file.
    output: CSV file containing original data plus classification columns.
    error_handling: Skips rows with missing descriptions and logs errors while processing the rest of the batch.
