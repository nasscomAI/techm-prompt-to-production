# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint based on its description into category, priority, reason, and flag.
    input: A dictionary row containing complaint details, including the 'description' field as a string.
    output: A dictionary with keys 'complaint_id', 'category', 'priority', 'reason', 'flag'.
    error_handling: If the description is empty or invalid, set category to 'Other', priority to 'Low', reason to 'Invalid description', flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads a CSV file of complaints, classifies each row using classify_complaint, and writes the results to a new CSV file.
    input: Input CSV file path (string) and output CSV file path (string).
    output: None (writes to file); prints completion message.
    error_handling: Skips invalid rows, logs errors, but continues processing; ensures output file is created even if some rows fail.
