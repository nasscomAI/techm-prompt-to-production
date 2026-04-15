# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint based on its description text into a category, priority level, and reason.
    input: Object containing the complaint description (string).
    output: Object containing category (string), priority (string), reason (string), and flag (string).
    error_handling: If the description is ambiguous or category cannot be certain, sets category to 'Other' and flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Processes a batch of citizen complaints from an input CSV file and writes the results to an output CSV file.
    input: Path to the input CSV file containing citizen complaints.
    output: Path to the output CSV file with classification results.
    error_handling: Continues processing if individual rows fail, marking them with 'NEEDS_REVIEW' where applicable.

