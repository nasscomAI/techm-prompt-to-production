"""
UC-X app.py
Interactive CLI to answer questions from policy documents.
Built according to RICE + agents.md + skills.md + CRAFT workflow.
"""
import os
import sys
import re

def retrieve_documents(file_paths):
    """
    Loads all 3 policy files and indexes them by document name and section number.
    Returns: A dictionary mapping document names to their sections.
    """
    indexed_docs = {}
    for path in file_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File missing: {path}")
        filename = os.path.basename(path)
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Documents are formatted with ═ barriers around section titles
        parts = content.split("═══════════════════════════════════════════════════════════")
        
        doc_index = {}
        for i in range(1, len(parts)-1, 2):
            section_title = parts[i].strip()
            section_content = parts[i+1].strip()
            
            # Extract section number like '1.', '2.', etc.
            match = re.match(r"^(\d+)\.", section_title)
            sec_num = match.group(1) if match else section_title
            
            doc_index[sec_num] = f"{section_title}\n{section_content}"
            
        indexed_docs[filename] = doc_index
        
    return indexed_docs

def call_llm(prompt: str) -> str:
    """
    Calls Gemini, OpenAI, or Anthropic REST APIs directly using Python's built-in urllib.
    Requires no external SDKs.
    """
    import urllib.request
    import json
    import os
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={gemini_key}"
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0}
        }
        req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"[GEMINI API ERROR] {str(e)}"
            
    elif openai_key:
        url = "https://api.openai.com/v1/chat/completions"
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_key}"
        }
        req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[OPENAI API ERROR] {str(e)}"
            
    elif anthropic_key:
        url = "https://api.anthropic.com/v1/messages"
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                return result["content"][0]["text"]
        except Exception as e:
            return f"[ANTHROPIC API ERROR] {str(e)}"
            
    else:
        return (
            "[ERROR] No LLM API Key found!\n\n"
            "To run this application, you must provide an API key.\n"
            "You can get a free Gemini API key in under a minute:\n"
            "1. Go to https://aistudio.google.com/app/apikey\n"
            "2. Sign in and click 'Create API key'\n"
            "3. Copy the key and create a .env file in this directory with:\n"
            "   GEMINI_API_KEY=your_copied_key_here\n\n"
            "Alternatively, you can provide an OPENAI_API_KEY or ANTHROPIC_API_KEY in the .env file."
        )

def answer_question(query, docs):
    """
    Constructs the prompt and searches indexed documents to find an answer,
    returning either a single-source answer with a citation or the exact refusal template.
    """
    context_text = ""
    for doc_name, sections in docs.items():
        context_text += f"\n--- DOCUMENT: {doc_name} ---\n"
        for sec_num, text in sections.items():
            context_text += f"[{doc_name} - Section {sec_num}]\n{text}\n\n"

    prompt = f"""Role: You are a strict, authoritative assistant answering company policy inquiries. Your operational boundary is strictly limited to querying the provided policy documents to find direct answers. You must act as a precise retrieval system, not a reasoning or advisory engine.

Intent: A correct output provides an exact, factual answer sourced from a single policy document, accompanied by a precise citation (document name and section number). If the answer cannot be found in a single document, the output is strictly the verbatim refusal template.

Context: You are allowed to use ONLY the following policy documents provided below. You are EXPLICITLY FORBIDDEN from using outside knowledge, common practice, inferences, or combining information from multiple documents to form an answer.

{context_text}

Enforcement Rules:
1. Never combine claims from two different documents into a single answer.
2. Never use hedging phrases: "while not explicitly covered", "typically", "generally understood", "it is common practice".
3. Cite source document name + section number for every factual claim.
4. If question is not in the documents — use the refusal template exactly, no variations:
"This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance."

Question: {query}
Answer:"""

    response = call_llm(prompt)
    return response.strip()

def main():
    from dotenv import load_dotenv
    load_dotenv()  # Loads variables from a .env file if it exists

    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.abspath(os.path.join(base_dir, "../data/policy-documents"))
    files = [
        os.path.join(docs_dir, "policy_hr_leave.txt"),
        os.path.join(docs_dir, "policy_it_acceptable_use.txt"),
        os.path.join(docs_dir, "policy_finance_reimbursement.txt")
    ]
    
    # 1. Retrieve Documents
    try:
        docs = retrieve_documents(files)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    # 2. Interactive Loop
    print("Welcome to UC-X: Ask My Documents")
    print("Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            query = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
            
        if not query:
            continue
        if query.lower() in ["exit", "quit"]:
            break
            
        print("Thinking...")
        answer = answer_question(query, docs)
        print(f"\nAnswer:\n{answer}")

if __name__ == "__main__":
    main()
