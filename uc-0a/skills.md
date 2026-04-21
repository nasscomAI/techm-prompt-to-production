# skills.md

skills:
  - name: classify_complaint
    description: Analyzes a single citizen complaint to determine its category, priority, reason, and whether it requires human review.
    input: A single complaint row as a dictionary containing at least a 'description' field (string).
    output: A dictionary containing 'complaint_id', 'category' (string enum), 'priority' (string enum), 'reason' (string), and 'flag' (string).
    error_handling: If the description is missing or empty, defaults to category 'Other', priority 'Standard', and flags as 'NEEDS_REVIEW' due to insufficient data. If multiple specific, non-overlapping categories match, flags the output as 'NEEDS_REVIEW' and defaults to the first matched category in the hierarchy.

  - name: batch_classify
    description: Processes a batch of complaints from a CSV file by applying the classify_complaint skill to each row and writing the results to a new CSV file.
    input: 'input_path' (string path to the source CSV) and 'output_path' (string path to the destination CSV).
    output: A CSV file generated at 'output_path' containing the original data appended with the classified fields.
    error_handling: Handles rows gracefully by returning the classified data to ensure the batch process does not crash. Produces a valid output file even if some rows contain anomalous data.
