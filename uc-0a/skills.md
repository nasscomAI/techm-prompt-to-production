# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint row into category, priority, reason, and flag based on the description text and severity triggers.
    input: "A dictionary representing a single complaint row (must contain a 'description' field)."
    output: "A dictionary containing: category (string from allowed list), priority (Urgent|Standard|Low), reason (single sentence citing words), and flag (NEEDS_REVIEW or blank)."
    error_handling: "If category is ambiguous or category names vary from the allowed list, return category: 'Other' and set flag: 'NEEDS_REVIEW'."

  - name: batch_classify
    description: Reads an input CSV file, applies the classify_complaint skill to each row, and writes the resulting classification fields to an output CSV file.
    input: "input_path (string): Path to the test_[city].csv file."
    output: "output_path (string): Path to the results_[city].csv file."
    error_handling: "Ensure the process does not crash on malformed rows; rows that cannot be processed should be logged and output with 'NEEDS_REVIEW' flag."
