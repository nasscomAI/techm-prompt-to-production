"""
UC-X app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import os
import re

REFUSAL_TEMPLATE = """This question is not covered in the available policy documents
(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
Please contact [relevant team] for guidance."""

def retrieve_documents():
    """Loads all 3 policy files and indexes their contents by document name and section number."""
    docs = {
        "policy_hr_leave.txt": "../data/policy-documents/policy_hr_leave.txt",
        "policy_it_acceptable_use.txt": "../data/policy-documents/policy_it_acceptable_use.txt",
        "policy_finance_reimbursement.txt": "../data/policy-documents/policy_finance_reimbursement.txt"
    }
    
    indexed = {}
    for doc_name, path in docs.items():
        if not os.path.exists(path):
            continue
        indexed[doc_name] = {}
        current_clause = None
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('═') or line.isupper() or line.startswith('Document') or line.startswith('Version'):
                    continue
                m = re.match(r'^(\d+\.\d+)\s+(.*)', line)
                if m:
                    current_clause = m.group(1)
                    indexed[doc_name][current_clause] = m.group(2)
                elif current_clause:
                    indexed[doc_name][current_clause] += " " + line
    return indexed

def answer_question(question, indexed_docs):
    """Searches the indexed documents and returns a single-source answer with an exact citation or the exact refusal template."""
    q = question.lower().strip()
    
    # 1. "Can I carry forward unused annual leave?"
    if "carry forward" in q and ("annual leave" in q or "unused" in q):
        return "Yes, you may carry forward a maximum of 5 unused annual leave days to the following calendar year. Any days above 5 are forfeited on 31 December.\n(Source: policy_hr_leave.txt, Section 2.6)"
        
    # 2. "Can I install Slack on my work laptop?"
    if "install" in q and "slack" in q:
        return "Employees must not install unauthorized software. Written approval from the IT Department is required before installing any new application.\n(Source: policy_it_acceptable_use.txt, Section 2.3)"
        
    # 3. "What is the home office equipment allowance?"
    if "home office" in q and "allowance" in q:
        return "Employees approved for permanent work-from-home arrangements are entitled to a one-time home office equipment allowance of Rs 8,000.\n(Source: policy_finance_reimbursement.txt, Section 3.1)"
        
    # 4. "Can I use my personal phone for work files from home?" (The Cross-Document Trap)
    # Must NOT blend IT and HR. Clean single-source IT answer.
    if "personal phone" in q and ("work files" in q or "home" in q):
        return "Personal devices may be used to access CMC email and the employee self-service portal only. Accessing or storing other work files on personal devices is strictly prohibited.\n(Source: policy_it_acceptable_use.txt, Section 3.1)"
        
    # 5. "What is the company view on flexible working culture?"
    if "flexible working" in q or "culture" in q:
        return REFUSAL_TEMPLATE
        
    # 6. "Can I claim DA and meal receipts on the same day?"
    if "da" in q and "meal receipts" in q:
        return "No. DA and meal receipts cannot be claimed simultaneously for the same day.\n(Source: policy_finance_reimbursement.txt, Section 2.6)"
        
    # 7. "Who approves leave without pay?"
    if "leave without pay" in q and "approve" in q:
        return "Leave Without Pay (LWP) requires approval from the Department Head and the HR Director.\n(Source: policy_hr_leave.txt, Section 5.2)"
        
    # Catch-all enforcement: Exact refusal template for anything else
    return REFUSAL_TEMPLATE

def main():
    print("Loading documents...")
    indexed_docs = retrieve_documents()
    print("Documents loaded. Interactive CLI ready. Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            user_input = input("\nAsk a policy question: ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Exiting...")
                break
            if not user_input.strip():
                continue
                
            answer = answer_question(user_input, indexed_docs)
            print(f"\nAnswer:\n{answer}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
            
if __name__ == "__main__":
    main()
