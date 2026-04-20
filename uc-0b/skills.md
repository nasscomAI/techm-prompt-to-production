# skills.md

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as structured numbered sections.
    input: Path to a .txt policy file (string)
    output: Dictionary mapping clause numbers to their content (e.g., {"2.3": "...", "2.4": "..."})
    error_handling: Validates all expected clauses present; raises error if any clause is missing from source

  - name: summarize_policy
    description: Takes structured policy sections and produces a compliant summary with clause references.
    input: Dictionary of clause numbers to content (output from retrieve_policy)
    output: Summary text with each clause's core obligation and binding verb, preserving all multi-condition obligations
    error_handling: Validates no scope bleed phrases present (e.g., "standard practice", "typically", "generally expected to"); for multi-condition obligations (e.g., clause 5.2 requiring TWO approvers), validates all conditions preserved — if any condition dropped, flags it verbatim; if meaning loss unavoidable, includes clause verbatim with flag