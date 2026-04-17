# skills.md

skills:
  - name: classify_complaint
    description: Classify a single citizen complaint by category, priority, and justification, applying R.I.C.E enforcement rules to ensure taxonomy compliance and ambiguity detection.
    input: |
      Single complaint object with:
      - id: unique identifier (string)
      - description: complaint text (string, one or more sentences)
      - ward: ward/geographic metadata (string, optional)
    output: |
      Classification object with:
      - id: echoed from input
      - category: one of {Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other}
      - priority: one of {Urgent, Standard, Low}
      - reason: single sentence citing specific words from the complaint description
      - flag: "NEEDS_REVIEW" if ambiguous, empty string if unambiguous
    error_handling: |
      If complaint text is too vague to determine any category: set category to "Other", flag to "NEEDS_REVIEW", and reason to "Insufficient detail in complaint description".
      If multiple categories genuinely apply: set flag to "NEEDS_REVIEW" and reason to explain both applicable categories.
      If severity keywords present but priority not set to Urgent: refuse and return error — this is a classification error.

  - name: batch_classify
    description: Read a CSV file of complaints, apply classify_complaint to each row, and write results to output CSV ensuring consistent category/priority values across all rows.
    input: |
      Parameters:
      - input_file: path to input CSV (string) with columns [id, description, ward, ...]
      - output_file: path for output CSV (string)
    output: |
      CSV file with columns [id, category, priority, reason, flag] containing classified complaints.
      All rows processed; rows with flag="NEEDS_REVIEW" logged to stderr but included in output.
    error_handling: |
      If input CSV is malformed or missing required columns: log error and halt with message indicating which rows failed to parse.
      If duplicate category names appear across rows for similar complaints: log warning indicating which rows have inconsistency; do not stop processing.
      If any row fails classification (no category can be assigned): output that row with flag="NEEDS_REVIEW" and category="Other"; continue processing remaining rows.
      After batch completion, report total rows processed, rows flagged for review, and count per category for audit.
