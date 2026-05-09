# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classify_complaint
    description: Classifies one complaint into category and priority.
    input: Dictionary row from CSV containing complaint text.
    output: Dictionary with complaint_id, category, priority, reason, flag.
    error_handling: If complaint text is missing or unclear, return category=Other and flag=NEEDS_REVIEW.

  - name: batch_classify
    description: Reads input CSV, applies complaint classification, writes output CSV.
    input: Input CSV file path.
    output: Output CSV file path.
    error_handling: Skip bad rows without crashing and continue processing.