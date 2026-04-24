skills:
  - name: retrieve_documents
    description: Loads all 3 policy files, indexes by document name and section number.
    input: List of relative file paths to the policy documents (List[str]).
    output: A single string concatenating the documents with clear markers for document names and section titles (str).
    error_handling: Return an error message if a file is missing or cannot be read.

  - name: answer_question
    description: Searches indexed documents to return a single-source answer with a section citation, or returns the exact refusal template if blending is required or answer is missing.
    input: The user's question (str) and the loaded document context from retrieve_documents (str).
    output: The single-source answer with citation, or exactly the refusal template (str).
    error_handling: If the question requires blending documents or the answer isn't explicitly found, strictly return the refusal template. Do not guess.
