# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single civic complaint row into category, priority,
      reason, and flag according to the enforcement rules in agents.md.
    input: One complaint row with fields — complaint_id, description (required);
      location, ward, date_raised (optional, used for traceability only).
    output: A structured record with exactly four fields:
        - category: one of Pothole · Flooding · Streetlight · Waste · Noise ·
          Road Damage · Heritage Damage · Heat Hazard · Drain Blockage · Other
        - priority: Urgent | Standard | Low
        - reason: one sentence quoting specific words from the description
        - flag: NEEDS_REVIEW if category is ambiguous, otherwise blank
    error_handling: If description is missing or empty, output category: Other,
      priority: Low, reason: "No description provided", flag: NEEDS_REVIEW.
      If category cannot be determined from the description alone, output
      category: Other and flag: NEEDS_REVIEW — never guess.

  - name: batch_classify
    description: Reads test_hyderabad.csv, applies classify_complaint to every
      row, and writes the results to results_hyderabad.csv.
    input: File path to input CSV (e.g. ../data/city-test-files/test_hyderabad.csv).
      Expected columns: complaint_id, date_raised, city, ward, location,
      description, reported_by, days_open.
    output: CSV file at uc-0a/results_hyderabad.csv with all original columns
      plus four appended fields: category, priority, reason, flag.
      One output row per input row — no rows dropped or reordered.
    error_handling: If a row fails classify_complaint (e.g. blank description),
      still emit the row with category: Other, flag: NEEDS_REVIEW, and log the
      complaint_id to stderr. Do not abort the batch on a single row failure.
