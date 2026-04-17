# skills.md — UC-RAG RAG Server
# INSTRUCTIONS:
# 1. Open your AI tool
# 2. Paste the full contents of uc-rag/README.md
# 3. Use this prompt:
#    "Read this UC README. Generate a skills.md YAML defining the two
#     skills: chunk_documents and retrieve_and_answer. Each skill needs:
#     name, description, input, output, error_handling.
#     error_handling must address the failure modes in the README.
#     Output only valid YAML."
# 4. Paste the output below, replacing this placeholder
# 5. Verify error_handling addresses all three failure modes

skills:
  - name: chunk_documents
    description: Split documents into chunks of ≤ 400 tokens, respecting sentence boundaries.
    input: Path to the policy-documents directory.
    output: List of chunk dictionaries with doc_name, chunk_index, and text.
    error_handling: |
      If a file is missing or unreadable, log the error and skip the file.
      Ensure no chunk exceeds 400 tokens or splits mid-sentence.

  - name: retrieve_and_answer
    description: Retrieve relevant chunks and generate an answer based on the query.
    input: Query string.
    output: Answer string and list of cited chunks.
    error_handling: |
      If no chunk scores above the similarity threshold (0.6), return the refusal template.
      Ensure the answer uses only retrieved chunks and cites sources.
