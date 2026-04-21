# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single complaint row by analyzing the description to assign category, priority, reason, and flag according to the enforcement rules.
    input: A dictionary representing a complaint row, containing at least a 'description' key with the complaint text.
    output: A dictionary with keys 'complaint_id', 'category', 'priority', 'reason', 'flag', where category is from the allowed list, priority is Urgent/Standard, reason cites words, and flag is NEEDS_REVIEW if ambiguous.
    error_handling: If the input is invalid or description is missing/empty, output category as 'Other', priority as 'Standard', reason explaining the issue, and flag as 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads a CSV file of complaints, applies classify_complaint to each row, and writes the results to a new CSV file.
    input: Two string paths - input_path to the CSV file and output_path for the results CSV.
    output: Writes a CSV file with columns complaint_id, category, priority, reason, flag for each row; prints a success message.
    error_handling: Handles file read/write errors by printing error messages; for bad rows, applies classify_complaint's error handling and continues processing other rows without crashing.
