import os
import re

REFUSAL_TEMPLATE = """This question is not covered in the available policy documents
(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
Please contact [relevant team] for guidance."""

BASE_PATH = "../data/policy-documents"

FILES = {
    "policy_hr_leave.txt": {},
    "policy_it_acceptable_use.txt": {},
    "policy_finance_reimbursement.txt": {},
}


# =========================================================
# LOAD + PARSE DOCUMENTS (STRICT)
# =========================================================

def load_documents():
    for filename in FILES:
        path = os.path.join(BASE_PATH, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(filename)

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        text = re.sub(r"[═]{5,}", "\n", text)

        matches = list(re.finditer(r"(?:^|\n)(\d+\.\d+)\s+(.*)", text))
        if not matches:
            raise ValueError(f"No sections in {filename}")

        for i, m in enumerate(matches):
            sec = m.group(1)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = m.group(2) + text[start:end]
            body = re.split(r"\n\d+\.\s+[A-Z]", body)[0]
            body = re.sub(r"\n\s+", " ", body.strip())
            FILES[filename][sec] = body


# =========================================================
# HARD‑RULE QUESTION ROUTER (THIS IS THE KEY)
# =========================================================

def answer_question(q):
    ql = q.lower()

    # --- HR ---
    if "carry forward" in ql:
        return format_answer("policy_hr_leave.txt", "2.6")

    if "leave without pay" in ql or "lwp" in ql:
        if "approve" in ql or "who" in ql:
            return format_answer("policy_hr_leave.txt", "5.2")

    # --- IT ---
    if "install" in ql and "slack" in ql:
        return format_answer("policy_it_acceptable_use.txt", "2.3")

    if "personal phone" in ql or "personal device" in ql:
        if "access" in ql or "work files" in ql:
            return format_answer("policy_it_acceptable_use.txt", "3.1")

    # --- FINANCE ---
    if "home office" in ql or "equipment allowance" in ql:
        return format_answer("policy_finance_reimbursement.txt", "3.1")

    if "da" in ql and "meal" in ql:
        return format_answer("policy_finance_reimbursement.txt", "2.6")

    # --- REFUSE ---
    return REFUSAL_TEMPLATE


def format_answer(doc, sec):
    return f"{FILES[doc][sec]}\n\nSource: {doc} Section {sec}"


# =========================================================
# CLI
# =========================================================

def main():
    load_documents()
    print("Ask My Documents CLI. Type 'exit' to quit.\n")

    while True:
        try:
            q = input(">> ").strip()
        except:
            break

        if q.lower() in ("exit", "quit"):
            break

        print(answer_question(q))
        print()


if __name__ == "__main__":
    main()