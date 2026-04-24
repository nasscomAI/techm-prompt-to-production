
skills:
  - name: retrieve_policy
    description: Loads a local .txt policy file and returns the content parsed as structured numbered sections for unambiguous citation.
    input: file_path (string) - the relative or absolute path to the .txt policy document.
    output: structured_content (object) - a mapping of section/clause numbers to their exact text.
    error_handling: Returns an explicit error if the file is missing, unreadable, or not structured with numbered clauses, refusing to proceed.

  - name: summarize_policy
    description: Takes structured policy sections and produces a compliant summary with exact clause references, ensuring no constraints are dropped or softened.
    input: structured_content (object) - the output from retrieve_policy containing the explicit clauses.
    output: summary_document (string) - a concise policy summary with direct clause references (e.g., [Clause 2.3]) ensuring preservation of all conditions.
    error_handling: Validates the output against the core clauses; if any are missing or if condition drops (e.g., only one approver for LWP) are detected, raises an exception and outputs a refusal.
