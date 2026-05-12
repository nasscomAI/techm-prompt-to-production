skills:
  - name: classify_complaint
    description: Classifies a single civic complaint description into category, priority, reason, and flag according to the defined schema.
    input:
      type: object
      format: JSON object with at least a "description" field containing the complaint text
    output:
      type: object
      format: JSON object with fields category (string), priority (string), reason (one sentence string), flag (string or empty)
    error_handling:
      - If description is missing or empty, return category as Other, priority as Low, reason stating no valid description provided, and flag as NEEDS_REVIEW
      - If complaint does not clearly match any allowed category, assign category as Other and set flag to NEEDS_REVIEW
      - If ambiguity exists between multiple categories, select best-fit category but set flag to NEEDS_REVIEW
      - If severity keywords (injury, child, school, hospital, ambulance, fire, hazard, fell, collapse) are present, always set priority to Urgent
      - If no severity keywords are present and priority is unclear, default to Standard
      - Always generate a reason; if not possible, return a minimal one-sentence explanation referencing available words and set flag to NEEDS_REVIEW
      - Never output category values outside the allowed list; if risk detected, fallback to Other
      - Prevent taxonomy drift by mapping similar complaints consistently to the same allowed category
      - Avoid hallucinated sub-categories by restricting output strictly to allowed values

  - name: batch_classify
    description: Processes an input CSV of complaint descriptions, applies classify_complaint to each row, and writes results to an output CSV.
    input:
      type: file
      format: CSV file at ../data/city-test-files/test_[city].csv with complaint descriptions per row
    output:
      type: file
      format: CSV file uc-0a/results_[city].csv with columns category, priority, reason, flag for each input row
    error_handling:
      - If input file is missing or unreadable, terminate with an explicit error message and do not generate output
      - If required description field is missing in any row, process the row with classify_complaint fallback and set flag to NEEDS_REVIEW
      - Ensure every row produces all four required output fields; if any field is missing, regenerate that row with safe defaults
      - Validate all category and priority outputs against allowed values; replace invalid entries with compliant defaults (category Other, priority Low, flag NEEDS_REVIEW)
      - Enforce severity keyword rule across all rows to prevent severity blindness
      - Ensure every row includes a one-sentence reason citing words from the row; if not, regenerate reason and flag row for review
      - Detect inconsistent category usage across similar rows and normalize to prevent taxonomy drift
      - If widespread ambiguity or repeated NEEDS_REVIEW flags occur, complete processing but retain flags without forcing confident classifications