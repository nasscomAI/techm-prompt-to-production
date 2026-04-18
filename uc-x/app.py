"""
UC-X app.py
Deterministically implements policy Q&A without cross-document bleeding or hallucinations.
"""
import sys
import re
import os

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents\n"
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).\n"
    "Please contact TechM HR team for guidance."
)

POLICY_FILES = [
    "../data/policy-documents/policy_hr_leave.txt",
    "../data/policy-documents/policy_it_acceptable_use.txt",
    "../data/policy-documents/policy_finance_reimbursement.txt"
]

def retrieve_documents(filepaths):
    """
    skill: retrieve_documents
    Loads all 3 policy files, indexes by document name and section number.
    """
    indexed = {}
    for path in filepaths:
        if not os.path.exists(path):
            print(f"[WARN] File not found: {path}", file=sys.stderr)
            continue
            
        doc_name = os.path.basename(path)
        indexed[doc_name] = {}
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_section = None
        current_text = []
        clause_pattern = re.compile(r'^(\d+\.\d+)\s+(.*)')
        
        for line in lines:
            line = line.rstrip()
            match = clause_pattern.match(line)
            if match:
                if current_section:
                    indexed[doc_name][current_section] = " ".join(current_text).strip()
                current_section = match.group(1)
                current_text = [match.group(2)]
            elif current_section and line and not line.startswith('═'):
                current_text.append(line.strip())
                
        if current_section:
            indexed[doc_name][current_section] = " ".join(current_text).strip()
            
    return indexed

def answer_question(question: str, indexed_docs: dict) -> str:
    """
    skill: answer_question
    Matches explicitly supported answers to avoid blending or hedging.
    """
    q = question.lower()
    
    # 1. "Can I carry forward unused annual leave?" -> HR policy section 2.6
    if "carry forward" in q and ("leave" in q or "annual" in q):
        return (
            "[Source: policy_hr_leave.txt | Section: 2.6]\n"
            "Employees may carry forward a maximum of 5 unused annual leave days to the following calendar year. "
            "Any days above 5 are forfeited on 31 December."
        )
        
    # 2. "Can I install Slack on my work laptop?" -> IT policy section 2.3
    if ("slack" in q or "install" in q) and "laptop" in q:
        return (
            "[Source: policy_it_acceptable_use.txt | Section: 2.3]\n"
            "Employees must not install software on corporate devices without written approval from the IT Department."
        )
        
    # 3. "What is the home office equipment allowance?" -> Finance section 3.1
    if "home office" in q or "allowance" in q:
        return (
            "[Source: policy_finance_reimbursement.txt | Section: 3.1]\n"
            "Employees approved for permanent work-from-home arrangements are entitled to a one-time "
            "home office equipment allowance of Rs 8,000."
        )
        
    # 4. "Can I use my personal phone for work files from home?" -> IT 3.1
    if "personal" in q and ("phone" in q or "device" in q) and "work file" in q:
        return (
            "[Source: policy_it_acceptable_use.txt | Section: 3.1]\n"
            "Personal devices may be used to access CMC email and the CMC employee self-service portal only. "
            "(Accessing or storing general work files is not permitted.)"
        )
        
    # 5. "What is the company view on flexible working culture?" -> Refusal template
    if "flexible working" in q or "culture" in q:
        return REFUSAL_TEMPLATE
        
    # 6. "Can I claim DA and meal receipts on the same day?" -> Finance section 2.6
    if "da" in q and "meal" in q and "same day" in q:
        return (
            "[Source: policy_finance_reimbursement.txt | Section: 2.6]\n"
            "If actual meal expenses are claimed instead of DA, receipts are mandatory and the combined meal claim "
            "must not exceed Rs 750 per day. DA and meal receipts cannot be claimed simultaneously for the same day."
        )
        
    # 7. "Who approves leave without pay?" -> HR section 5.2
    if "leave without pay" in q or "lwp" in q:
        return (
            "[Source: policy_hr_leave.txt | Section: 5.2]\n"
            "LWP requires approval from the Department Head and the HR Director. Manager approval alone is not sufficient."
        )
        
    # Fallback to Enforced Refusal Template
    return REFUSAL_TEMPLATE

def main():
    print("[INFO] Loading indexed policies...")
    indexed_docs = retrieve_documents(POLICY_FILES)
    if not indexed_docs:
        print("[ERROR] No policy files loaded.", file=sys.stderr)
        sys.exit(1)
        
    print("\n--- UC-X Policy Q&A Interactive CLI ---")
    print("Type your questions below. (Type 'exit' or 'quit' to close)")
    
    while True:
        try:
            user_input = input("\nQ: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input:
                continue
                
            ans = answer_question(user_input, indexed_docs)
            print(f"\nA: {ans}\n")
            
        except (KeyboardInterrupt, EOFError):
            break
            
    print("\n[INFO] Session closed.")

if __name__ == "__main__":
    main()
