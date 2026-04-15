skills:
  - name: classify_complaint
    description: Accepts a single citizen complaint description and returns a structured record with category, priority, reason, and flag.
    input: |
      A plain-text complaint description (string). Example:
        "Large pothole near school gate caused a child to fall off a bicycle."
    output: |
      A dict/JSON object with exactly four fields:
        {
          "category":  "<one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other>",
          "priority":  "<one of: Urgent, Standard, Low>",
          "reason":    "<one sentence citing specific words from the description>",
          "flag":      "<NEEDS_REVIEW | blank>"
        }
    error_handling: |
      - If description is empty or non-text, output category: Other, priority: Low,
        reason: "No description provided to classify.", flag: NEEDS_REVIEW.
      - If the category cannot be determined from the description alone, output
        category: Other and flag: NEEDS_REVIEW regardless of any apparent context.
      - If a severity keyword is present, priority must be overridden to Urgent
        even if the general tone of the complaint seems minor.

  - name: batch_classify
    description: Reads an input CSV of complaint rows, applies classify_complaint to each row, and writes a results CSV with the four classification fields appended.
    input: |
      A CSV file path (string) pointing to a file with at minimum a description
      column. The category and priority_flag columns are stripped — do not
      expect or use them. Example invocation:
        batch_classify(input="data/test_pune.csv", output="results_pune.csv")
    output: |
      A CSV file written to the specified output path containing all original
      columns plus four new columns: category, priority, reason, flag.
      One row per input complaint, no rows skipped.
    error_handling: |
      - If the input file is missing or unreadable, raise FileNotFoundError with
        the full path in the message and halt — do not produce partial output.
      - If an individual row fails classify_complaint, write category: Other,
        priority: Low, reason: "Row could not be classified.", flag: NEEDS_REVIEW
        for that row and continue processing remaining rows.
      - If the output path is not writable, raise PermissionError and halt.
