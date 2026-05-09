skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as structured numbered sections.
    input: A file path string pointing to a .txt policy document.
    output: A dictionary or list of structured numbered sections extracted from the file.
    error_handling: If the file is not found or unreadable, return an error message; if the file lacks numbered sections, return an empty structure and flag the issue.

  - name: summarize_policy
    description: Takes structured policy sections and produces a compliant summary with clause references.
    input: A structured data object (dictionary or list) containing numbered policy sections.
    output: A text string summary that includes every clause with references, quoting verbatim if meaning loss occurs.
    error_handling: If input is invalid or missing sections, produce a partial summary and flag omissions; if a clause cannot be summarized without meaning loss, quote it verbatim and flag it to avoid clause omission, scope bleed, or obligation softening.
