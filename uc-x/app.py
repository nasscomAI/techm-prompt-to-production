"""
UC-X — Ask My Documents
Policy Document QA Agent

Implements agents.md + skills.md:
  - retrieve_documents: loads and indexes 3 policy files by section
  - answer_question: returns single-source cited answer or refusal template
"""

import os
import re

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILES = [
    os.path.join(BASE_DIR, "../data/policy-documents/policy_hr_leave.txt"),
    os.path.join(BASE_DIR, "../data/policy-documents/policy_it_acceptable_use.txt"),
    os.path.join(BASE_DIR, "../data/policy-documents/policy_finance_reimbursement.txt"),
]

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, "
    "policy_finance_reimbursement.txt). "
    "Please contact [relevant team] for guidance."
)

HEDGING_PHRASES = [
    "while not explicitly covered",
    "typically",
    "generally understood",
    "it is common practice",
    "it is generally",
    "usually",
    "in most cases",
]

# ── Skill: retrieve_documents ─────────────────────────────────────────────────

def retrieve_documents(file_paths):
    """
    Loads policy files and builds an index:
      { doc_name: { section_id: section_text } }
    Raises on missing files or empty documents.
    """
    index = {}

    for path in file_paths:
        doc_name = os.path.basename(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Policy file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        sections = _parse_sections(raw)

        if not sections:
            raise ValueError(
                f"No parseable sections found in '{doc_name}'. "
                "Cannot index an empty document."
            )

        index[doc_name] = sections

    return index


def _parse_sections(text):
    """
    Parses numbered sections (e.g. 2.3, 5.1) from policy text.
    Returns { "2.3": "text of that section", ... }
    Strips decorative separator lines (═══...) so they don't bleed
    into the preceding section's text.
    """
    # Remove separator lines and top-level section headings before parsing
    clean = re.sub(r"═+[^\n]*\n?", "", text)
    # Remove top-level headings like "5. LEAVE WITHOUT PAY (LWP)"
    clean = re.sub(r"^\d+\.\s+[A-Z][A-Z\s\(\)\-]+\n?", "", clean, flags=re.MULTILINE)

    sections = {}
    pattern = re.compile(r"^(\d+\.\d+)\s+(.+)", re.MULTILINE)
    matches = list(pattern.finditer(clean))

    for i, match in enumerate(matches):
        sec_id = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(clean)
        sec_text = clean[start:end].strip()
        sections[sec_id] = sec_text

    return sections


# ── Skill: answer_question ────────────────────────────────────────────────────

def answer_question(question, index):
    """
    Searches the index for a single-source answer.
    Returns a dict with answer + citation, or the refusal template string.
    Enforcement rules from agents.md are applied here.
    """
    q_lower = _expand_synonyms(question.lower())
    hits = []  # list of (doc_name, section_id, section_text, score)

    for doc_name, sections in index.items():
        for sec_id, sec_text in sections.items():
            sec_lower = _expand_synonyms(sec_text.lower())
            score = _relevance_score(q_lower, sec_lower)
            if score > 0:
                hits.append((doc_name, sec_id, sec_text, score))

    if not hits:
        return REFUSAL_TEMPLATE

    # Sort by score descending
    hits.sort(key=lambda x: x[3], reverse=True)

    top_score = hits[0][3]

    # Collect all hits within 60% of top score (tighter window to reduce false blends)
    competitive = [h for h in hits if h[3] >= top_score * 0.6]
    docs_in_competitive = set(h[0] for h in competitive)

    if len(docs_in_competitive) > 1:
        # Multi-document match — potential blend risk → refusal
        return REFUSAL_TEMPLATE

    best_doc, best_sec, best_text, _ = hits[0]

    # Build the answer from the single best section only
    answer_text = _extract_answer_text(best_text)

    return {
        "answer": answer_text,
        "source_document": best_doc,
        "section": best_sec,
    }


def _expand_synonyms(question):
    """Expand common shorthand and stem key terms so scoring matches policy text better."""
    replacements = {
        r"\bleave without pay\b": "leave without pay lwp",
        r"\blwp\b": "leave without pay lwp",
        r"\bbyod\b": "personal device byod",
        r"\bwork from home\b": "work from home wfh",
        r"\bwfh\b": "work from home wfh",
        r"\bapproves\b": "approves approval approve",
        r"\bapprove\b": "approve approval approves",
        r"\bapproval\b": "approval approve approves",
    }
    for pattern, replacement in replacements.items():
        question = re.sub(pattern, replacement, question)
    return question


def _relevance_score(question, section_text):
    """
    Keyword overlap score with bigram bonus.
    Single keywords score 1 each; adjacent keyword pairs score 2 extra
    when both appear together, rewarding sections that match the full
    intent of the question (e.g. 'leave without pay' over just 'leave').
    """
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "i", "my",
        "me", "we", "our", "you", "your", "it", "its", "this", "that",
        "to", "of", "in", "on", "at", "for", "with", "and", "or",
        "not", "no", "what", "when", "how", "who", "which",
    }
    words = re.findall(r"\b\w+\b", question)
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    if not keywords:
        return 0

    # Unigram score
    score = sum(1 for kw in keywords if kw in section_text)

    # Bigram bonus — pairs of adjacent keywords both present
    for i in range(len(keywords) - 1):
        pair = keywords[i] + " " + keywords[i + 1]
        if pair in section_text:
            score += 2

    return score


def _extract_answer_text(section_text):
    """Returns the section text cleaned up for display."""
    # Collapse internal whitespace/newlines for readability
    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    return " ".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("UC-X — Ask My Documents")
    print("Policy QA Agent | Type 'quit' or 'exit' to stop")
    print("=" * 60)

    # Load and index documents once
    try:
        index = retrieve_documents(POLICY_FILES)
    except (FileNotFoundError, ValueError) as e:
        print(f"\n[ERROR] {e}")
        return

    doc_names = list(index.keys())
    total_sections = sum(len(s) for s in index.values())
    print(f"\nLoaded {len(doc_names)} documents | {total_sections} sections indexed")
    for name in doc_names:
        print(f"  • {name} ({len(index[name])} sections)")
    print()

    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Exiting.")
            break

        result = answer_question(question, index)

        print()
        if isinstance(result, str):
            # Refusal template
            print(f"ANSWER: {result}")
        else:
            print(f"ANSWER: {result['answer']}")
            print(f"SOURCE: {result['source_document']} § {result['section']}")
        print()


if __name__ == "__main__":
    main()
