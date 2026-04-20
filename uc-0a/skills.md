# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint into a category, priority, and generates a reason with review flag.
    input: A complaint record object with at least a 'description' string field.
    output: An object with four fields: category (string, exact value from allowed list), priority (string: Urgent/Standard/Low), reason (string, one sentence citing specific words from description), flag (string: NEEDS_REVIEW or empty string).
    error_handling: If the description is empty or not a string, return an error. If the category is genuinely ambiguous from the description alone, output category=Other and flag=NEEDS_REVIEW rather than raising an exception.

  - name: batch_classify
    description: Reads an input CSV of complaint records, applies classify_complaint to each row, and writes the results to an output CSV.
    input: Paths to input CSV file and output CSV file. Input CSV must contain a 'description' column.
    output: Writes a CSV file with columns: description (original), category, priority, reason, flag. Returns count of processed records.
    error_handling: If input file is missing or malformed, exit with an error message. If no description column exists, exit with an error. Continue processing if individual rows fail classification, logging failures to stderr.
