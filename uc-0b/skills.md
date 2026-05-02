# skills.md
# UC-0B — Policy Summarization Skills

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content structured as numbered sections with clause identifiers.
    input: File path (string) pointing to a .txt policy document.
    output: Dictionary with keys 'filename' (str), 'full_text' (str), 'clauses' (list of dicts with 'number', 'section', 'text' keys).
    error_handling: If file not found, raise FileNotFoundError. If file is empty, raise ValueError. If file lacks numbered structure, return raw text and flag with warning.

  - name: summarize_policy
    description: Takes structured policy sections and produces a compliant summary with explicit clause references and binding verb preservation.
    input: Dictionary from retrieve_policy (clauses list with numbered sections) and a target file path (string).
    output: Summarized text written to file; summary list (list of clause objects with 'clause_id', 'obligation', 'binding_verb', 'conditions' keys).
    error_handling: If a clause cannot be summarized without meaning loss, include verbatim quote with [QUOTED] flag. If conditions are complex, preserve ALL of them or refuse summarization for that clause.
