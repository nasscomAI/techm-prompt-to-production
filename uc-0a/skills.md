# skills.md
skills:

  - name: classify_complaint
    description: Accepts a single complaint row and returns exactly four classification
      fields — category, priority, reason, and flag — enforcing the allowed taxonomy
      and severity keyword rules.
    input:
      type: object
      format:
        description: A single row from the input CSV represented as a key-value object.
          Must contain at least a complaint description string. The category and
          priority_flag fields will be absent and must not be assumed or carried
          forward from any external source.
        fields:
          - name: description
            type: string
            required: true
            notes: Free-text citizen complaint. Must be non-empty.
          - name: any_other_csv_columns
            type: string
            required: false
            notes: All remaining columns from the source CSV are passed through
              unchanged and must appear unmodified in the output.
    output:
      type: object
      format:
        fields:
          - name: category
            type: string
            allowed_values:
              - Pothole
              - Flooding
              - Streetlight
              - Waste
              - Noise
              - Road Damage
              - Heritage Damage
              - Heat Hazard
              - Drain Blockage
              - Other
            notes: Exact string match required — no casing, spelling, or punctuation
              variants permitted.
          - name: priority
            type: string
            allowed_values:
              - Urgent
              - Standard
              - Low
            notes: Must be Urgent when the description contains any of — injury,
              child, school, hospital, ambulance, fire, hazard, fell, collapse
              (case-insensitive, full-text scan). Must be Standard or Low otherwise.
          - name: reason
            type: string
            notes: Exactly one sentence. Must cite specific words drawn directly
              from the input description. Must never be empty, null, or generic.
          - name: flag
            type: string
            allowed_values:
              - NEEDS_REVIEW
              - ""
            notes: Set to NEEDS_REVIEW when the correct category cannot be determined
              with confidence. Blank when category is clear.
    error_handling:
      - trigger: description field is empty or missing
        action: Set category to Other, priority to Low, reason to "Description
          was absent so no classification signal was available.", flag to
          NEEDS_REVIEW.
      - trigger: description contains a severity keyword but the complaint type
          is ambiguous
        action: Priority must still be set to Urgent regardless of ambiguity;
          category is set to the closest match or Other; flag is set to
          NEEDS_REVIEW.
      - trigger: description could match more than one taxonomy category with
          equal confidence (taxonomy drift risk)
        action: Choose the single best-fitting category, set flag to NEEDS_REVIEW,
          and include both candidate categories by name in the reason sentence.
      - trigger: description appears to describe a category not present in the
          allowed taxonomy (hallucinated sub-category risk)
        action: Set category to Other; do not invent a new label. Reason must
          note that no matching taxonomy category was found.
      - trigger: severity keyword is present but spelled as a variant or partial
          match (e.g. "injured", "children", "schools")
        action: Apply case-insensitive substring matching so that morphological
          variants of any severity keyword still trigger Urgent priority.

  - name: batch_classify
    description: Reads the input CSV row by row, applies classify_complaint to each
      row, and writes all results to the output CSV preserving row order and
      passthrough columns.
    input:
      type: file
      format:
        mime_type: text/csv
        path: ../data/city-test-files/test_bengaluru.csv
        notes: Must contain a description column and exactly 15 data rows. The
          category and priority_flag columns will be absent. All other columns
          are treated as passthrough and must be preserved in the output unchanged.
    output:
      type: file
      format:
        mime_type: text/csv
        path: uc-0a/results_bengaluru.csv
        notes: Must contain one output row per input row in the same order. Each
          row includes all passthrough columns plus the four classification fields —
          category, priority, reason, flag. No rows may be added, dropped, or
          reordered.
    error_handling:
      - trigger: input file is missing or path is invalid
        action: Halt immediately and raise a file-not-found error with the
          attempted path. Do not produce a partial output file.
      - trigger: input file has fewer or more than 15 data rows
        action: Log a warning stating the actual row count, then proceed to
          classify all rows present. Do not pad or truncate.
      - trigger: a row is malformed or unparseable (e.g. mismatched column count)
        action: Write the row to the output with category set to Other, priority
          to Low, reason set to "Row could not be parsed.", flag set to
          NEEDS_REVIEW. Continue processing remaining rows.
      - trigger: classify_complaint returns an out-of-taxonomy category string
          for any row (taxonomy drift)
        action: Reject the returned value, substitute Other, set flag to
          NEEDS_REVIEW, and log the offending value and row index.
      - trigger: classify_complaint returns a missing or empty reason field
          (missing justification)
        action: Reject the row result, re-invoke classify_complaint once with an
          explicit instruction that reason is mandatory. If still empty, write
          "No reason produced." and set flag to NEEDS_REVIEW.
      - trigger: output directory does not exist
        action: Create the directory path before writing. If creation fails,
          raise a permission error and halt without writing partial output.
