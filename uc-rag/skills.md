skills:
  - name: chunk_documents
    description: >
      Loads all policy documents from the data/policy-documents directory and splits them into
      sentence-aware chunks of maximum 400 tokens. Ensures no sentence is split across chunks
      and attaches metadata including document name and chunk index.
    input: >
      Path to directory: data/policy-documents/
    output: >
      List of chunk dictionaries:
      [
        {
          "doc_name": "policy_name",
          "chunk_index": 0,
          "text": "chunk text"
        }
      ]
    error_handling: >
      If a file is missing or unreadable, skip the file and log an error without stopping execution.
      To prevent chunk boundary failure, enforce sentence-boundary-aware splitting and ensure no chunk
      exceeds 400 tokens or splits mid-sentence.

  - name: retrieve_and_answer
    description: >
      Takes a query string, embeds it using sentence-transformers, retrieves relevant chunks
      from ChromaDB using cosine similarity, filters out chunks below a similarity threshold of 0.6,
      and generates an answer strictly grounded in the retrieved chunks with proper citations.
    input: >
      Query string
    output: >
      {
        "answer": "grounded answer",
        "citations": [
          {"doc_name": "policy_name", "chunk_index": 1}
        ]
      }
    error_handling: >
      If no retrieved chunk has a similarity score of 0.6 or higher, return the refusal template:
      "This question is not covered in the retrieved policy documents. Retrieved chunks: []. Please contact the relevant department for guidance."
      To prevent wrong chunk retrieval, apply similarity threshold filtering and restrict results to top relevant chunks.
      To prevent answering outside retrieved context, enforce that the LLM uses only retrieved chunks and does not introduce external knowledge.
      To prevent cross-document blending, group retrieved chunks by document and generate separate answers per document.
      To prevent missing citations, ensure every response includes doc_name and chunk_index for all referenced chunks.