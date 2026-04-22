

skills:
  - name: retrieve_documents
    description: Loads all 3 policy files (HR, IT, Finance) and indexes them by document name and section number.
    input: None
    output: A collection of indexed document sections.
    error_handling: Logs an error if any policy file is missing or inaccessible.

  - name: answer_question
    description: Searches the indexed documents for a specific answer, returning a single-source response with citation or the refusal template.
    input: Question (string)
    output: Answer with citation (string) or the refusal template (string).
    error_handling: Returns the refusal template if the answer cannot be found or if multiple conflicting sources are found.

