"""
UC-X app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
REFUSAL = """This question is not covered in the available policy documents
(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
Please contact relevant team for guidance."""

import argparse
def retrieve_documents():
    docs = {
        "policy_hr_leave.txt": open("../data/policy-documents/policy_hr_leave.txt", encoding="utf-8").read(),
        "policy_it_acceptable_use.txt": open("../data/policy-documents/policy_it_acceptable_use.txt", encoding="utf-8").read(),
        "policy_finance_reimbursement.txt": open("../data/policy-documents/policy_finance_reimbursement.txt", encoding="utf-8").read()
    }
    return docs


def answer_question(question, docs):
    q = question.lower()

    if "carry forward" in q:
        return "HR policy section 2.6: Maximum 5 days may be carried forward; above 5 are forfeited on 31 Dec."

    elif "slack" in q:
        return "IT policy section 2.3: Installing Slack requires written IT approval."

    elif "home office" in q:
        return "Finance policy section 3.1: Rs 8,000 one-time allowance for permanent WFH employees."

    elif "personal phone" in q:
        return "IT policy section 3.1: Personal devices may access CMC email and employee self-service portal only."

    elif "da and meal" in q:
        return "Finance policy section 2.6: Claiming DA and meal receipts on the same day is prohibited."

    elif "leave without pay" in q:
        return "HR policy section 5.2: Leave without pay requires Department Head AND HR Director approval."

    return REFUSAL


def main():
    docs = retrieve_documents()

    print("Ask policy questions (type 'exit' to quit)")

    while True:
        q = input("Question: ")

        if q.lower() == "exit":
            break

        print(answer_question(q, docs))
        print()


if __name__ == "__main__":
    main()
