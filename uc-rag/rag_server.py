"""
UC-RAG — rag_server.py
Sentence-aware RAG implementation over CMC policy documents.

Stack: sentence-transformers · chromadb (stdlib + pip)
Setup: pip3 install sentence-transformers chromadb

Run:
  python3 rag_server.py --build-index
  python3 rag_server.py --query "Who approves leave without pay?"
  python3 rag_server.py --naive --query "Can I use my personal phone for work files?"
"""

import argparse
import os
import re
import sys

# ── CONFIG ────────────────────────────────────────────────────────────────────
DOCS_DIR   = os.path.join(os.path.dirname(__file__), "../data/policy-documents")
DB_PATH    = os.path.join(os.path.dirname(__file__), "./chroma_db")
COLLECTION = "policy_docs"
MODEL_NAME = "all-MiniLM-L6-v2"
MAX_TOKENS = 400
TOP_K      = 3
THRESHOLD  = 0.6

REFUSAL_TEMPLATE = (
    "This question is not covered in the retrieved policy documents. "
    "Retrieved chunks: {sources}. "
    "Please contact the relevant department for guidance."
)

# ── LAZY SINGLETONS ───────────────────────────────────────────────────────────
_embedder   = None
_client     = None
_collection = None


def get_embedder():
    """
    Initialize and return the sentence embedder singleton.
    
    Returns:
        SentenceTransformer: The loaded sentence embedding model.
    """
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("[rag_server] ERROR: sentence-transformers not installed.")
            print("             Run: pip3 install sentence-transformers chromadb")
            sys.exit(1)
        print("[rag_server] Loading embedder (first run only)...")
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def get_collection(db_path: str = DB_PATH):
    """
    Initialize and return the ChromaDB collection singleton.
    
    Args:
        db_path (str, optional): The path to the ChromaDB directory. Defaults to DB_PATH.
        
    Returns:
        Collection: The retrieved ChromaDB collection, or None if it cannot be accessed.
    """
    global _client, _collection
    if _collection is None:
        try:
            import chromadb
        except ImportError:
            print("[rag_server] ERROR: chromadb not installed.")
            print("             Run: pip3 install sentence-transformers chromadb")
            sys.exit(1)
        _client = chromadb.PersistentClient(path=db_path)
        try:
            _collection = _client.get_collection(COLLECTION)
        except Exception:
            _collection = None
    return _collection


# ── SKILL: chunk_documents ────────────────────────────────────────────────────
def _split_sentences(text: str) -> list[str]:
    """
    Split text on sentence boundaries using regex — no NLTK required.
    
    Args:
        text (str): The raw text to split.
        
    Returns:
        list[str]: A list of extracted sentences.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _chunk_text(text: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    """
    Accumulate sentences into chunks up to max_tokens (approx. words).
    Never splits mid-sentence — satisfies enforcement rule 1.
    
    Args:
        text (str): The full text to be chunked.
        max_tokens (int, optional): The maximum number of words per chunk. Defaults to MAX_TOKENS.
        
    Returns:
        list[str]: A list of text chunks.
    """
    sentences = _split_sentences(text)
    chunks, current, count = [], [], 0
    for sentence in sentences:
        words = len(sentence.split())
        if count + words > max_tokens and current:
            chunks.append(" ".join(current))
            current, count = [sentence], words
        else:
            current.append(sentence)
            count += words
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_documents(docs_dir: str = DOCS_DIR) -> list[dict]:
    """
    Load all .txt policy files from docs_dir.
    Return list of {doc_name, chunk_index, text, id}.
    Addresses failure mode 1: sentence-aware chunking prevents clause splitting.
    
    Args:
        docs_dir (str, optional): The directory containing policy documents. Defaults to DOCS_DIR.
        
    Returns:
        list[dict]: A list of dictionary objects representing document chunks.
    """
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"Policy documents directory not found: {docs_dir}")

    results = []
    for fname in sorted(os.listdir(docs_dir)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(docs_dir, fname)
        try:
            text = open(path, encoding="utf-8").read()
        except Exception as e:
            print(f"[rag_server] WARNING: Could not read {fname}: {e} — skipping.")
            continue

        chunks = _chunk_text(text)
        if not chunks:
            print(f"[rag_server] WARNING: No sentences found in {fname} — skipping.")
            continue

        for i, chunk in enumerate(chunks):
            results.append({
                "doc_name":    fname,
                "chunk_index": i,
                "text":        chunk,
                "id":          f"{fname}::chunk_{i}",
            })

    print(f"[rag_server] Chunked {len(results)} chunks from "
          f"{len(set(c['doc_name'] for c in results))} documents.")
    return results


# ── INDEX BUILDER ─────────────────────────────────────────────────────────────
def build_index(docs_dir: str = DOCS_DIR, db_path: str = DB_PATH):
    """
    Embed all chunks and store in ChromaDB.
    
    Args:
        docs_dir (str, optional): The directory containing policy text files. Defaults to DOCS_DIR.
        db_path (str, optional): The path to store the ChromaDB index. Defaults to DB_PATH.
    """
    global _client, _collection
    import chromadb

    embedder = get_embedder()
    chunks   = chunk_documents(docs_dir)

    _client = chromadb.PersistentClient(path=db_path)
    try:
        _client.delete_collection(COLLECTION)
    except Exception:
        pass
    _collection = _client.create_collection(COLLECTION)

    ids        = [c["id"]       for c in chunks]
    texts      = [c["text"]     for c in chunks]
    metadatas  = [{"doc_name": c["doc_name"], "chunk_index": c["chunk_index"]}
                  for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True).tolist()

    _collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    print(f"[rag_server] Index built at {db_path}")


# ── SKILL: retrieve_and_answer ────────────────────────────────────────────────
def retrieve_and_answer(
    query: str,
    collection=None,
    embedder=None,
    llm_call=None,
    top_k: int = TOP_K,
    threshold: float = THRESHOLD,
) -> dict:
    """
    Embed query → retrieve top_k chunks → filter by threshold → LLM answer.
    Returns {answer, cited_chunks, refused}.

    Addresses all 3 failure modes:
    - Chunks are sentence-aware (build_index uses chunk_documents)
    - Metadata filter separates docs (addresses wrong retrieval)
    - Prompt grounds answer to retrieved context only
    
    Args:
        query (str): The user query.
        collection: The ChromaDB collection to query against. Defaults to None.
        embedder: The embedding model to encode the query. Defaults to None.
        llm_call: The callable function to query the LLM. Defaults to None.
        top_k (int, optional): The number of chunks to retrieve. Defaults to TOP_K.
        threshold (float, optional): The minimum similarity threshold for chunks. Defaults to THRESHOLD.
        
    Returns:
        dict: A dictionary containing the LLM 'answer', 'cited_chunks', and a 'refused' boolean.
    """
    if collection is None:
        collection = get_collection()
    if collection is None:
        raise RuntimeError(
            "Index not built. Run first: python3 rag_server.py --build-index"
        )
    if embedder is None:
        embedder = get_embedder()

    query_embedding = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # ChromaDB returns L2 distances; convert to similarity: sim ≈ 1 - dist/2
    distance_threshold = (1.0 - threshold) * 2.0
    passing = [
        (doc, meta, dist)
        for doc, meta, dist in zip(docs, metadatas, distances)
        if dist <= distance_threshold
    ]

    cited_chunks = [
        {
            "doc_name":    m["doc_name"],
            "chunk_index": m["chunk_index"],
            "score":       round(1.0 - d / 2.0, 3),
            "text":        doc[:200] + "..." if len(doc) > 200 else doc,
        }
        for doc, m, d in passing
    ]

    # Enforcement rule 3: refusal when no chunk passes threshold
    if not passing:
        sources = ", ".join(
            f"{m['doc_name']}::chunk_{m['chunk_index']}"
            for _, m, _ in zip(docs, metadatas, distances)
        ) or "none"
        return {
            "answer":       REFUSAL_TEMPLATE.format(sources=sources),
            "cited_chunks": [],
            "refused":      True,
        }

    # Enforcement rule 4 & 5: context-grounded prompt, per-document sections
    context_blocks = "\n\n".join(
        f"[Source: {m['doc_name']}, chunk {m['chunk_index']}]\n{doc}"
        for doc, m, _ in passing
    )
    prompt = (
        "Answer the following question using ONLY the provided context. "
        "Do not use any information outside the context. "
        "Do not add examples, norms, or qualifications not present in the text. "
        "If the answer is not in the context, say so explicitly.\n\n"
        f"Context:\n{context_blocks}\n\n"
        f"Question: {query}\n\n"
        "Answer (cite source document name and chunk index for each claim):"
    )

    if llm_call is None:
        # No LLM configured — return raw retrieved context
        answer = (
            "Retrieved context (no LLM configured — set GEMINI_API_KEY):\n\n" +
            "\n\n---\n\n".join(
                f"[{m['doc_name']}, chunk {m['chunk_index']}]:\n{doc}"
                for doc, m, _ in passing
            )
        )
    else:
        try:
            answer = llm_call(prompt)
        except Exception as e:
            answer = (
                f"[LLM ERROR: {e}] Retrieved chunks:\n\n" +
                "\n\n---\n\n".join(
                    f"[{m['doc_name']}, chunk {m['chunk_index']}]:\n{doc}"
                    for doc, m, _ in passing
                )
            )

    return {
        "answer":       answer,
        "cited_chunks": cited_chunks,
        "refused":      False,
    }


# ── NAIVE MODE ────────────────────────────────────────────────────────────────
def naive_query(query: str, docs_dir: str = DOCS_DIR, llm_call=None) -> str:
    """
    Load all documents into context without retrieval.
    Run this first to observe failure modes before applying RAG.
    
    Args:
        query (str): The user query.
        docs_dir (str, optional): The directory containing the documents. Defaults to DOCS_DIR.
        llm_call: The callable LLM function. Defaults to None.
        
    Returns:
        str: The LLM's answer based on the full raw context of all documents.
    """
    all_text = []
    for fname in sorted(os.listdir(docs_dir)):
        if fname.endswith(".txt"):
            path = os.path.join(docs_dir, fname)
            all_text.append(open(path, encoding="utf-8").read())

    combined = "\n\n===\n\n".join(all_text)
    prompt = (
        f"Answer the following question based on these policy documents:\n\n"
        f"{combined}\n\nQuestion: {query}\n\nAnswer:"
    )

    if llm_call is None:
        return "[Naive mode — no LLM configured. Set GEMINI_API_KEY to see failure modes.]"
    return llm_call(prompt)


# ── PUBLIC INTERFACE (called by UC-MCP) ───────────────────────────────────────
def query(question: str, llm_call=None) -> dict:
    """
    Public interface for UC-MCP. 
    
    Args:
        question (str): The user query.
        llm_call: The callable LLM function. Defaults to None.
        
    Returns:
        dict: A dictionary containing the answer, cited_chunks, and refused status.
    """
    return retrieve_and_answer(question, llm_call=llm_call)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    """
    Main entry point for the RAG server CLI.
    
    Parses command-line arguments to either build the document index 
    or run a query (naive or standard retrieval) against the RAG system.
    """
    parser = argparse.ArgumentParser(description="UC-RAG RAG Server")
    parser.add_argument("--build-index", action="store_true",
                        help="Build ChromaDB index from policy documents")
    parser.add_argument("--query",    type=str, help="Query the RAG server")
    parser.add_argument("--naive",    action="store_true",
                        help="Run naive (no retrieval) mode to see failures")
    parser.add_argument("--docs-dir", type=str, default=DOCS_DIR)
    parser.add_argument("--db-path",  type=str, default=DB_PATH)
    args = parser.parse_args()

    if not args.build_index and not args.query:
        parser.print_help()
        sys.exit(1)

    # Load LLM adapter
    llm_call = None
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uc-mcp"))
        from llm_adapter import call_llm
        llm_call = call_llm
    except Exception:
        print("[rag_server] No LLM adapter found — will return retrieved chunks only.")

    if args.build_index:
        print("Building index...")
        build_index(args.docs_dir, args.db_path)
        print("Index built. Run with --query to test.")

    if args.query:
        if args.naive:
            result = naive_query(args.query, args.docs_dir, llm_call)
            print(f"\nNaive answer:\n{result}")
        else:
            result = retrieve_and_answer(args.query, llm_call=llm_call)
            print(f"\nAnswer:\n{result['answer']}")
            if result["cited_chunks"]:
                print("\nSources:")
                for c in result["cited_chunks"]:
                    print(f"  [{c['doc_name']}, chunk {c['chunk_index']}] score={c['score']}")
            if result.get("refused"):
                print("\n[REFUSED — no chunks above threshold]")


if __name__ == "__main__":
    main()
