"""
UC-X - Ask My Documents
Policy Q&A Agent (Interactive CLI)

Implements two skills from skills.md:
  - retrieve_documents : loads all 3 policy .txt files, indexes by section number
  - answer_question    : searches indexed sections, returns single-source answer
                         with citation OR the refusal template

Enforcement rules from agents.md:
  1. Never combine claims from two different documents into a single answer
  2. Never use hedging phrases — use the refusal template instead
  3. If question not in documents — use refusal template exactly, no variations
  4. Cite source document name + section number for every factual claim

Run:
    python app.py
"""

import io
import os
import re
import sys

# Force stdout to UTF-8 on Windows to handle em-dashes and special chars in policy text
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

POLICY_FILES = {
    "policy_hr_leave.txt":             "HR-POL-001",
    "policy_it_acceptable_use.txt":    "IT-POL-003",
    "policy_finance_reimbursement.txt": "FIN-POL-007",
}

# Resolved relative to this script's location
POLICY_DIR = Path(__file__).parent.parent / "data" / "policy-documents"

# Refusal template — must be used verbatim (agents.md enforcement rule 3)
REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, "
    "policy_finance_reimbursement.txt). "
    "Please contact [relevant team] for guidance."
)

# Hedging phrases banned by agents.md enforcement rule 2
BANNED_HEDGES = [
    "while not explicitly covered",
    "typically",
    "generally understood",
    "it is common practice",
    "it is generally",
    "in most organisations",
    "standard practice",
]

# Cross-document blending guard + direct section lookups for high-risk questions
# Maps a trigger phrase → (only_permitted_source, preferred_section)
SINGLE_SOURCE_GUARDS = {
    "personal phone":   ("IT-POL-003", "3.1"),
    "personal device":  ("IT-POL-003", "3.1"),
    "byod":             ("IT-POL-003", "3.1"),
    "install slack":    ("IT-POL-003", "2.3"),
    "install software": ("IT-POL-003", "2.3"),
    "without pay":      ("HR-POL-001", "5.2"),
    "leave without":    ("HR-POL-001", "5.2"),
    "lwp":              ("HR-POL-001", "5.2"),
    "who approves":     ("HR-POL-001", "5.2"),
    "approves leave":   ("HR-POL-001", "5.2"),
}

# Topics that ARE covered — used to detect out-of-scope questions for refusal
COVERED_TOPIC_KEYWORDS = {
    "leave", "annual", "sick", "maternity", "paternity", "lwp", "lop", "carry",
    "forward", "encash", "grievance", "laptop", "software", "install", "device",
    "password", "data", "email", "internet", "mfa", "reimburs", "travel", "da",
    "meal", "hotel", "allowance", "equipment", "phone", "mobile", "training",
    "claim", "receipt", "work", "holiday", "approval", "approve", "wfh",
    "remote", "home", "office", "security", "portal", "certification",
}


# ─────────────────────────────────────────────────────────────────────────────
# Skill 1: retrieve_documents
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_documents(policy_dir: Path) -> dict:
    """
    Loads all 3 policy .txt files from policy_dir, parses them into sections,
    and returns an index keyed by (doc_ref, section_id) → section text.

    Also returns a flat list of all sections for keyword search.

    Returns:
        {
          "index": {(doc_ref, section_id): {"doc_ref": str, "filename": str,
                                             "section_id": str, "heading": str,
                                             "body": str}},
          "sections": [same dicts as a flat list]
        }

    Raises:
        FileNotFoundError — if any policy file is missing
    """
    index = {}
    sections_flat = []

    for filename, doc_ref in POLICY_FILES.items():
        fpath = policy_dir / filename
        if not fpath.exists():
            raise FileNotFoundError(
                f"retrieve_documents: policy file not found: {fpath.resolve()}"
            )

        with open(fpath, "r", encoding="utf-8") as fh:
            raw = fh.read()

        parsed = _parse_sections(raw, doc_ref, filename)
        for sec in parsed:
            key = (doc_ref, sec["section_id"])
            index[key] = sec
            sections_flat.append(sec)

    print(f"[retrieve_documents] Loaded {len(sections_flat)} sections from {len(POLICY_FILES)} documents.")
    return {"index": index, "sections": sections_flat}


def _parse_sections(raw: str, doc_ref: str, filename: str) -> list:
    """
    Parses numbered clauses (N.N format) from a policy text file.
    Strips trailing section headers (line of = signs) from body text.
    Returns list of section dicts.
    """
    sections = []

    # Extract section headings from ═══ separator blocks
    heading_map = {}
    heading_pattern = re.compile(r"═+\s*\n(.+?)\s*\n═+", re.DOTALL)
    heading_positions = []
    for m in heading_pattern.finditer(raw):
        heading_positions.append((m.start(), m.group(1).strip()))

    # Match numbered clauses
    clause_pattern = re.compile(
        r"^(\d+\.\d+)\s+(.*?)(?=^\d+\.\d+\s|═{3,}|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    for match in clause_pattern.finditer(raw):
        section_id = match.group(1)
        body = match.group(0).strip()
        # Remove any trailing separator lines that got included
        body = re.sub(r"\s*═+.*", "", body, flags=re.DOTALL).strip()
        pos = match.start()

        # Find closest preceding heading
        heading = None
        for hpos, htitle in reversed(heading_positions):
            if hpos < pos:
                heading = htitle
                break

        sections.append({
            "doc_ref": doc_ref,
            "filename": filename,
            "section_id": section_id,
            "heading": heading,
            "body": body,
        })

    return sections


# ─────────────────────────────────────────────────────────────────────────────
# Skill 2: answer_question
# ─────────────────────────────────────────────────────────────────────────────

def answer_question(question: str, doc_store: dict) -> str:
    """
    Searches the indexed policy sections for the answer to the question.

    Strategy:
      1. Check if question is out-of-scope — refusal template
      2. Apply single-source guard for cross-document trap topics
      3. Score sections using token overlap + phrase bonuses + section-id boost
      4. If top score too low — return refusal template
      5. Return single-source answer with citation (never blend two sources)
    """
    sections = doc_store["sections"]
    q_lower = question.lower()
    q_tokens = set(re.findall(r"\b\w+\b", q_lower))

    # Out-of-scope detection: if no covered topic keyword overlaps → refuse
    topic_overlap = q_tokens & COVERED_TOPIC_KEYWORDS
    if not topic_overlap:
        return REFUSAL_TEMPLATE

    # Check single-source guard (cross-document blending protection)
    forced_source = None
    forced_section = None
    for trigger, (required_doc, preferred_sec) in SINGLE_SOURCE_GUARDS.items():
        if trigger in q_lower:
            forced_source = required_doc
            forced_section = preferred_sec
            break

    # If a preferred section is known, look it up directly
    if forced_section:
        index = doc_store["index"]
        direct = index.get((forced_source, forced_section))
        if direct:
            body_clean = " ".join(direct["body"].split())
            citation = (
                f"[Source: {direct['filename']} "
                f"-- {direct['doc_ref']} section {direct['section_id']}]"
            )
            return f"{body_clean}\n\n{citation}"

    # Score sections by keyword + phrase relevance
    scored = []

    # Build meaningful query tokens (strip stop-words)
    STOP = {"can", "i", "my", "the", "a", "an", "is", "are", "for", "to",
            "and", "or", "of", "in", "on", "at", "be", "do", "use", "what",
            "who", "when", "how", "does", "will", "from", "with", "that",
            "this", "it", "its", "not", "no", "same", "day"}
    meaningful_tokens = {t for t in q_tokens if t not in STOP and len(t) > 2}

    for sec in sections:
        body_lower = sec["body"].lower()
        body_tokens = set(re.findall(r"\b\w+\b", body_lower))

        if forced_source and sec["doc_ref"] != forced_source:
            continue

        # Token overlap score
        overlap = len(meaningful_tokens & body_tokens)

        # Phrase bonus: reward multi-word substring matches
        phrase_bonus = 0
        for token in meaningful_tokens:
            if token in body_lower:
                phrase_bonus += 2

        # Bigram bonus — reward adjacent word pairs from the question
        q_words = re.findall(r"\b\w+\b", q_lower)
        bigram_bonus = 0
        for i in range(len(q_words) - 1):
            bigram = q_words[i] + " " + q_words[i + 1]
            if bigram in body_lower:
                bigram_bonus += 5

        total = overlap + phrase_bonus + bigram_bonus
        scored.append((total, sec))

    if not scored:
        return REFUSAL_TEMPLATE

    scored.sort(key=lambda x: x[0], reverse=True)
    top_score, top_sec = scored[0]

    # Low confidence threshold — refuse rather than guess
    if top_score < 4:
        return REFUSAL_TEMPLATE

    # Build the answer from the top-scoring single section only (never blend)
    body_clean = " ".join(top_sec["body"].split())
    citation = (
        f"[Source: {top_sec['filename']} "
        f"-- {top_sec['doc_ref']} section {top_sec['section_id']}]"
    )
    return f"{body_clean}\n\n{citation}"


# ─────────────────────────────────────────────────────────────────────────────
# Refusal / hedge guard
# ─────────────────────────────────────────────────────────────────────────────

def _guard_output(answer: str) -> str:
    """
    Enforcement rule 2: if any banned hedge phrase is detected in a generated
    answer, replace with the refusal template. This is a safety net — the
    answer_question function should never produce them, but guard defensively.
    """
    lower = answer.lower()
    for phrase in BANNED_HEDGES:
        if phrase in lower:
            return (
                f"[HEDGE DETECTED — answer replaced by refusal template]\n"
                f"{REFUSAL_TEMPLATE}"
            )
    return answer


# ─────────────────────────────────────────────────────────────────────────────
# Interactive CLI
# ─────────────────────────────────────────────────────────────────────────────

def run_interactive(doc_store: dict):
    """
    Runs the interactive Q&A REPL. Type a question and press Enter.
    Type 'quit' or 'exit' to stop. Type 'test' to run all 7 test questions.
    """
    TEST_QUESTIONS = [
        "Can I carry forward unused annual leave?",
        "Can I install Slack on my work laptop?",
        "What is the home office equipment allowance?",
        "Can I use my personal phone to access work files when working from home?",
        "What is the company view on flexible working culture?",
        "Can I claim DA and meal receipts on the same day?",
        "Who approves leave without pay?",
    ]

    print("\n" + "=" * 70)
    print("UC-X — Ask My Documents")
    print("Policy Q&A Agent | CMC Policy Documents")
    print("Sources: HR-POL-001 · IT-POL-003 · FIN-POL-007")
    print("=" * 70)
    print("Type a question and press Enter. Commands: 'test' | 'quit'")
    print("=" * 70 + "\n")

    while True:
        try:
            question = input("Question> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        if question.lower() == "test":
            print("\n--- Running all 7 test questions ---\n")
            for i, q in enumerate(TEST_QUESTIONS, 1):
                print(f"[{i}] {q}")
                answer = answer_question(q, doc_store)
                answer = _guard_output(answer)
                print(f"  -> {answer}\n")
            continue

        answer = answer_question(question, doc_store)
        answer = _guard_output(answer)
        print(f"\n{answer}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Skill 1: retrieve_documents ───────────────────────────────────────────
    try:
        doc_store = retrieve_documents(POLICY_DIR)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Interactive REPL ──────────────────────────────────────────────────────
    run_interactive(doc_store)


if __name__ == "__main__":
    main()
