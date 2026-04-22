# skills.md

skills:
  - name: classify_complaint
    description: Analyzes a single complaint description to determine its category, priority, and justification based on strict predefined rules.
    input: dictionary containing complaint details, specifically 'description' and 'complaint_id'.
    output: dictionary containing 'complaint_id', 'category', 'priority', 'reason', and 'flag'.
    error_handling: If the category is ambiguous or keywords for specific categories are missing, sets category to 'Other' and flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Processes an input CSV of complaints, applying the classification logic to each row and writing the results to an output CSV.
    input: file path to the input CSV and file path for the output CSV.
    output: Success message indicating the output file path.
    error_handling: Skips rows with missing essential data and ensures the process continues even if individual classifications encounter issues.
