"""
UC-RAG — RAG Server
rag_server.py — Starter file

Build this using your AI coding tool:
1. Share the contents of agents.md, skills.md, and uc-rag/README.md
2. Ask the AI to implement this file following the enforcement rules
   in agents.md and the skill definitions in skills.md
3. Run with: python3 rag_server.py --build-index
4. Then:      python3 rag_server.py --query "your question here"

Stack:
  pip3 install sentence-transformers chromadb
  LLM: set your API key in llm_adapter.py (../uc-mcp/llm_adapter.py)
       or set environment variable GEMINI_API_KEY
"""

import argparse
import os
import sys
from nltk.tokenize import sent_tokenize

# --- SKILL: chunk_documents ---
def chunk_documents(docs_dir: str, max_tokens: int = 400) -> list[dict]:
    """
    Load all .txt files from docs_dir.
    Split each into chunks of max_tokens, respecting sentence boundaries.
    Return list of: {doc_name, chunk_index, text}

    Failure mode to prevent:
    - Never split mid-sentence (chunk boundary failure)
    - Never exceed max_tokens per chunk
    """
    import os
    from transformers import GPT2TokenizerFast

    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    chunks = []

    for file_name in os.listdir(docs_dir):
        if file_name.endswith(".txt"):
            file_path = os.path.join(docs_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
                sentences = sent_tokenize(text)

                current_chunk = []
                current_tokens = 0
                chunk_index = 0

                for sentence in sentences:
                    sentence_tokens = len(tokenizer.tokenize(sentence))

                    if current_tokens + sentence_tokens > max_tokens:
                        chunks.append({
                            "doc_name": file_name,
                            "chunk_index": chunk_index,
                            "text": " ".join(current_chunk),
                        })
                        chunk_index += 1
                        current_chunk = []
                        current_tokens = 0

                    current_chunk.append(sentence)
                    current_tokens += sentence_tokens

                if current_chunk:
                    chunks.append({
                        "doc_name": file_name,
                        "chunk_index": chunk_index,
                        "text": " ".join(current_chunk),
                    })

    return chunks


# --- SKILL: retrieve_and_answer ---
def retrieve_and_answer(
    query: str,
    collection,          # ChromaDB collection
    embedder,            # SentenceTransformer model
    llm_call,            # callable: (prompt: str) -> str
    top_k: int = 3,
    threshold: float = 0.6,
) -> dict:
    """
    Embed query, retrieve top_k chunks from ChromaDB.
    Generate an answer using only retrieved chunks.
    Cite source document name and chunk index in the response.
    Refuse to answer if no chunk scores above the threshold.
    """
    # Embed the query
    query_embedding = embedder.encode(query)

    # Retrieve top_k chunks
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    # Filter chunks by similarity threshold
    retrieved_chunks = []
    for doc, score in zip(results["documents"], results["distances"]):
        if score >= threshold:
            retrieved_chunks.append(doc)

    # Refuse to answer if no chunks meet the threshold
    if not retrieved_chunks:
        return {
            "answer": "I'm sorry, I cannot answer that question based on the available documents.",
            "sources": []
        }

    # Generate the answer using retrieved chunks
    context = "\n".join([chunk["text"] for chunk in retrieved_chunks])
    prompt = f"Answer the question based on the following context:\n{context}\n\nQuestion: {query}\nAnswer:"
    answer = llm_call(prompt)

    # Cite sources
    sources = [f"{chunk['doc_name']} (chunk {chunk['chunk_index']})" for chunk in retrieved_chunks]

    return {
        "answer": answer,
        "sources": sources
    }


# --- INDEX BUILDER ---
def build_index(docs_dir: str, db_path: str = "./chroma_db"):
    """
    Chunk all documents and store embeddings in ChromaDB.
    Called once before querying.
    """
    raise NotImplementedError(
        "Implement build_index using your AI tool.\n"
        "Hint: call chunk_documents(), embed each chunk with "
        "SentenceTransformer, upsert into ChromaDB collection."
    )


# --- NAIVE MODE (run this first to see failure modes) ---
def naive_query(query: str, docs_dir: str, llm_call):
    """
    Load all documents into context without retrieval.
    Run this BEFORE building your RAG pipeline to observe the failure modes.
    """
    raise NotImplementedError(
        "Implement naive_query using your AI tool.\n"
        "Hint: load all .txt files, concatenate, pass to LLM with query. "
        "No chunking, no retrieval, no enforcement."
    )


# --- MAIN ---
def main():
    parser = argparse.ArgumentParser(description="UC-RAG RAG Server")
    parser.add_argument("--build-index", action="store_true",
                        help="Build ChromaDB index from policy documents")
    parser.add_argument("--query", type=str,
                        help="Query the RAG server")
    parser.add_argument("--naive", action="store_true",
                        help="Run naive (no retrieval) mode to see failures")
    parser.add_argument("--docs-dir", type=str,
                        default="../data/policy-documents",
                        help="Path to policy documents directory")
    parser.add_argument("--db-path", type=str,
                        default="./chroma_db",
                        help="Path to ChromaDB storage directory")
    args = parser.parse_args()

    if not args.build_index and not args.query:
        parser.print_help()
        sys.exit(1)

    if args.build_index:
        print("Building index...")
        build_index(args.docs_dir, args.db_path)
        print("Index built. Run with --query to test.")

    if args.query:
        if args.naive:
            # Import LLM adapter from uc-mcp
            sys.path.insert(0, "../uc-mcp")
            from llm_adapter import call_llm
            result = naive_query(args.query, args.docs_dir, call_llm)
            print(f"\nNaive answer:\n{result}")
        else:
            # Full RAG query
            raise NotImplementedError(
                "Wire up retrieve_and_answer with ChromaDB and embedder here."
            )


if __name__ == "__main__":
    main()
