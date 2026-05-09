# skills.md

skills:
  - name: classify_complaint
    description: Classify a single complaint row into category, priority, reason, and flag according to the UC-0A schema.
    input: A complaint row object or dictionary with the complaint description and any related fields from the input CSV.
    output: A dictionary containing:
      - category: one of the allowed UC-0A categories
      - priority: Urgent, Standard, or Low
      - reason: one sentence citing specific words from the description
      - flag: NEEDS_REVIEW or blank
    error_handling: If the description is missing, unclear, or ambiguous, return category Other, flag NEEDS_REVIEW, and a reason noting the lack of determinative information.

  - name: batch_classify
    description: Read an input CSV, apply classify_complaint to each row, and write an output CSV with the required UC-0A fields.
    input: Path to an input CSV file and a target output CSV file path, or a list of complaint rows.
    output: A completed output CSV file or list of classified rows with category, priority, reason, and flag added.
    error_handling: If a row is invalid, skip or preserve it with category Other and flag NEEDS_REVIEW, and log the issue for later review.
