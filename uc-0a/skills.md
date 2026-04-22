# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classify_complaint
    description: Classifies a single complaint row into category, priority, reason, and flag according to the UC-0A schema.
    input: A dictionary representing one complaint row from the input CSV, including at minimum complaint_id and description fields, and any other metadata columns     present.
    output: A dictionary with keys: complaint_id, category, priority, reason, flag. category is one of the allowed category strings, priority is Urgent, Standard, or Low, reason is a one-sentence string citing words from the description, and flag is either NEEDS_REVIEW or blank.
    error_handling: If required fields like description or complaint_id are missing or empty, return category: Other, priority: Standard, a reason explicitly stating that required information is missing, and flag: NEEDS_REVIEW. If the description is too ambiguous to assign a clear category, set category: Other and flag: NEEDS_REVIEW.

  - name: batch_classify
    description: Reads the input CSV, applies classify_complaint to each row, and writes the results CSV with the required schema.
    input: Two file paths: input_path to the test_[city].csv file and output_path where results_[city].csv should be written.
    output: A CSV file at output_path with one row per input complaint and columns: complaint_id, category, priority, reason, flag. Returns nothing from the function.
    error_handling: If the input CSV cannot be read, raise a clear exception. If individual rows are malformed, log or skip them without crashing, and still produce an output CSV for all valid rows; ambiguous rows should be classified as category: Other with flag: NEEDS_REVIEW.
