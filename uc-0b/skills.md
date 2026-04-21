# skills.md

skills:
  - name: retrieve_policy
    description: Loads a policy text file and returns its content as structured numbered sections.
    input: A file path to a `.txt` policy document.
    output: A list of clauses with clause numbers, text, and any nested conditions.
    error_handling: Returns a clear error when the file is missing, unreadable, or the policy does not contain parseable numbered clauses.

  - name: summarize_policy
    description: Produces a compliant summary from structured policy clauses while preserving meaning and clause references.
    input: Structured clauses produced by `retrieve_policy`.
    output: Summary text containing every numbered clause, with all conditions preserved or verbatim clauses flagged when needed.
    error_handling: If a clause cannot be safely summarized, returns the original clause verbatim with an explicit preservation note, rather than producing a weakened summary.
