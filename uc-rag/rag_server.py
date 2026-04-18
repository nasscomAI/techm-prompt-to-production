"""
UC-RAG — RAG Server
rag_server.py — Full Implementation

Stack:
  pip3 install sentence-transformers chromadb
  LLM: set your API key in llm_adapter.py (../uc-mcp/llm_adapter.py)
       or set environment variable GEMINI_API_KEY
"""

import argparse
import os
import sys
import re

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Please install requirements: pip3 install sentence-transformers chromadb")
    sys.exit(1)


# --- SKILL: chunk_documents ---
def chunk_documents(docs_dir: str, max_tokens: int = 400, overlap_tokens: int = 0) -> list[dict]:
    """
    Load all .txt files from docs_dir.
    Split each into chunks of max_tokens with overlap_tokens.
    Uses a sliding window of sentences to improve score density.
    Return list of: {doc_name, chunk_index, text}
    """
    chunks = []
    if not os.path.exists(docs_dir):
        print(f"Error: Directory {docs_dir} not found.")
        return chunks
        
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            
        # Clean up text: remove decorative bars and normalize whitespace
        text = re.sub(r'[═─]{3,}', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunk_idx = 0
        current_sentences = []
        current_length = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i].strip()
            if not sentence:
                i += 1
                continue
                
            sent_words = sentence.split()
            sent_len = len(sent_words)
            
            # If a single sentence is huge, we treat it as its own chunk
            if sent_len > max_tokens:
                chunks.append({
                    "doc_name": filename,
                    "chunk_index": chunk_idx,
                    "text": sentence
                })
                chunk_idx += 1
                i += 1
                continue
            
            # Add to current chunk if space allows
            if current_length + sent_len <= max_tokens:
                current_sentences.append(sentence)
                current_length += sent_len
                i += 1
            else:
                # Store the chunk
                chunks.append({
                    "doc_name": filename,
                    "chunk_index": chunk_idx,
                    "text": " ".join(current_sentences)
                })
                chunk_idx += 1
                
                # Backtrack for overlap
                # Find how many sentences to keep to get ~overlap_tokens
                overlap_count = 0
                overlap_sent_list = []
                # Go backwards through current_sentences
                for s in reversed(current_sentences):
                    s_len = len(s.split())
                    if overlap_count + s_len <= overlap_tokens:
                        overlap_sent_list.insert(0, s)
                        overlap_count += s_len
                    else:
                        break
                
                current_sentences = overlap_sent_list
                current_length = overlap_count
                # i doesn't advance; we continue from where we left off but with overlap buffer
                # Actually, i should have advanced in the "if" above.
                # The logic should be: if we can't add more, we save and THEN continue.
                # So the "else" should NOT increment i.
            
        # Add final chunk if not empty
        if current_sentences:
            chunks.append({
                "doc_name": filename,
                "chunk_index": chunk_idx,
                "text": " ".join(current_sentences)
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
    Filter chunks below threshold.
    If no chunks pass threshold, return refusal template.
    Otherwise call llm with retrieved chunks as context only.
    Return: {answer, cited_chunks: [{doc_name, chunk_index, score}]}
    """
    query_embedding = embedder.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    distances = results['distances'][0] if results['distances'] else []
    documents = results['documents'][0] if results['documents'] else []
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    
    valid_chunks = []
    cited_chunks = []
    
    for doc, meta, dist in zip(documents, metadatas, distances):
        similarity = 1.0 - dist
        print(f"DEBUG: Chunk similarity: {similarity:.4f} | {meta['doc_name']} (Chunk {meta['chunk_index']})")
        if similarity >= threshold:
            valid_chunks.append(doc)
            cited_chunks.append({
                "doc_name": meta["doc_name"],
                "chunk_index": meta["chunk_index"],
                "score": round(similarity, 3)
            })
            
    if not valid_chunks:
        print(f"DEBUG: No chunks passed threshold {threshold}")
        sources_str = ", ".join([f'{m["doc_name"]} (Chunk {m["chunk_index"]})' for m in metadatas]) if metadatas else "None"
        template = (
            "This question is not covered in the retrieved policy documents. "
            f"Retrieved chunks: [{sources_str}]. Please contact the relevant department for guidance."
        )
        return {"answer": template, "cited_chunks": [], "refused": True}
        
    context_str = "\n\n---\n\n".join(valid_chunks)
    
    prompt = f"""
ROLE: A retrieval-augmented policy assistant that answers queries from City Municipal Corporation staff regarding HR, IT, and Finance policies by consulting the correct policy documents.

INTENT: Provide accurate policy answers that strictly adhere to the provided documents, including document name and chunk index citations, and to explicitly refuse to answer queries that are not covered within the retrieved policy context.

CONTEXT:
The agent must rely ONLY on the text contained within the retrieved document chunks below. General knowledge or standard practices must never be used to synthesize answers.
{context_str}

ENFORCEMENT RULES:
1. Every answer must cite the source document name and chunk index.
2. Answer must use only information present in the retrieved chunks. Never add context from outside the retrieved set.
3. If the query spans two documents - retrieve from each separately. Never merge retrieved chunks from different documents into one answer.

USER QUERY:
{query}
"""
    answer = llm_call(prompt)
    return {"answer": answer, "cited_chunks": cited_chunks, "refused": False}


def query(question: str, llm_call):
    """
    Helper function for MCP server integration.
    Initializes ChromaDB and embedder, then retrieves and answers.
    """
    db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    try:
        collection = client.get_collection(name="policy_documents")
    except Exception:
        return {"answer": "ChromaDB index not found. Please build index first.", "cited_chunks": [], "refused": True}
        
    embedder = SentenceTransformer('BAAI/bge-small-en-v1.5')
    return retrieve_and_answer(question, collection, embedder, llm_call)


# --- INDEX BUILDER ---
def build_index(docs_dir: str, db_path: str = "./chroma_db"):
    """
    Chunk all documents and store embeddings in ChromaDB.
    Called once before querying.
    """
    embedder = SentenceTransformer('BAAI/bge-small-en-v1.5')
    client = chromadb.PersistentClient(path=db_path)
    
    collection = client.get_or_create_collection(
        name="policy_documents",
        metadata={"hnsw:space": "cosine"}
    )
    
    chunks = chunk_documents(docs_dir)
    print(f"Generated {len(chunks)} chunks.")
    if not chunks: 
        return
    
    texts = [c["text"] for c in chunks]
    metadatas = [{"doc_name": c["doc_name"], "chunk_index": c["chunk_index"]} for c in chunks]
    ids = [f'{c["doc_name"]}_chunk_{c["chunk_index"]}' for c in chunks]
    
    print("Embedding chunks and storing in ChromaDB...")
    embeddings = embedder.encode(texts).tolist()
    
    collection.upsert(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )


# --- NAIVE MODE ---
def naive_query(query: str, docs_dir: str, llm_call):
    """
    Load all documents into context without retrieval.
    """
    if not os.path.exists(docs_dir):
        return "Docs dir not found."
    texts = []
    for filename in sorted(os.listdir(docs_dir)):
        if filename.endswith(".txt"):
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                texts.append(f"--- {filename} ---\n{f.read()}")
    
    context = "\n\n".join(texts)
    prompt = f"Answer this query:\n{query}\n\nUsing this text:\n{context}"
    return llm_call(prompt)


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
        # Set UTF-8 encoding for stdout to avoid charmap errors on Windows
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        if args.naive:
            sys.path.insert(0, "../uc-mcp")
            try:
                from llm_adapter import call_llm
            except ImportError:
                print("Could not import llm_adapter. Check path.")
                sys.exit(1)
                
            result = naive_query(args.query, args.docs_dir, call_llm)
            print(f"\nNaive answer:\n{result}")
        else:
            sys.path.insert(0, "../uc-mcp")
            try:
                from llm_adapter import call_llm
            except ImportError:
                print("Could not import llm_adapter. Check path.")
                sys.exit(1)
                
            client = chromadb.PersistentClient(path=args.db_path)
            try:
                collection = client.get_collection(name="policy_documents")
                print(f"Collection count: {collection.count()}")
            except Exception:
                print("Error: Collection not found. Run --build-index first.")
                sys.exit(1)
                
            embedder = SentenceTransformer('BAAI/bge-small-en-v1.5')
            
            res = retrieve_and_answer(args.query, collection, embedder, call_llm)
            
            # Debug: Print all retrieved chunks and their similarities
            print("\n--- Retrieval Debug ---")
            query_embedding = embedder.encode([args.query]).tolist()
            debug_results = collection.query(query_embeddings=query_embedding, n_results=5)
            for doc, meta, dist in zip(debug_results['documents'][0], debug_results['metadatas'][0], debug_results['distances'][0]):
                similarity = 1.0 - dist
                print(f"Score: {similarity:.3f} | {meta['doc_name']} (Chunk {meta['chunk_index']})")
                print(f"TEXT:\n{doc}")
                print("-" * 40)

            print("\n---------- RAG ANSWER ----------\n")
            print(res["answer"])
            print("\n--------------------------------")
            if res["cited_chunks"]:
                print("\nSources Cited:")
                for c in res["cited_chunks"]:
                    print(f"- {c['doc_name']} (Chunk {c['chunk_index']}, Match: {c['score']})")
            print("\n")


if __name__ == "__main__":
    main()
