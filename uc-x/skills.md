skills:
  - name: retrieve_documents
    description: Loads the HR, IT, and Finance policy files and indexes their content by document name and section number.
    input: List of file paths to policy documents.
    output: Indexed data structure containing document text mapped to section numbers and source filenames.
    error_handling: Returns an error message if any of the specified files are missing or unreadable.

  - name: answer_question
    description: Searches the indexed policy documents for a specific question and returns a single-source answer with citations or a standard refusal.
    input: User question as a string and the indexed policy data.
    output: String containing the policy answer with document and section citation, or the mandatory refusal template.
    error_handling: Returns the mandatory refusal template if the answer is ambiguous, requires cross-document blending, or is not found in the source documents.
