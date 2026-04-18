# skills.md

skills:
  - name: retrieve_policy
    description: Loads a plain-text policy file and returns a structured clause inventory.
    input: "file_path (string) — path to policy .txt"
    output: |
      JSON object with keys:
        - clauses: array of { number: string, text: string, raw_range: {start_line:int,end_line:int} }
        - metadata: { source_path: string, parsed_at: timestamp }
    error_handling: |
      - If file missing or unreadable: return an error with actionable message.
      - If numbering cannot be reliably detected: return raw text under `clauses` as a
        single element and set `metadata.parse_confidence` low.

  - name: summarize_policy
    description: Produces a clause-preserving summary from the structured policy.
    input: |
      - `clauses` (array) — as produced by `retrieve_policy`.
      - `options` (object, optional) — { max_length:int, prefer_verbatim:bool }
    output: |
      JSON object with keys:
        - `summary_text` (string) — the human-readable summary with clause refs
        - `included_clauses` (array of numbers)
        - `verbatim_quotes` (array of {number, text})
        - `notes` (array) — any flags about potential meaning loss
    error_handling: |
      - If a clause cannot be safely summarized without dropping conditions,
        include the clause verbatim in `verbatim_quotes` and add a note.
      - If input is malformed, return a structured error describing the issue.

  - name: verify_summary
    description: Compares a generated summary against the original clauses and reports omissions or condition drops.
    input: |
      - `clauses` (array) — original structured clauses
      - `summary_text` (string) — produced summary
    output: |
      JSON object with keys:
        - `missing_clauses` (array of numbers)
        - `condition_drops` (array of {number, details})
        - `ok` (bool) — true when no issues found
    error_handling: |
      - If automated verification is uncertain about a phrasing, mark the clause
        in `condition_drops` with `details: 'uncertain'` and recommend manual review.

notes: |
  These skills implement the enforcement requirements in `agents.md`: always preserve
  numbered clauses, never add external information, and verbatim-quote clauses when
  necessary to avoid meaning loss.
