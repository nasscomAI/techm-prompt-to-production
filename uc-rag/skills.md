# skills.md — UC-RAG RAG Server

skills:
  - name: chunk_documents
    description: Loads all .txt policy files from the policy-documents directory and splits each into sentence-boundary-respecting chunks of at most 400 tokens, returning structured metadata for each chunk.
    input: String docs_dir — path to the directory containing the three CMC policy .txt files.
    output: List of dicts, each with keys 'doc_name' (filename), 'chunk_index' (int, 0-based), 'text' (chunk content), and 'id' (unique string '<doc_name>::chunk_<index>').
    error_handling: If a file cannot be opened, log the error and skip that file — do not crash. If the directory does not exist, raise FileNotFoundError with the path. If a document produces no sentences, skip it and log a warning.

  - name: retrieve_and_answer
    description: Embeds the query with sentence-transformers, retrieves the top-3 chunks from ChromaDB by cosine similarity, filters out chunks below 0.6, and returns a grounded answer with citations or the refusal template if no chunks pass.
    input: String query, ChromaDB collection object, SentenceTransformer embedder, callable llm_call(prompt) -> str, optional int top_k (default 3), optional float threshold (default 0.6).
    output: Dict with keys 'answer' (string), 'cited_chunks' (list of dicts with doc_name, chunk_index, score), and 'refused' (bool).
    error_handling: If the ChromaDB collection is None or not built, raise RuntimeError instructing the user to run --build-index first. If no chunks score above 0.6, return the refusal template with refused=True and an empty cited_chunks list — never call the LLM. If the LLM call raises an exception, return the retrieved chunks as raw text with a warning and refused=False.
