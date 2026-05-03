# skills.md

skills:
  - name: retrieve_documents
    description: Loads the HR, IT, and Finance policy files and indexes their content by document name and section number for precise retrieval.
    input: File paths to policy documents (List of strings).
    output: Indexed document structure (Dictionary/Object) mapped by document name and section.
    error_handling: Log an error if a file is missing or unreadable; do not proceed with partial data for critical policy checks.

  - name: answer_question
    description: Searches the indexed policy documents to find a single source of truth for the user's question, ensuring no document blending occurs.
    input: User question (String) and Indexed documents (Object).
    output: A string containing the direct answer with mandatory citation (Document Name + Section) OR the exact refusal template.
    error_handling: If the answer requires combining multiple documents or is not found, return the mandatory refusal template.
