# skills.md

skills:
  - name: retrieve_documents
    description: Loads all 3 policy files and indexes their contents by document name and section number.
    input: File paths to the three policy text documents.
    output: An indexed structure of documents, organized by source name and specific section number.
    error_handling: If a file cannot be read or sections cannot be parsed, raise an error indicating which document failed to load.

  - name: answer_question
    description: Searches the indexed documents and returns a single-source answer with an exact citation or the exact refusal template.
    input: A user's question string and the indexed documents from `retrieve_documents`.
    output: A precise answer citing the source document and section, OR the exact verbatim refusal template.
    error_handling: If the answer is ambiguous, requires blending documents, or is not explicitly covered, immediately return the verbatim refusal template.
