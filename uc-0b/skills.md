# skills.md

skills:
  - name: retrieve_policy
    description: Loads .txt policy file, returns content as structured numbered sections.
    input: File path string to the text file.
    output: Dictionary mapping clause numbers to their exact text.
    error_handling: Fail safely and report if the file is missing or unreadable.

  - name: summarize_policy
    description: Takes structured sections, produces compliant summary with clause references.
    input: Dictionary of structured policy sections.
    output: Formatted string containing the final summary, mapping each clause to its obligation.
    error_handling: Any clause that cannot be cleanly summarized without meaning loss is quoted verbatim and flagged.
