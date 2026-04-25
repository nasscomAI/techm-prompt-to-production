"""
UC-X — Ask My Documents
RAG over CMC policy documents with RICE enforcement.
"""
import os
import anthropic

POLICY_FILES = {
    "policy_hr_leave.txt": "HR Leave Policy (HR-POL-001)",
    "policy_it_acceptable_use.txt": "IT Acceptable Use Policy (IT-POL-003)",
    "policy_finance_reimbursement.txt": "Finance Expense Reimbursement Policy (FIN-POL-007)",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "policy-documents")

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). "
    "Please contact the relevant team for guidance."
)

# RICE system prompt
SYSTEM_PROMPT = f"""
ROLE
You are a policy document assistant for City Municipal Corporation (CMC) employees.
You answer questions strictly and only from the three CMC policy documents provided below.
You have no access to external knowledge, general HR/IT norms, or any information outside these documents.

INTENT
For every question, produce exactly one of two outputs:
1. A direct factual answer drawn from a SINGLE document, prefixed with the document filename and section number.
2. The exact refusal template when the question is not answered in any document.

A correct answer is verifiable: a reader must be able to open the cited document, find the cited section, and confirm the claim word-for-word.

CONTEXT
You have access to exactly these three documents (provided in full below):
- policy_hr_leave.txt — HR Leave Policy (HR-POL-001)
- policy_it_acceptable_use.txt — IT Acceptable Use Policy (IT-POL-003)
- policy_finance_reimbursement.txt — Finance Expense Reimbursement Policy (FIN-POL-007)

All information you use must come from these documents and only these documents.

ENFORCEMENT — these rules are absolute:
1. SINGLE SOURCE: Every answer must draw from exactly one document. Never combine or blend information from two different documents into a single answer. If partial information exists in two documents, answer only from the single most directly relevant document, or use the refusal template.
2. NO HEDGING: You must never use any of the following phrases or paraphrases of them: "while not explicitly covered", "typically", "generally understood", "it is common practice", "usually", "in general", "it can be assumed", "it would be reasonable to conclude".
3. EXACT REFUSAL: If the question is not answered in any of the three documents, respond with EXACTLY this text and nothing else:
   "{REFUSAL_TEMPLATE}"
4. CITE ALWAYS: Every factual claim must be introduced with the document filename and section number in the format: "(policy_<name>.txt section X.Y)". No exceptions.
""".strip()


def retrieve_documents():
    docs = {}
    for filename, label in POLICY_FILES.items():
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            docs[filename] = {"label": label, "content": f.read()}
    return docs


def build_document_context(docs):
    parts = []
    for filename, info in docs.items():
        parts.append(
            f"=== DOCUMENT: {filename} | {info['label']} ===\n{info['content']}"
        )
    return "\n\n".join(parts)


def answer_question(client, question, document_context):
    full_system = SYSTEM_PROMPT + "\n\n" + document_context
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=full_system,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


def main():
    client = anthropic.Anthropic()
    docs = retrieve_documents()
    document_context = build_document_context(docs)

    print("CMC Policy Assistant — Ask Me Anything")
    print("Type your question and press Enter. Type 'quit' to exit.")
    print("-" * 60)

    while True:
        try:
            question = input("\nYour question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        answer = answer_question(client, question, document_context)
        print(f"\nAnswer:\n{answer}")
        print("-" * 60)


if __name__ == "__main__":
    main()
