# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single complaint row by extracting category, priority, reason, and ambiguity flag.
    input: "Dict with keys: description (str). Must contain a non-empty complaint description."
    output: "Dict with keys: category (str, one of allowed taxonomy), priority (Urgent/Standard/Low), reason (str, one sentence), flag (str, NEEDS_REVIEW or blank)."
    error_handling: "If description is empty or unparseable, return category: Other, priority: Standard, reason: Unable to classify, flag: NEEDS_REVIEW."

  - name: batch_classify
    description: Reads input CSV, applies classify_complaint to each row, writes output CSV with classification results.
    input: "Path to CSV file with column: description. Path to output file (str)."
    output: "CSV file written to output path with columns: category, priority, reason, flag."
    error_handling: "If input file does not exist or is malformed, raise error with file path and row number. If output path is not writable, raise error with path."
