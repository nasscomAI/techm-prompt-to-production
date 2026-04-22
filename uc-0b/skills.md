# skills.md

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns the content as structured numbered sections.
    input: File path (string)
    output: List of structured sections/clauses (list of strings or objects)
    error_handling: Raise FileNotFoundError if path is invalid; return error message if file is not text.

  - name: summarize_policy
    description: Takes structured sections and produces a compliant summary with clause references, adhering to enforcement rules.
    input: List of structured sections (list)
    output: Formatted summary (string)
    error_handling: Return error if mandatory clauses are missing or conditions are dropped.
