skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint to determine its rigid category, priority level, and reason.
    input: String or Dictionary (The text description of a single citizen complaint).
    output: Dictionary containing four explicit fields (category, priority, reason, flag).
    error_handling: If the complaint is genuinely ambiguous or does not fit the taxonomy, the category must be 'Other' and the flag must be 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads an input CSV of raw complaints, applies the classify_complaint skill to each valid row individually, and writes the structured results to an output CSV.
    input: String (Filepath to the input CSV file containing complaint rows).
    output: String (Filepath to the newly generated output CSV file with results).
    error_handling: If the input file is missing, unreadable, or improperly formatted, halt the execution and return a file access error.
