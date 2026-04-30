# skills.md

skills:
  - name: retrieve_policy
    description: Load a .txt policy file and return its content parsed into structured numbered sections.
    input: The file path to the policy text document.
    output: A list or dictionary of structured sections, preserving the original numbering and text.
    error_handling: If the file cannot be read or sections cannot be clearly parsed, raise an error indicating the parse failure.

  - name: summarize_policy
    description: Take structured sections and produce a compliant summary with clause references.
    input: The structured numbered sections produced by `retrieve_policy`.
    output: A summarized text document with clause references that strictly adheres to the enforcement rules.
    error_handling: If a clause cannot be summarized without losing meaning or dropping conditions, quote it verbatim and flag it.
