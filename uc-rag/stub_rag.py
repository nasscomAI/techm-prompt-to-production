"""
UC-RAG — stub_rag.py
Fully working RAG implementation against the policy documents.

USE THIS IF:
- Your rag_server.py is not yet working
- You want to proceed to UC-MCP without finishing UC-RAG
- You want to compare your implementation against a reference

UC-MCP imports from this file by default.
To use your own rag_server.py in UC-MCP, update uc-mcp/mcp_server.py:
  change: from stub_rag import query as rag_query
  to:     from rag_server import query as rag_query   (once your server works)

Requirements:
  pip3 install sentence-transformers chromadb
"""

import os
from stub_chroma_db import StubChromaDB
from sentence_transformers import SentenceTransformer
from rag_server import chunk_documents, retrieve_and_answer

# Initialize ChromaDB and SentenceTransformer
chroma_db = StubChromaDB()
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Preprocess documents
docs_dir = os.path.join(os.path.dirname(__file__), "../data/policy-documents")
chunks = chunk_documents(docs_dir)

# Add chunks to ChromaDB
for chunk in chunks:
    embedding = embedder.encode(chunk["text"])
    chroma_db.add(chunk["doc_name"], chunk["chunk_index"], chunk["text"], embedding)

# Query function
def query(question):
    return retrieve_and_answer(
        query=question,
        collection=chroma_db,
        embedder=embedder,
        llm_call=lambda prompt: "This is a simulated LLM response.",
        top_k=3,
        threshold=0.6
    )

# Example usage
if __name__ == "__main__":
    print(query("Who approves leave without pay?"))
