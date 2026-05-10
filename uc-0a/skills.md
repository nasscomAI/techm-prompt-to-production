skills:
  - name: classify_complaint
    description: Receives a single citizen complaint row and returns the appropriate category, priority, reason, and flag out.
    input: A single citizen complaint row (text format) containing the description.
    output: A structured object with exact fields for category, priority, reason, and flag.
    error_handling: Return category "Other", flag "NEEDS_REVIEW", and state the conflicting or ambiguous factors in the reason if the description is unclear.

  - name: batch_classify
    description: Reads an input CSV of complaints, applies classify_complaint to each row individually, and writes an output CSV.
    input: Path to the input CSV file.
    output: Writes results to the specified output CSV path.
    error_handling: If input is invalid or ambiguous, log the error and continue to the next row, setting category to "Other" and flag to "NEEDS_REVIEW" if classification fails.
