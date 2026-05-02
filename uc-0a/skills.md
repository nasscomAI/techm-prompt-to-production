- name: classify_complaint
  description: Classifies a single citizen complaint row into a strict taxonomy and priority level with justification.
  input: Object (JSON-like complaint row)
  output: Object (JSON-like result with category, priority, reason, and flag)
  error_handling: Sets the flag field to NEEDS_REVIEW if the category is ambiguous and enforces strict priority logic for severity keywords.

- name: batch_classify
  description: Automates the classification of complaints by processing an input CSV file and generating an output results CSV.
  input: String (file path to input CSV)
  output: String (file path to output CSV)
  error_handling: Detects and handles empty input files, category name variations, priority misclassifications, missing justification, and ambiguous classifications by flagging them for review and maintaining taxonomic consistency.

