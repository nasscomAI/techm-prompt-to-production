# skills.md — UC-0A Complaint Classifier

skills:
  - name: classify_complaint
    description: Analyzes a single citizen complaint description and determines its category, priority, reason, and review flag.
    input: One complaint row containing at least a text description.
    output: category (exact string), priority (Urgent/Standard/Low), reason (one sentence citing specific words), and flag (NEEDS_REVIEW or blank).
    error_handling: If the complaint description is genuinely ambiguous, set the flag to 'NEEDS_REVIEW' instead of guessing with false confidence.

  - name: batch_classify
    description: Reads a batch of complaints from an input CSV, applies classify_complaint to each row, and writes the results to an output CSV.
    input: Path to the input CSV file (e.g., `../data/city-test-files/test_[city].csv`).
    output: Path to the output CSV file (e.g., `uc-0a/results_[city].csv`) containing the original data plus the new classification columns.
    error_handling: Handle file not found errors, and gracefully process empty descriptions by classifying them as 'Other' with a 'NEEDS_REVIEW' flag.
