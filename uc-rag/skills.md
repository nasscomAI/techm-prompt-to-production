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
    description: >
      Loads all policy documents from data/policy-documents/ and splits each document
      into chunks of maximum 400 tokens, ensuring that splits only occur on sentence boundaries 
      (never mid-sentence) to prevent chunk boundary failure.
    input: "path to the policy documents directory (e.g., data/policy-documents/)"
    output: "list of chunk dictionaries containing the doc_name, chunk_index, and text"
    error_handling: "If a file is missing or unreadable, log an error for that specific file and proceed with the remaining available files."

  - name: retrieve_and_answer
    description: >
      Takes a query string, embeds it using sentence-transformers, retrieves the top-3 chunks
      from ChromaDB by cosine similarity, filters out any chunk scoring below 0.6 to prevent
      wrong chunk retrieval, and calls the LLM with the filtered chunks as context only to prevent
      answering outside of retrieved context.
    input: "user query string"
    output: "answer string + list of cited chunks (doc_name and chunk_index)"
    error_handling: "If no chunk scores above similarity threshold 0.6, immediately return the refusal template: 'This question is not covered in the retrieved policy documents. Retrieved chunks: [list chunk sources]. Please contact the relevant department for guidance.'"
