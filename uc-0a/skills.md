# skills.md — UC-0A Complaint Classifier

skills:
  - name: classify_complaint
    description: Classifies a single complaint dict into category, priority, reason, and flag using rule-based enforcement against the approved taxonomy.
    input: dict with at minimum complaint_id (str) and description (str)
    output: dict with keys complaint_id, category (one of 10 exact values), priority (Urgent/Standard/Low), reason (str citing words from description), flag (NEEDS_REVIEW or blank)
    error_handling: Returns category=Other, priority=Standard, flag=NEEDS_REVIEW with reason explaining the issue when description is empty, null, or classification fails

  - name: batch_classify
    description: Reads an input CSV, applies classify_complaint to every row, and writes a results CSV; never crashes on bad rows and always produces output.
    input: input_path (str, path to city test CSV), output_path (str, path for results CSV)
    output: writes CSV with columns complaint_id, category, priority, reason, flag; prints row count and output path to stdout; bad rows written with NEEDS_REVIEW flag
    error_handling: Wraps each row in try/except; failed rows get category=Other, flag=NEEDS_REVIEW, error message in reason field; errors logged to stderr; execution continues to next row
