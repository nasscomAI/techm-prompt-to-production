skills:
  - name: classify_complaint
    description: Classifies one citizen complaint into the approved UC-0A category and priority schema with evidence.
    input: A CSV row as a dictionary containing complaint_id and description, with other fields ignored unless needed for traceability.
    output: A dictionary with complaint_id, category, priority, reason, and flag.
    error_handling: Missing or unclear descriptions return category Other, Standard priority, a reason explaining the missing signal, and flag NEEDS_REVIEW.

  - name: batch_classify
    description: Reads a city complaint CSV, applies classify_complaint to each row, and writes the UC-0A results CSV.
    input: Input CSV path and output CSV path.
    output: A CSV file with header complaint_id, category, priority, reason, and flag.
    error_handling: Continues processing if an individual row fails, writes that row as Other with flag NEEDS_REVIEW, and does not crash the whole batch.
