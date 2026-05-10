- name: retrieve_policy
  description: Loads the .txt policy file and returns its content as structured numbered sections.
  input:
    type: string
    format: Relative file path to the .txt policy document.
  output:
    type: array
    format: List of objects containing clause numbers and their raw text.
  error_handling: Returns an error if the file is missing or if the text cannot be parsed into numbered sections, rather than returning empty content.

- name: summarize_policy
  description: Takes structured sections and produces a compliant summary with explicit clause references without altering meaning or conditions.
  input:
    type: array
    format: List of objects containing clause numbers and their raw text.
  output:
    type: string
    format: Text summary with all 10 clauses present, preserving all conditions and binding verbs.
  error_handling: Rejects the output and flags an error if clause omission, scope bleed (e.g., adding phrases like "as is standard practice"), obligation softening, or condition dropping (e.g., missing one of two required approvers) is detected; quotes verbatim and flags if summarization causes meaning loss.
