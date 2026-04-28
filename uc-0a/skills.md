# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint into category and priority based on the description.
    input: A dictionary representing a complaint row with keys including 'description' and 'complaint_id'.
    output: A dictionary with keys 'complaint_id', 'category', 'priority', 'reason', 'flag'.
    error_handling: If description is missing or empty, sets category to 'Other', priority to 'Low', reason to 'No description provided', flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Processes a CSV file of complaints, classifies each one, and writes the results to a new CSV.
    input: Input file path (string) and output file path (string).
    output: None (writes to file), prints completion message.
    error_handling: Skips rows with missing required fields, writes partial results, does not crash on bad data.
