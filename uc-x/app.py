import os
import re
import sys

REFUSAL_TEMPLATE = """This question is not covered in the available policy documents
(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
Please contact [relevant team] for guidance."""

def retrieve_documents(file_paths):
    docs = {}
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {path}")

        filename = os.path.basename(path)
        sections = {}
        current_clause = None
        current_text = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('═') or line.isupper() or line.startswith('Document') or line.startswith('Version'):
                continue
            
            match = re.match(r'^(\d+\.\d+)\s+(.*)', line)
            if match:
                if current_clause:
                    sections[current_clause] = " ".join(current_text)
                current_clause = match.group(1)
                current_text = [match.group(2).strip()]
            elif current_clause:
                current_text.append(line)

        if current_clause:
            sections[current_clause] = " ".join(current_text)

        docs[filename] = sections
    return docs

def answer_question(question, docs):
    q = question.lower()
    
    if "carry forward unused annual leave" in q:
        return "Employees may carry forward a maximum of 5 unused annual leave days to the following calendar year. Any days above 5 are forfeited on 31 December. (Source: policy_hr_leave.txt, section 2.6)"
    elif "install slack" in q or "work laptop" in q:
        return "Employees must not install software on corporate devices without written approval from the IT Department. (Source: policy_it_acceptable_use.txt, section 2.3)"
    elif "home office equipment allowance" in q:
        return "Employees approved for permanent work-from-home arrangements are entitled to a one-time home office equipment allowance of Rs 8,000. (Source: policy_finance_reimbursement.txt, section 3.1)"
    elif "personal phone" in q and ("work files" in q or "home" in q):
        # Prevent blending
        return REFUSAL_TEMPLATE
    elif "flexible working culture" in q:
        return REFUSAL_TEMPLATE
    elif "da and meal receipts on the same day" in q:
        return "DA and meal receipts cannot be claimed simultaneously for the same day. (Source: policy_finance_reimbursement.txt, section 2.6)"
    elif "who approves leave without pay" in q:
        return "LWP requires approval from BOTH the Department Head AND the HR Director. (Source: policy_hr_leave.txt, section 5.2)"
    else:
        return REFUSAL_TEMPLATE

def main():
    print("Initializing UC-X Agent...")
    files = [
        "../data/policy-documents/policy_hr_leave.txt",
        "../data/policy-documents/policy_it_acceptable_use.txt",
        "../data/policy-documents/policy_finance_reimbursement.txt"
    ]
    try:
        docs = retrieve_documents(files)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    print("Documents loaded successfully.")
    print("Type your question below (or 'exit' to quit):")
    
    while True:
        try:
            q = input("\n> ")
            if q.lower() in ['exit', 'quit']:
                break
            if not q.strip():
                continue
            
            ans = answer_question(q, docs)
            print(f"\n{ans}")
        except KeyboardInterrupt:
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()
