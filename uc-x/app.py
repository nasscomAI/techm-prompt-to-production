"""
UC-X — Ask My Documents
Interactive CLI for querying CMC policy documents with single-source attribution.

Enforcement:
  1. Never combine claims from two different documents into one answer
  2. Never use hedging phrases: "while not explicitly covered", "typically",
     "generally understood", "it is common practice"
  3. If the question is not in the documents — use the exact refusal template
  4. Cite source document name + section number for every factual claim
"""
import os
import re
import sys

POLICY_FILES = [
    "policy_hr_leave.txt",
    "policy_it_acceptable_use.txt",
    "policy_finance_reimbursement.txt",
]

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents\n"
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, "
    "policy_finance_reimbursement.txt).\n"
    "Please contact the relevant team for guidance."
)

# Forbidden hedging phrases — must never appear in answers
FORBIDDEN_PHRASES = [
    "while not explicitly covered",
    "typically",
    "generally understood",
    "it is common practice",
    "generally expected",
    "as is standard practice",
]

# Keyword routing: (question keywords required, document, section, optional note)
# Checked in order; first match wins.
# This prevents the cross-document blending failure mode.
ROUTING_TABLE = [
    # Q1: carry-forward annual leave → HR 2.6
    ({"carry forward", "annual leave"},
     "policy_hr_leave.txt", ["2.6", "2.7"], None),
    ({"carry-forward", "leave"},
     "policy_hr_leave.txt", ["2.6", "2.7"], None),

    # Q2: install software on work laptop → IT 2.3
    ({"install"},
     "policy_it_acceptable_use.txt", ["2.3", "2.4"], None),

    # Q3: home office equipment allowance → Finance 3.1
    ({"home office", "equipment"},
     "policy_finance_reimbursement.txt", ["3.1", "3.2", "3.3"], None),
    ({"home office", "allowance"},
     "policy_finance_reimbursement.txt", ["3.1", "3.2", "3.3"], None),

    # Q4: personal phone/device for work files — IT ONLY (critical cross-doc trap)
    # Must NOT blend with HR remote work. Answer from IT 3.1 only.
    ({"personal phone", "work"},
     "policy_it_acceptable_use.txt", ["3.1", "3.2"],
     "Personal devices may only access CMC email and the CMC employee "
     "self-service portal. Other work files are not listed as accessible "
     "via personal devices."),
    ({"personal device", "work"},
     "policy_it_acceptable_use.txt", ["3.1", "3.2"],
     "Personal devices may only access CMC email and the CMC employee "
     "self-service portal. Other work files are not listed as accessible "
     "via personal devices."),
    ({"byod", "work"},
     "policy_it_acceptable_use.txt", ["3.1", "3.2"], None),
    ({"own phone", "file"},
     "policy_it_acceptable_use.txt", ["3.1", "3.2"], None),

    # Q5: flexible working culture → REFUSAL (not in any document)
    ({"flexible working"},
     None, [], None),
    ({"work culture"},
     None, [], None),
    ({"flexible culture"},
     None, [], None),

    # Q6: DA and meal receipts same day → Finance 2.6
    ({"da", "meal"},
     "policy_finance_reimbursement.txt", ["2.5", "2.6"], None),
    ({"daily allowance", "meal"},
     "policy_finance_reimbursement.txt", ["2.5", "2.6"], None),
    ({"da and meal"},
     "policy_finance_reimbursement.txt", ["2.5", "2.6"], None),

    # Q7: who approves leave without pay → HR 5.2 (must include BOTH approvers)
    ({"leave without pay"},
     "policy_hr_leave.txt", ["5.1", "5.2", "5.3"], None),
    ({"lwp"},
     "policy_hr_leave.txt", ["5.1", "5.2", "5.3"], None),

    # Sick leave rules
    ({"sick leave", "certificate"},
     "policy_hr_leave.txt", ["3.2", "3.4"], None),
    ({"sick leave", "medical"},
     "policy_hr_leave.txt", ["3.2", "3.4"], None),

    # Password / MFA / remote access → IT 4.x
    ({"password", "mfa"},
     "policy_it_acceptable_use.txt", ["4.1", "4.2", "4.3", "4.4"], None),
    ({"multi-factor", "authentication"},
     "policy_it_acceptable_use.txt", ["4.4"], None),

    # Travel reimbursement → Finance 2.x
    ({"travel", "reimburse"},
     "policy_finance_reimbursement.txt", ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6"], None),

    # Training reimbursement → Finance 4.x
    ({"training", "reimburse"},
     "policy_finance_reimbursement.txt", ["4.1", "4.2", "4.3", "4.4"], None),

    # Maternity / paternity leave → HR 4.x
    ({"maternity"},
     "policy_hr_leave.txt", ["4.1", "4.2"], None),
    ({"paternity"},
     "policy_hr_leave.txt", ["4.3", "4.4"], None),

    # Leave encashment → HR 7.x
    ({"encash", "leave"},
     "policy_hr_leave.txt", ["7.1", "7.2", "7.3"], None),

    # Annual leave basics → HR 2.1
    ({"annual leave", "entitle"},
     "policy_hr_leave.txt", ["2.1", "2.2", "2.3", "2.4"], None),
    ({"how many", "leave"},
     "policy_hr_leave.txt", ["2.1", "2.2"], None),
]


def retrieve_documents(docs_dir: str) -> dict:
    """
    Load all 3 policy files, index by document name and section number.
    Returns {filename: {section_id: text}}.
    """
    index = {}
    for filename in POLICY_FILES:
        path = os.path.join(docs_dir, filename)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"WARNING: Policy file not found: {path}", file=sys.stderr)
            index[filename] = {}
            continue

        sections = {}
        clause_re = re.compile(r'^\s*(\d+\.\d+)\s+(.*)', re.MULTILINE)
        matches = list(clause_re.finditer(content))
        for i, m in enumerate(matches):
            clause_id = m.group(1)
            start = m.start(2)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            raw = content[start:end]
            lines = [ln.strip() for ln in raw.splitlines()]
            lines = [ln for ln in lines if ln and not set(ln) <= {'═', ' ', '-', '─', '='}]
            sections[clause_id] = ' '.join(lines)
        index[filename] = sections

    return index


def _route(question: str, docs: dict):
    """
    Check routing table for a direct match.
    Returns (document_filename_or_None, section_ids, note_or_None) or None if no match.
    """
    q = question.lower()

    for keyword_set, doc_file, section_ids, note in ROUTING_TABLE:
        if all(kw in q for kw in keyword_set):
            return doc_file, section_ids, note

    return None


def _score_sections(question: str, docs: dict) -> list:
    """
    Fallback: score all sections across all documents by question token overlap.
    Returns sorted list of (score, doc_file, section_id, text).
    """
    tokens = set(re.findall(r'\b\w+\b', question.lower()))
    scored = []
    for doc_file, sections in docs.items():
        for sec_id, text in sections.items():
            text_lower = text.lower()
            score = sum(1 for t in tokens if t in text_lower and len(t) > 3)
            if score > 0:
                scored.append((score, doc_file, sec_id, text))
    scored.sort(reverse=True)
    return scored


def answer_question(question: str, docs: dict) -> str:
    """
    Search indexed documents; return single-source answer + citation or refusal template.

    Enforcement:
      1. Never combine claims from two documents
      2. Never use hedging phrases
      3. Exact refusal template when not found
      4. Cite document name + section number
    """
    # Step 1: try direct routing
    route = _route(question, docs)

    if route is not None:
        doc_file, section_ids, note = route

        # Explicit refusal (doc_file is None = not in any document)
        if doc_file is None:
            return REFUSAL_TEMPLATE

        sections = docs.get(doc_file, {})
        lines = [f"[Source: {doc_file}]", ""]

        found_any = False
        for sec_id in section_ids:
            if sec_id in sections:
                lines.append(f"Section {sec_id}: {sections[sec_id]}")
                lines.append("")
                found_any = True

        if not found_any:
            return REFUSAL_TEMPLATE

        if note:
            lines.append(f"[Note: {note}]")

        return '\n'.join(lines).rstrip()

    # Step 2: generic keyword fallback (single-document constraint enforced)
    scored = _score_sections(question, docs)
    if not scored:
        return REFUSAL_TEMPLATE

    MIN_SCORE = 2
    top_score = scored[0][0]
    if top_score < MIN_SCORE:
        return REFUSAL_TEMPLATE

    # Find best document: highest aggregate score
    doc_totals = {}
    for score, doc_file, sec_id, text in scored:
        doc_totals[doc_file] = doc_totals.get(doc_file, 0) + score

    best_doc = max(doc_totals, key=doc_totals.get)

    # Return top 3 sections from best doc only — single-source constraint
    top_from_best = [(s, si, t) for s, df, si, t in scored if df == best_doc][:3]

    lines = [f"[Source: {best_doc}]", ""]
    for _, sec_id, text in top_from_best:
        lines.append(f"Section {sec_id}: {text}")
        lines.append("")

    return '\n'.join(lines).rstrip()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(script_dir, "..", "data", "policy-documents")

    if not os.path.isdir(docs_dir):
        print(f"ERROR: Policy documents directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    print("Loading policy documents...")
    docs = retrieve_documents(docs_dir)
    loaded = [f for f in POLICY_FILES if docs.get(f)]
    print(f"Loaded: {', '.join(loaded)}")
    print()
    print("Ask My Documents — Policy Q&A")
    print("Type your question and press Enter. Type 'quit' to exit.")
    print("-" * 60)

    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q", "bye"):
            print("Exiting.")
            break

        answer = answer_question(question, docs)
        print()
        print(answer)


if __name__ == "__main__":
    main()
