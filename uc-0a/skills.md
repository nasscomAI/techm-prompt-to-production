# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.
 
skills:
  - name: classify_complaint
    description: Classify a single citizen complaint row into category, priority, reason, and flag.
    input: A CSV row (or JSON object) with fields `description` (string) representing the complaint text.
    output: An object containing `category` (one of the allowed categories), `priority` (Urgent/Standard/Low), `reason` (one sentence citing keywords), and `flag` (NEEDS_REVIEW or empty).
    error_handling: If the description is empty or ambiguous beyond rule set, set category to `Other` and flag to `NEEDS_REVIEW`.
 
  - name: batch_classify
    description: Process an input CSV file, applying classify_complaint to each row and writing results to an output CSV.
    input: Paths to input CSV file (with complaint descriptions) and desired output CSV file.
    output: Output CSV file with original rows plus columns `category`, `priority`, `reason`, `flag` per row.
    error_handling: Skips rows with missing descriptions, logs them, and assigns `Other`/`NEEDS_REVIEW` for those rows.