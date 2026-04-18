# skills.md

skills:
  - name: classify_complaint
    description: Classify a single complaint row into category, priority, reason, and flag.
    input:
      type: object
      fields:
        - description: string (free-text complaint description)
        - metadata: object (optional; may include location, time, reporter)
    output:
      type: object
      fields:
        - category: string (one of the exact allowed values)
        - priority: string (Urgent|Standard|Low)
        - reason: string (one sentence citing words from description)
        - flag: string ("NEEDS_REVIEW" or blank)
    error_handling:
      - If `description` is missing or empty, return `category: Other`, `priority: Low`, `reason` explaining missing input, and `flag: NEEDS_REVIEW`.
      - If multiple categories are equally plausible, set `flag: NEEDS_REVIEW` and choose `category: Other` when no clear match.

  - name: batch_classify
    description: Read an input CSV of complaint rows, apply `classify_complaint` to each row, and write an output CSV with required fields.
    input:
      type: file
      format: CSV with columns including at least `description` (additional columns preserved)
    output:
      type: file
      format: CSV with columns: original columns + `category`, `priority`, `reason`, `flag`
    error_handling:
      - Skip rows with irrecoverable parse errors and log them with row index and error reason.
      - For rows with ambiguous classification, populate `flag: NEEDS_REVIEW` and include the classifier `reason` to aid reviewers.

notes: >
  Implementations should follow the enforcement rules in agents.md and the
  Classification Schema in README.md. Keep output strings exact to the
  allowed values to avoid downstream aggregation errors.
