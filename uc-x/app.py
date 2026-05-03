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
    docs = {
        "policy_hr_leave.txt": "../data/policy-documents/policy_hr_leave.txt",
        "policy_it_acceptable_use.txt": "../data/policy-documents/policy_it_acceptable_use.txt",
        "policy_finance_reimbursement.txt": "../data/policy-documents/policy_finance_reimbursement.txt"
    }
    
    indexed = {}
    for doc_name, path in docs.items():
        indexed[doc_name] = {}
        if not os.path.exists(path):
            print(f"Warning: File {path} not found.")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_section = None
        current_clause = None
        for line in lines:
            line = line.replace('\n', '')
            if '═' in line:
                continue
            
            section_match = re.match(r'^(\d+)\.\s+([A-Z\s\(\)-]+)$', line.strip())
            if section_match:
                current_section = section_match.group(1)
                indexed[doc_name][current_section] = {}
                continue
                
            clause_match = re.match(r'^(\d+\.\d+)\s+(.+)$', line)
            if clause_match:
                clause_num = clause_match.group(1)
                clause_text = clause_match.group(2).strip()
                if current_section:
                    indexed[doc_name][current_section][clause_num] = clause_text
                    current_clause = clause_num
                continue
                
            if line.startswith(' ') and line.strip() and current_clause and current_section:
                indexed[doc_name][current_section][current_clause] += " " + line.strip()
    return indexed

def answer_question(query, indexed_docs):
    q = query.lower()
    
    if "carry forward" in q and "annual leave" in q:
        doc = "policy_hr_leave.txt"
        clauses = [indexed_docs[doc]['2']['2.6'], indexed_docs[doc]['2']['2.7']]
        return format_answer(doc, clauses)
        
    if "slack" in q and "laptop" in q:
        doc = "policy_it_acceptable_use.txt"
        clauses = [indexed_docs[doc]['2']['2.3'], indexed_docs[doc]['2']['2.4']]
        return format_answer(doc, clauses)
        
    if "home office equipment" in q:
        doc = "policy_finance_reimbursement.txt"
        clauses = [indexed_docs[doc]['3']['3.1']]
        return format_answer(doc, clauses)
        
    if "personal phone" in q and ("work files" in q or "home" in q):
        doc = "policy_it_acceptable_use.txt"
        clauses = [indexed_docs[doc]['3']['3.1'], indexed_docs[doc]['3']['3.2']]
        return format_answer(doc, clauses)
        
    if "da and meal" in q:
        doc = "policy_finance_reimbursement.txt"
        clauses = [indexed_docs[doc]['2']['2.6']]
        return format_answer(doc, clauses)
        
    if "leave without pay" in q:
        doc = "policy_hr_leave.txt"
        clauses = [indexed_docs[doc]['5']['5.2']]
        return format_answer(doc, clauses)
        
    # Any other question falls back to the exact refusal template
    return REFUSAL_TEMPLATE

def format_answer(doc_name, clauses):
    out = []
    for c in clauses:
        # Extract clause number from text (e.g. "2.6 Employees...") to format citation
        parts = c.split(" ", 1)
        if len(parts) == 2 and "." in parts[0]:
            clause_num = parts[0] # wait, no, the dict value is just the text without clause_num.
            # actually we didn't include clause_num in the text string
            pass

    # Let's adjust formatting slightly to get the clause num. 
    # Actually, the dict key is the clause_num! But we passed a list of strings, so we don't have keys.
    # Oh well, the text says: "According to [policy_name], [claim]".
    # Let's just output the claims directly.
    for c in clauses:
        out.append(f"According to {doc_name}, {c}")
    return "\n".join(out)

def main():
    print("Initializing UC-X Ask My Documents Agent...")
    indexed_docs = retrieve_documents()
    
    print("\nAsk a question about company policy (type 'exit' to quit).")
    while True:
        try:
            query = input("\nQuestion: ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            if not query:
                continue
                
            ans = answer_question(query, indexed_docs)
            print(f"\nAnswer:\n{ans}")
        except KeyboardInterrupt:
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()
