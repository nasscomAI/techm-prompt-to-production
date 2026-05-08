"""
UC-X app.py — Ask My Documents.
Interactive CLI for querying company policy documents.

Run:
    python app.py
"""
import os
import re
import sys

POLICY_FILES = [
    "../data/policy-documents/policy_hr_leave.txt",
    "../data/policy-documents/policy_it_acceptable_use.txt",
    "../data/policy-documents/policy_finance_reimbursement.txt",
]

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents\n"
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).\n"
    "Please contact [relevant team] for guidance."
)

SYSTEM_PROMPT = f"""You are a policy document Q&A agent for CMC company policies.

Your role: Answer employee questions strictly from the three approved policy documents provided. Do not interpret, infer, or blend information across documents.

Rules you must follow:
1. Never combine claims from two different documents into a single answer. Each answer must come from exactly one source document.
2. Never use hedging phrases: "while not explicitly covered", "typically", "generally understood", "it is common practice".
3. Cite the source document name and section number for every factual claim. Format: [document_name, Section X.X]
4. If the question is not answered within the available documents, respond with exactly:
{REFUSAL_TEMPLATE}
   No variations of this refusal are permitted.

Answer format for a found answer:
[document_name, Section X.X]: <exact answer from that section>

Answer format when not found:
{REFUSAL_TEMPLATE}
"""


# --- skill: retrieve_documents ---

def retrieve_documents() -> dict:
    """Load all three policy files and index by document name and section number."""
    index = {}
    for file_path in POLICY_FILES:
        doc_name = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Policy file not found: {file_path}")

        sections = {}
        for match in re.finditer(r"(\d+\.\d+)\s+(.+?)(?=\n\s*\d+\.\d+|\Z)", raw_text, re.DOTALL):
            section_num = match.group(1)
            section_text = match.group(2).strip()
            sections[section_num] = section_text

        index[doc_name] = {"raw_text": raw_text, "sections": sections}

    return index


# --- skill: answer_question (local, no API) ---

def answer_question_local(question: str, index: dict) -> str:
    """Keyword search across indexed sections. Returns single-source match or refusal template."""
    keywords = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 3]
    best_doc = None
    best_section = None
    best_score = 0

    for doc_name, doc_data in index.items():
        for section_num, section_text in doc_data["sections"].items():
            text_lower = section_text.lower()
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_doc = doc_name
                best_section = (section_num, section_text)

    if best_score == 0 or best_section is None:
        return REFUSAL_TEMPLATE

    section_num, section_text = best_section
    preview = section_text[:300].replace("\n", " ")
    return f"[{best_doc}, Section {section_num}]: {preview}"


# --- skill: answer_question ---

def answer_question(question: str, index: dict, client) -> str:
    """Search indexed documents for a single-source answer, or return refusal template."""
    # Build context block: all document text with clear source labels
    context_parts = []
    for doc_name, doc_data in index.items():
        context_parts.append(f"=== {doc_name} ===\n{doc_data['raw_text']}")
    context = "\n\n".join(context_parts)

    user_message = (
        f"Policy documents:\n\n{context}\n\n"
        f"Question: {question}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


# --- main ---

def main():
    no_key = not os.environ.get("ANTHROPIC_API_KEY")

    print("Loading policy documents...")
    try:
        index = retrieve_documents()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    docs_loaded = list(index.keys())
    print(f"Loaded: {', '.join(docs_loaded)}")

    client = None
    if not no_key:
        import anthropic
        client = anthropic.Anthropic()

    print("\nAsk My Documents — type your question, or 'quit' to exit.\n")
    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            break

        if client:
            answer = answer_question(question, index, client)
        else:
            answer = answer_question_local(question, index)
        print(f"\nAnswer: {answer}\n")


if __name__ == "__main__":
    main()
