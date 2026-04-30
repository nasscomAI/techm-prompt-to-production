# skills.md

skills:
  - name: classify_complaint
    description: Classify a single citizen complaint row by determining its category, priority, reason, and flag.
    input: A single complaint row containing a description of the issue.
    output: A dictionary or object containing the determined `category`, `priority`, `reason`, and `flag`.
    error_handling: If the complaint description is genuinely ambiguous, assign a flag of `NEEDS_REVIEW` and choose the most likely category or 'Other'.

  - name: batch_classify
    description: Read an input CSV of complaints, apply the `classify_complaint` skill to each row, and write the output to a CSV file.
    input: An input file path (CSV) and an output file path (CSV).
    output: A new CSV file at the output path containing the classified complaints.
    error_handling: Flag null descriptions, ignore malformed rows without crashing, and ensure output is written even if some rows fail processing.
