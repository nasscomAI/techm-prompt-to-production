# skills.md — UC-0A Complaint Classifier Skills

skills:
  - name: classify_complaint
    description: Classifies a single complaint row by extracting category, priority, justification reason, and review flag from the complaint description using the standardized taxonomy.
    input: "Dictionary with keys: complaint_id (str), description (str). Description is the complaint text to be classified."
    output: "Dictionary with keys: category (str - one of the 10 allowed values), priority (str - Urgent/Standard/Low), reason (str - one sentence citing specific description words), flag (str - NEEDS_REVIEW or empty string)"
    error_handling: "If the description is empty or unclassifiable, output category as Other with flag NEEDS_REVIEW and reason as 'Insufficient information to classify complaint.' If multiple categories apply equally, output category as Other with flag NEEDS_REVIEW and reason explaining the ambiguity."

  - name: batch_classify
    description: Reads complaint CSV file, applies classify_complaint skill to each row, and writes structured output CSV with classifications, priorities, reasons, and review flags.
    input: "Path to input CSV file with columns: complaint_id, date_raised, city, ward, location, description, reported_by, days_open"
    output: "CSV file written to specified output path with columns: complaint_id, date_raised, city, ward, location, description, reported_by, days_open, category, priority, reason, flag"
    error_handling: "If input file cannot be read, raise error with file path. If output path is not writable, raise error. If a row fails classification, output category as Other, flag as NEEDS_REVIEW, and reason as error message."
