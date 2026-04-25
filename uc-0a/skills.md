# skills.md

skills:
  - name: classify_complaint
    description: Analyzes a single citizen complaint description to determine its category, priority, and justification.
    input: A string containing the complaint description.
    output: A structured object containing category, priority, reason (citing specific words), and a flag for ambiguity.
    error_handling: If the category is ambiguous or cannot be determined, it assigns 'Other' and sets the 'NEEDS_REVIEW' flag.

  - name: batch_classify
    description: Processes multiple complaints from a CSV file and writes the results to a new CSV file.
    input: An input CSV file path containing a 'description' column.
    output: An output CSV file path containing the original description plus category, priority, reason, and flag columns.
    error_handling: Handles file I/O errors and ensures each row is processed through classify_complaint, even if individual rows fail.
