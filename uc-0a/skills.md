# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classiify_complaint
    description: "Classifies a single civic complaint into category, priority, reason, and flag based strictly on the defined schema."
    input: type: object
           format: "Single complaint row containing at least a description field as plain text"
    output: type: object
            format: "category (string), priority (string), reason (one sentence string), flag (string or blank)"
    error_handling: "If the description is missing or empty, return category=Other, priority=Low, reason='No valid description provided', flag=NEEDS_REVIEW"
    "If multiple categories are plausible and ambiguity cannot be resolved from text, set flag=NEEDS_REVIEW and avoid confident classification"
    "If no allowed category matches, default to category=Other without inventing new labels"
    "If severity keywords (injury, child, school, hospital, ambulance, fire, hazard, fell, collapse) are present but priority is not Urgent, override to Urgent"
    "If reason cannot cite exact words from the description, set flag=NEEDS_REVIEW and include best possible citation"
    "Prevent taxonomy drift by ensuring only allowed category values are used"
    "Reject any attempt to output missing fields by filling defaults and marking NEEDS_REVIEW"

  - name: batch_classify
    description: "Processes a CSV file of complaint rows, applies classification to each row, and writes results to an output CSV file."
    input: type: file
           format: "CSV file at ../data/city-test-files/test_[your-city].csv with 15 rows and complaint descriptions"
    output:type: file
           format: "CSV file at uc-0a/results_[your-city].csv with columns category, priority, reason, flag for each row" 
    error_handling: 
    "If input file is missing, unreadable, or malformed, abort processing and return an error message indicating invalid input file"
    "If any row is invalid or missing description, process row using classify_complaint fallback and mark NEEDS_REVIEW"
    "Ensure all rows produce outputs with all required fields; do not skip rows"
    "If inconsistent category naming occurs across rows, normalize to allowed schema values"
    "If severity keywords are present in any row but not marked Urgent, correct during processing"
    "If output file cannot be written, return an error indicating write failure"
    "Do not introduce new columns or omit required columns in the output CSV"


