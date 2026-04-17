"""
UC-X app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import os
import re
import sys

# -----------------------------
# CONSTANTS
# -----------------------------
DATA_PATH = "../data/policy-documents"

FILES = {
    "policy_hr_leave.txt": os.path.join(DATA_PATH, "policy_hr_leave.txt"),
    "policy_it_acceptable_use.txt": os.path.join(DATA_PATH, "policy_it_acceptable_use.txt"),
    "policy_finance_reimbursement.txt": os.path.join(DATA_PATH, "policy_finance_reimbursement.txt"),
}

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). "
    "Please contact [relevant team] for guidance."
)

FORBIDDEN_PHRASES = [
    "while not explicitly covered",
    "typically",
    "generally understood",
    "it is common practice"
]

# -----------------------------
# SKILL 1: retrieve_documents
# -----------------------------
def retrieve_documents():
    documents = {}

    for doc_name, path in FILES.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing document: {doc_name}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            raise IOError(f"Unable to read document: {doc_name}")

        # Parse sections like "2.6", "3.1" etc.
        sections = {}
        matches = re.split(r'(\n?\d+\.\d+\s)', content)

        if len(matches) < 2:
            raise ValueError(f"Invalid document format (no sections found): {doc_name}")

        current_section = None

        for part in matches:
            section_match = re.match(r'\n?(\d+\.\d+)\s', part)
            if section_match:
                current_section = section_match.group(1)
                sections[current_section] = ""
            else:
                if current_section:
                    sections[current_section] += part.strip() + " "

        if not sections:
            raise ValueError(f"Invalid document format: {doc_name}")

        documents[doc_name] = sections

    return documents

# -----------------------------
# HELPER: simple keyword match
# -----------------------------
def match_sections(question, documents):
    q = question.lower()
    results = {}

    for doc_name, sections in documents.items():
        matched_sections = []

        for sec_num, text in sections.items():
            text_lower = text.lower()

            # naive keyword overlap
            score = sum(1 for word in q.split() if word in text_lower)

            if score > 0:
                matched_sections.append((sec_num, text, score))

        if matched_sections:
            # sort by relevance
            matched_sections.sort(key=lambda x: x[2], reverse=True)
            results[doc_name] = matched_sections

    return results

# -----------------------------
# SKILL 2: answer_question
# -----------------------------
def answer_question(question, documents):
    if not question or not isinstance(question, str) or not question.strip():
        return REFUSAL_TEMPLATE

    matches = match_sections(question, documents)

    if not matches:
        return REFUSAL_TEMPLATE

    # ENFORCEMENT: single document only
    if len(matches.keys()) > 1:
        return REFUSAL_TEMPLATE

    doc_name = list(matches.keys())[0]
    sections = matches[doc_name]

    if not sections:
        return REFUSAL_TEMPLATE

    # take best section only (avoid condition dropping / blending)
    best_section = sections[0]
    sec_num, text, _ = best_section

    if not text.strip():
        return REFUSAL_TEMPLATE

    # Build answer with citation
    answer = text.strip()

    # ENFORCEMENT: citation required
    answer_with_citation = f"{answer} (Source: {doc_name}, Section {sec_num})"

    # ENFORCEMENT: check forbidden phrases
    for phrase in FORBIDDEN_PHRASES:
        if phrase in answer_with_citation.lower():
            return REFUSAL_TEMPLATE

    return answer_with_citation

# -----------------------------
# MAIN CLI
# -----------------------------
def main():
    try:
        documents = retrieve_documents()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    print("Ask your questions (type 'exit' to quit):")

    while True:
        try:
            question = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if question.lower() in ["exit", "quit"]:
            print("Exiting.")
            break

        answer = answer_question(question, documents)

        # Final enforcement check: ensure citation exists unless refusal
        if answer != REFUSAL_TEMPLATE:
            if "Source:" not in answer or "Section" not in answer:
                answer = REFUSAL_TEMPLATE

        print(answer)




if __name__ == "__main__":
    main()
