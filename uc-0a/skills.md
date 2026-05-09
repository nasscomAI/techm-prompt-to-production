        1# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classify_complaint
    description: Classifies a complaint into a category with an associated priority and reason.
    input: A single complaint row as a dict containing a 'description' field.
    output: A dict containing the fields 'category', 'priority', 'reason', and 'flag'.
    error_handling: Sets 'NEEDS_REVIEW' flag when the category is ambiguous or if there is insufficient information.

  - name: batch_classify
    description: Batch processes CSV files of complaints, classifying each complaint and writing the results to a new CSV file.
    input: `input_path` as a string for the input CSV file location.
    output: `output_path` as a string for the output CSV file location.
    error_handling: Does not crash on bad rows in the input CSV; marks problematic rows with 'NEEDS_REVIEW' in the output CSV.
