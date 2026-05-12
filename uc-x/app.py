"""
UC-X — Ask My Documents
app.py — Multi-document policy Q&A agent (interactive CLI).

Skills:
  - retrieve_documents : loads 3 policy .txt files, indexes by doc name + section
  - answer_question    : searches indexed sections, returns single-source
                         answer with citation OR exact refusal template

Enforcement:
  - Single-source answers only — never blend across documents
  - No hedging phrases
  - Exact refusal template for uncovered questions
  - Citation (document + section) on every factual claim

Run:
  python app.py
"""

import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

POLICY_FILES = [
    "../data/policy-documents/policy_hr_leave.txt",
    "../data/policy-documents/policy_it_acceptable_use.txt",
    "../data/policy-documents/policy_finance_reimbursement.txt",
]

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, "
    "policy_finance_reimbursement.txt). "
    "Please contact [relevant team] for guidance."
)

BANNED_PHRASES = [
    "while not explicitly covered",
    "typically",
    "generally understood",
    "it is common practice",
    "generally expected to",
    "as is standard practice",
]


# ═══════════════════════════════════════════════════════════════════════════
# Custom Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class StructureError(Exception):
    """No numbered sections found in a policy document."""


# ═══════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Section:
    section_id: str
    heading: Optional[str]
    body: str


@dataclass
class DocumentIndex:
    documents: Dict[str, List[Section]]
    document_names: List[str]
    section_count: int


@dataclass
class AnswerResult:
    answer: str
    source_document: Optional[str]
    source_sections: List[str]
    is_refusal: bool


# ═══════════════════════════════════════════════════════════════════════════
# SKILL 1: retrieve_documents
# ═══════════════════════════════════════════════════════════════════════════

def _parse_sections(text: str) -> List[Section]:
    """Parse a policy document into numbered sections."""
    clause_re = re.compile(r"^(\d+\.\d+)\s+(.*)")
    separator_re = re.compile(r"^[═]+\s*$")
    heading_re = re.compile(r"^\d+\.\s+[A-Z]")

    sections: List[Section] = []
    current_heading: Optional[str] = None
    current_id: Optional[str] = None
    body_lines: List[str] = []

    def flush():
        nonlocal current_id, body_lines
        if current_id is not None:
            body = re.sub(r"\s+", " ", " ".join(body_lines)).strip()
            sections.append(Section(
                section_id=current_id,
                heading=current_heading,
                body=body,
            ))
            current_id = None
            body_lines = []

    for line in text.splitlines():
        stripped = line.strip()
        if separator_re.match(stripped):
            continue
        if heading_re.match(stripped):
            flush()
            current_heading = stripped
            continue
        m = clause_re.match(stripped)
        if m:
            flush()
            current_id = m.group(1)
            t = m.group(2).strip()
            body_lines = [t] if t else []
            continue
        if current_id is not None and stripped:
            body_lines.append(stripped)

    flush()
    return sections


def retrieve_documents(file_paths: List[str]) -> DocumentIndex:
    """
    Loads all policy files, parses each into numbered sections, returns
    a searchable index keyed by document filename.
    """
    documents: Dict[str, List[Section]] = {}
    doc_names: List[str] = []
    total_sections = 0

    for fp in file_paths:
        path = Path(fp)
        name = path.name

        # file_not_found
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: '{fp}'")

        # unreadable_or_empty
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception as exc:
            raise IOError(f"Cannot read '{fp}': {exc}") from exc

        if not raw.strip():
            raise IOError(f"Policy file '{fp}' is empty.")

        sections = _parse_sections(raw)

        # no_sections_detected
        if not sections:
            raise StructureError(
                f"No numbered sections found in '{name}'."
            )

        # duplicate_section_ids — warn but keep
        seen_ids = set()
        for s in sections:
            if s.section_id in seen_ids:
                warnings.warn(
                    f"Duplicate section {s.section_id} in {name}",
                    UserWarning, stacklevel=2,
                )
            seen_ids.add(s.section_id)

        documents[name] = sections
        doc_names.append(name)
        total_sections += len(sections)

    print(f"[retrieve_documents] Loaded {len(doc_names)} documents, "
          f"{total_sections} total sections.")
    for name, secs in documents.items():
        print(f"  • {name}: {len(secs)} sections")

    return DocumentIndex(
        documents=documents,
        document_names=doc_names,
        section_count=total_sections,
    )


# ═══════════════════════════════════════════════════════════════════════════
# SKILL 2: answer_question
# ═══════════════════════════════════════════════════════════════════════════

# Domain synonyms to bridge natural language and policy formalisms
DOMAIN_SYNONYMS = {
    "phone": "device",
    "mobile": "device",
    "smartphone": "device",
    "laptop": "corporate device",
    "computer": "corporate device",
    "workstation": "corporate device",
    "slack": "software",
    "teams": "software",
    "zoom": "software",
    "files": "data",
    "documents": "data",
}


def _score_section(question_lower: str, section: Section) -> float:
    """
    Score a section's relevance using:
    1. Weighted phrase matching (high priority)
    2. Domain synonym expansion
    3. Heading-heavy keyword matching
    """
    body_lower = section.body.lower()
    heading_lower = (section.heading or "").lower()
    combined = body_lower + " " + heading_lower

    score = 0.0

    # --- Phase 1: Phrase Matching ---
    q_words = question_lower.split()
    for n in (3, 2):
        for i in range(len(q_words) - n + 1):
            phrase = " ".join(q_words[i:i + n])
            if len(phrase) < 5:
                continue
            if phrase in combined:
                score += n * 3.0  # Heavy weight for phrases

    # --- Phase 2: Keyword matching with Synonyms ---
    keywords = set(re.findall(r"[a-z]{3,}", question_lower))
    stopwords = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "has", "her", "was", "one", "our", "out", "had", "may", "who",
        "its", "how", "use", "what", "when", "from", "that", "this",
        "with", "have", "will", "each", "does", "been", "they", "any",
        "same", "get", "per", "about", "view", "company", "please",
    }
    keywords -= stopwords

    # Expand keywords with synonyms
    expanded_keywords = set(keywords)
    for kw in keywords:
        if kw in DOMAIN_SYNONYMS:
            expanded_keywords.add(DOMAIN_SYNONYMS[kw])

    for kw in expanded_keywords:
        # Boost matches in headings significantly
        if kw in heading_lower:
            score += 3.0
        if kw in body_lower:
            score += 1.0

    return score


def _find_best_sections(
    question: str,
    doc_index: DocumentIndex,
) -> List[Tuple[str, Section, float]]:
    """Returns all sections with scores > 0, sorted by score descending."""
    q_lower = question.lower()
    all_hits: List[Tuple[str, Section, float]] = []

    for doc_name, sections in doc_index.documents.items():
        for sec in sections:
            score = _score_section(q_lower, sec)
            if score > 0:
                all_hits.append((doc_name, sec, score))

    all_hits.sort(key=lambda x: x[2], reverse=True)
    return all_hits


def _format_answer(doc_name: str, sections: List[Section]) -> str:
    """Format an answer from sections of a single document with citations."""
    lines = []
    for sec in sections:
        lines.append(
            f"[{doc_name}, Section {sec.section_id}]: {sec.body}"
        )
    return "\n\n".join(lines)


def _check_hedging(text: str) -> Optional[str]:
    """Check for banned hedging phrases. Returns the phrase found, or None."""
    t_lower = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in t_lower:
            return phrase
    return None


def answer_question(question: str, doc_index: DocumentIndex) -> AnswerResult:
    """
    Searches indexed documents for sections relevant to the question.
    """
    if not question or not question.strip():
        return AnswerResult(
            answer="Please enter a question.",
            source_document=None, source_sections=[], is_refusal=False,
        )

    all_hits = _find_best_sections(question, doc_index)

    if not all_hits:
        return AnswerResult(
            answer=REFUSAL_TEMPLATE,
            source_document=None, source_sections=[], is_refusal=True,
        )

    # Threshold for a 'confident' answer
    best_score = all_hits[0][2]
    if best_score < 2.5:
        return AnswerResult(
            answer=REFUSAL_TEMPLATE,
            source_document=None, source_sections=[], is_refusal=True,
        )

    # Single-source enforcement: pick document of top hit
    best_doc = all_hits[0][0]

    # Collect other high-scoring hits from the same document
    best_doc_hits = [
        (sec, score) for doc, sec, score in all_hits
        if doc == best_doc and score >= 2.0
    ][:2]

    top_sections = [sec for sec, _ in best_doc_hits]
    section_ids = [s.section_id for s in top_sections]

    answer_text = _format_answer(best_doc, top_sections)

    # Final hedging check
    hedge = _check_hedging(answer_text)
    if hedge:
        return AnswerResult(
            answer=REFUSAL_TEMPLATE,
            source_document=None, source_sections=[], is_refusal=True,
        )

    return AnswerResult(
        answer=answer_text,
        source_document=best_doc,
        source_sections=section_ids,
        is_refusal=False,
    )



# ═══════════════════════════════════════════════════════════════════════════
# Interactive CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 65)
    print("  UC-X — Ask My Documents")
    print("  Policy Q&A Agent (single-source answers only)")
    print("=" * 65)
    print()

    # ── Skill 1: retrieve_documents ───────────────────────────────────
    try:
        doc_index = retrieve_documents(POLICY_FILES)
    except (FileNotFoundError, IOError, StructureError) as exc:
        print(f"[ERROR] retrieve_documents: {exc}", file=sys.stderr)
        sys.exit(1)

    print()
    print("Type a policy question and press Enter.")
    print("Type 'quit' or 'exit' to stop.\n")

    # ── Interactive loop ──────────────────────────────────────────────
    while True:
        try:
            question = input("Q: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        if not question:
            print("Please enter a question.\n")
            continue

        # ── Skill 2: answer_question ──────────────────────────────────
        result = answer_question(question, doc_index)

        if result.is_refusal:
            print(f"\nA: {result.answer}\n")
        else:
            print(f"\nA (source: {result.source_document}, "
                  f"sections: {', '.join(result.source_sections)}):")
            print(f"{result.answer}\n")


if __name__ == "__main__":
    main()
