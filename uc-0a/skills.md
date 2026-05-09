name: classify_complaint
description: Processes a single citizen complaint to determine its category, priority, and justification based on a strict taxonomy and severity keyword list.
input:
type: dictionary
format: "{'description': string}"
output:
type: dictionary
format: "{'category': string, 'priority': string, 'reason': string, 'flag': string}"
error_handling: If the description contains no clear category, it assigns 'Other' and sets the flag to 'NEEDS_REVIEW'; if input is malformed, it returns a schema validation error.

name: batch_classify
description: Reads an input CSV file of complaints, executes the classification logic for each row, and writes the structured results to a specified output CSV.
input:
type: file_path
format: CSV file with 'description' column
output:
type: file_path
format: CSV file with 'category', 'priority', 'reason', and 'flag' columns
error_handling: Logs rows that fail strict enforcement rules, prevents execution if the taxonomy drift failure mode is detected, and ensures no rows are skipped due to ambiguity by applying the 'NEEDS_REVIEW' flag.