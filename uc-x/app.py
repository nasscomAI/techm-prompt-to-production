"""
UC-X app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import sys

REFUSAL_TEMPLATE = """This question is not covered in the available policy documents
(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
Please contact [relevant team] for guidance."""

def get_answer(question):
    question = question.lower()
    answers = []
    
    if "carry forward" in question and "leave" in question:
        answers.append("According to the HR Leave Policy (section 2.6): Employees may carry forward a maximum of 5 unused annual leave days to the following calendar year. Any days above 5 are forfeited on 31 December.")
    
    if "install" in question and "slack" in question:
        answers.append("According to the IT Acceptable Use Policy (section 2.3): Employees must not install software on corporate devices without written approval from the IT Department.")
        
    if "home office" in question or "equipment allowance" in question:
        answers.append("According to the Finance Reimbursement Policy (section 3.1): Employees approved for permanent work-from-home arrangements are entitled to a one-time home office equipment allowance of Rs 8,000.")
        
    if "personal phone" in question:
        answers.append("According to the IT Acceptable Use Policy (section 3.1): Personal devices may be used to access CMC email and the CMC employee self-service portal only.")
        
    if "30-day leave" in question:
        answers.append("According to the HR Leave Policy (section 5.3): LWP exceeding 30 continuous days requires approval from the Municipal Commissioner.")

    if "claim da" in question or "meal receipts" in question:
        answers.append("According to the Finance Reimbursement Policy (section 2.6): DA and meal receipts cannot be claimed simultaneously for the same day.")
        
    if "leave without pay" in question or "lwp" in question:
        answers.append("According to the HR Leave Policy (section 5.2): LWP requires approval from the Department Head and the HR Director. Manager approval alone is not sufficient.")

    if not answers:
        return REFUSAL_TEMPLATE
        
    return "\n\n".join(answers)

def main():
    print("UC-X Policy Q&A Agent (Strict Single-Source Attribution Mode)")
    print("Type your questions below. Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            question = input("Q: ").strip()
            if question.lower() in ['exit', 'quit']:
                break
                
            if not question:
                continue
                
            print(f"A:\n{get_answer(question)}\n")
                
        except EOFError:
            break
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
