# skills.md

skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint description into a category, priority, reason, and ambiguity flag.
    input: A single complaint description string (plain text from one CSV row).
    output: >
      A structured record with four fields:
        - category: exactly one of — Pothole, Flooding, Streetlight, Waste, Noise,
          Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other
        - priority: Urgent | Standard | Low
        - reason: one sentence citing specific words from the input description
        - flag: NEEDS_REVIEW if the category is genuinely ambiguous, otherwise blank
    error_handling: >
      If the description is empty or unparseable, output category: Other,
      priority: Low, reason: "Description was empty or unreadable.", flag: NEEDS_REVIEW.
      If severity keywords (injury, child, school, hospital, ambulance, fire, hazard,
      fell, collapse) are present, priority must be Urgent regardless of other signals.
      If the category cannot be confidently determined, set category: Other and
      flag: NEEDS_REVIEW — never guess with false confidence.

  - name: batch_classify
    description: Reads an input CSV of complaint rows, applies classify_complaint to each row, and writes the results to an output CSV.
    input: >
      File path to a CSV (e.g. ../data/city-test-files/test_[city].csv).
      Required column: description. Columns category and priority_flag will be absent
      and must be generated.
    output: >
      A CSV file written to uc-0a/results_[city].csv containing all original columns
      plus: category, priority, reason, flag — one row per input complaint.
    error_handling: >
      If a row is missing a description, apply classify_complaint error handling for
      that row and continue processing remaining rows. Log a warning for each skipped
      or defaulted row. Do not abort the entire batch on a single bad row.
