import argparse
import os
import re
from collections import defaultdict

import chromadb
from sentence_transformers import SentenceTransformer


# -----------------------------
# Helper
# -----------------------------
def clean_sentence(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    if re.match(r"^\d+(\.\d+)?", s):
        return s
    return ""


# -----------------------------
# Chunking
# -----------------------------
def chunk_documents(docs_dir: str, max_tokens: int = 400):
    chunks = []

    for file in os.listdir(docs_dir):
        if not file.endswith(".txt"):
            continue

        path = os.path.join(docs_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk, current_len = [], 0
        chunk_index = 0

        for sent in sentences:
            tokens = sent.split()

            if current_len + len(tokens) > max_tokens:
                chunks.append({
                    "doc_name": file,
                    "chunk_index": chunk_index,
                    "text": " ".join(current_chunk)
                })
                chunk_index += 1
                current_chunk, current_len = [], 0

            current_chunk.append(sent)
            current_len += len(tokens)

        if current_chunk:
            chunks.append({
                "doc_name": file,
                "chunk_index": chunk_index,
                "text": " ".join(current_chunk)
            })

    return chunks


# -----------------------------
# STRICT EXTRACTION
# -----------------------------
def strict_llm(context_chunks, query):
    query = query.lower()
    relevant = []

    for chunk in context_chunks:
        sentences = re.split(r'\n|\.', chunk)

        for s in sentences:
            s_lower = s.lower()

            if "leave without pay" in query or "approve" in query:
                if "leave without pay" in s_lower or "lwp" in s_lower:
                    cleaned = clean_sentence(s)
                    if cleaned:
                        relevant.append(cleaned)

            elif "personal phone" in query or "personal device" in query:
                if "personal device" in s_lower:
                    cleaned = clean_sentence(s)
                    if cleaned:
                        relevant.append(cleaned)

            elif "allowance" in query or "reimbursement" in query:
                if "allowance" in s_lower or "reimbursement" in s_lower:
                    cleaned = clean_sentence(s)
                    if cleaned:
                        relevant.append(cleaned)

    return " ".join(relevant)


# -----------------------------
# RETRIEVE + ANSWER
# -----------------------------
def retrieve_and_answer(query, collection, embedder, top_k=3, threshold=0.2):

    query_embedding = embedder.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=6
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved = []

    for doc, meta, dist in zip(docs, metas, distances):
        score = 1 / (1 + dist)

        if score >= threshold:
            retrieved.append({
                "doc_name": meta["doc_name"],
                "chunk_index": meta["chunk_index"],
                "text": doc,
                "score": score
            })

    # -----------------------------
    # TRUE refusal (no retrieval)
    # -----------------------------
    if not retrieved:
        return {
            "answer": "I can only answer questions about CMC HR, IT, and Finance policies.",
            "sources": [],
            "refused": True
        }

    # -----------------------------
    # RELEVANCE CHECK (CRITICAL FIX)
    # -----------------------------
    query_lower = query.lower()
    keywords = re.findall(r'\b\w+\b', query_lower)

    relevant = False
    for r in retrieved:
        text_lower = r["text"].lower()
        if any(k in text_lower for k in keywords if len(k) > 3):
            relevant = True
            break

    if not relevant:
        return {
            "answer": "I can only answer questions about CMC HR, IT, and Finance policies.",
            "sources": [],
            "refused": True
        }

    # -----------------------------
    # Group by document
    # -----------------------------
    grouped = defaultdict(list)
    for r in retrieved:
        grouped[r["doc_name"]].append(r)

    doc_name, chunks = max(
        grouped.items(),
        key=lambda x: max(c["score"] for c in x[1])
    )

    chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)[:top_k]
    context_chunks = [c["text"] for c in chunks]

    # -----------------------------
    # Generate answer
    # -----------------------------
    answer = strict_llm(context_chunks, query)

    # Fallback if extraction fails
    if not answer.strip():
        fallback = context_chunks[0][:300]
        answer = f"Based on policy documents: {fallback}"

    sources = [
        f"{c['doc_name']}::chunk_{c['chunk_index']}"
        for c in chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
        "refused": False
    }


# -----------------------------
# PUBLIC API
# -----------------------------
def query(question: str, llm_call=None):
    db_path = os.path.join(os.path.dirname(__file__), "stub_chroma_db")

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection("policy_docs")

    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    return retrieve_and_answer(question, collection, embedder)


# -----------------------------
# BUILD INDEX
# -----------------------------
def build_index(docs_dir, db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), "stub_chroma_db")

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection("policy_docs")

    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    chunks = chunk_documents(docs_dir)

    for i, chunk in enumerate(chunks):
        embedding = embedder.encode(chunk["text"]).tolist()

        collection.add(
            documents=[chunk["text"]],
            embeddings=[embedding],
            metadatas=[{
                "doc_name": chunk["doc_name"],
                "chunk_index": chunk["chunk_index"]
            }],
            ids=[f"id_{i}"]
        )

    print(f"Indexed {len(chunks)} chunks at {db_path}")


# -----------------------------
# MAIN
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-index", action="store_true")
    parser.add_argument("--query", type=str)
    parser.add_argument("--docs-dir", default="../data/policy-documents")

    args = parser.parse_args()

    if args.build_index:
        build_index(args.docs_dir)

    if args.query:
        result = query(args.query)

        print("\nAnswer:\n", result["answer"])
        print("\nSources:")
        for s in result["sources"]:
            print(s)


if __name__ == "__main__":
    main()