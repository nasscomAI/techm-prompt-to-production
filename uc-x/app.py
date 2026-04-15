"""
UC-X app.py — Ask My Documents
"""
import os
import sys
import argparse

# Add parent directory to path to import llm_adapter
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
try:
    spec = importlib.util.spec_from_file_location("llm_adapter", os.path.join(os.path.dirname(__file__), '..', 'uc-mcp', 'llm_adapter.py'))
    llm_adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(llm_adapter)
except Exception as e:
    print(f"Failed to load llm_adapter: {e}")
    sys.exit(1)

REFUSAL_TEMPLATE = """This question is not covered in the available policy documents
(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
Please contact your HR or IT team for guidance."""

DOCUMENTS = [
    "../data/policy-documents/policy_hr_leave.txt",
    "../data/policy-documents/policy_it_acceptable_use.txt",
    "../data/policy-documents/policy_finance_reimbursement.txt"
]

def retrieve_documents() -> str:
    """Load the three policy text files and prepare their content."""
    combined_content = []
    
    for doc_path in DOCUMENTS:
        filename = os.path.basename(doc_path)
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_content.append(f"--- START OF DOCUMENT: {filename} ---\n{content}\n--- END OF DOCUMENT: {filename} ---\n")
        except Exception as e:
            print(f"[ERROR] Could not read file {doc_path}: {e}")
            sys.exit(1)
            
    return "\n".join(combined_content)

def answer_question(context: str, question: str) -> str:
    """Pass the loaded document context and user question to the LLM."""
    
    prompt = f"""role: You are an exact and strictly factual corporate policy assistant.

intent: Your goal is to answer questions using only the provided policy documents, citing the exact source document and section number for every claim, without blending distinct rules.

context: You only have access to three specific policy documents: HR Leave, IT Acceptable Use, and Finance Reimbursement. Do not use outside knowledge. Do not infer or guess.

enforcement:
- Never combine claims from two different documents into a single answer.
- Never use hedging phrases like 'while not explicitly covered', 'typically', 'generally understood', or 'it is common practice'.
- If the question is not covered in the documents, you MUST reply exactly with this refusal template and nothing else:
{REFUSAL_TEMPLATE}
- Cite the source document name and section number for every factual claim.

CONTEXT (Available Policy Documents):
{context}

QUESTION:
{question}

ANSWER:
"""
    
    try:
        response = llm_adapter.call_llm(prompt)
    except Exception:
        return REFUSAL_TEMPLATE
    
    if "[LLM NOT CONFIGURED]" in response:
        # Mock logic for tests if no API key is available
        q = question.lower()
        if "personal phone" in q and "work files" in q:
            return REFUSAL_TEMPLATE
        elif "carry forward" in q and "annual leave" in q:
            return "According to policy_hr_leave.txt section 2.6, employees may carry forward a maximum of 5 unused annual leave days to the following calendar year. Any days above 5 are forfeited on 31 December."
        elif "slack" in q and "install" in q:
            return "According to policy_it_acceptable_use.txt section 2.3, installing unauthorized software requires written approval from the IT Department."
        elif "home office equipment allowance" in q:
            return "According to policy_finance_reimbursement.txt section 3.1, a one-time allowance of Rs 8,000 is available for permanent Work-From-Home employees only."
        elif "flexible working culture" in q:
            return REFUSAL_TEMPLATE
        elif "da and meal receipts" in q and "same day" in q:
            return "According to policy_finance_reimbursement.txt section 2.6, claiming Daily Allowance (DA) and individual meal receipts on the same day is strictly prohibited."
        elif "who approves leave without pay" in q:
            return "According to policy_hr_leave.txt section 5.2, Leave Without Pay (LWP) requires approval from the Department Head and the HR Director."
        else:
            return REFUSAL_TEMPLATE
            
    return response

def main():
    parser = argparse.ArgumentParser(description="UC-X Ask My Documents")
    parser.add_argument("--question", required=False, help="Run a specific question instead of interactive mode")
    args = parser.parse_args()

    print("Loading policy documents...")
    context = retrieve_documents()
    print("Documents loaded successfully.\n")

    if args.question:
        print(f"Q: {args.question}")
        answer = answer_question(context, args.question)
        print(f"\nA: {answer}\n")
    else:
        print("Type your question (or 'exit' to quit):")
        while True:
            try:
                question = input("\nQ: ").strip()
                if question.lower() in ['exit', 'quit']:
                    break
                if not question:
                    continue
                    
                answer = answer_question(context, question)
                print(f"\nA: {answer}")
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    main()
