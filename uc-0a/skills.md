# skills.md — UC-0A Complaint Classifier

skills:
  - name: classify_complaint
    role: >
      You are the core categorization execution step for individual citizen complaints within the classifier pipeline.
    intent: >
      Analyze a single citizen complaint description and determine its category, priority, reason, and review flag, avoiding any hallucinated sub-categories.
    context: >
      You receive one complaint row containing at least a text description. You must apply the predefined classification schema and severity keywords to generate the correct output fields without any external assumptions.
    enforcement:
      - "Output must contain exactly four fields: category (exact string), priority (Urgent/Standard/Low), reason (one sentence citing specific words), and flag (NEEDS_REVIEW or blank)."
      - "If the complaint description is genuinely ambiguous, set the flag to 'NEEDS_REVIEW' instead of guessing with false confidence."

  - name: batch_classify
    role: >
      You are the batch processing coordinator responsible for handling entire files of complaint data efficiently.
    intent: >
      Read a batch of complaints from an input CSV, apply the classify_complaint skill to each row, and write the consolidated results to an output CSV.
    context: >
      You will read from the input path (e.g., `../data/city-test-files/test_[city].csv`) and process exactly 15 rows per city. You will write the classification results to the output path (e.g., `uc-0a/results_[city].csv`).
    enforcement:
      - "Ensure all rows are processed and the output CSV is correctly formatted with the new classification columns."
      - "Handle file not found errors gracefully."
      - "Process empty descriptions by classifying them as 'Other' with a 'NEEDS_REVIEW' flag."
