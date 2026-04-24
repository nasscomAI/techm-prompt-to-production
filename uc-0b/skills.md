# skills.md
# Defined skills required by the UC-0B agent

skills:
  - name: retrieve_policy
    description: Load a plain-text policy file and parse it into numbered sections.
    input: File path (string) to a UTF-8 encoded `.txt` policy document.
    output: JSON-like structure: list of {"section_number": "2.3", "heading": "...", "body": "..."}.
    error_handling: If file missing or unreadable, return an explicit error message. If numbering is ambiguous, return raw text and a parse warning.

  - name: summarize_policy
    description: Produce a compliant summary that preserves all clause obligations and references.
    input: Structured sections (as returned by `retrieve_policy`) and the clause inventory (list of required clause identifiers and conditions).
    output: Plain-text summary that includes every inventory clause exactly, with clause references (e.g., "Clause 2.3: ..."). If a clause cannot be summarised without meaning loss, include the verbatim original and a flag.
    error_handling: If any inventory clause is missing from the structured sections, refuse to generate and return a detailed missing-clause report.

# Notes
- `summarize_policy` must enforce that multi-condition obligations keep all conditions intact (no dropping or softening).
- Implementations should prefer quoting verbatim when preservation would otherwise change meaning.
