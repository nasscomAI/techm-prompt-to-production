"""
UC-0B app.py — Summary generator that changes meaning.
"""
import argparse
import re
from pathlib import Path

# Clause inventory required by UC-0B
INVENTORY = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

SECTION_GROUPS = {
    "Annual Leave": ["2.3", "2.4", "2.5", "2.6", "2.7"],
    "Sick Leave": ["3.2", "3.4"],
    "Leave Without Pay (LWP)": ["5.2", "5.3"],
    "Leave Encashment": ["7.2"]
}


def _clean_excerpt(s: str) -> str:
    # Remove lines that are decorative separators (e.g. ======== or ----)
    lines = s.splitlines()
    keep = []
    for l in lines:
        ls = l.strip()
        if not ls:
            continue
        # drop lines consisting mostly of non-alphanumeric repeated chars
        if re.match(r'^[^A-Za-z0-9\s]{3,}$', ls):
            continue
        keep.append(ls)
    return ' '.join(keep).strip()


def retrieve_policy(path):
    """Load a plain-text policy file and return a mapping of clause -> matched text.

    Strategy:
    - Split document into paragraphs and look for clause identifiers (e.g. "2.3").
    - If not found in paragraphs, attempt to extract the sentence containing the clause id.
    - Return dict of clause -> text (verbatim extract).
    """
    text = Path(path).read_text(encoding="utf-8")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    found = {}

    # use top-level _clean_excerpt

    for clause in INVENTORY:
        pattern = re.compile(r"\b" + re.escape(clause) + r"\b")
        # Search paragraphs first
        hit = None
        for p in paragraphs:
            if pattern.search(p):
                hit = p
                break
        if not hit:
            # Fallback: search for sentence containing the clause
            m = re.search(r"([^.\n]*\b" + re.escape(clause) + r"\b[^.\n]*\.)", text)
            if m:
                hit = m.group(1).strip()
        if hit:
            found[clause] = _clean_excerpt(hit)

    # Parse sections by header (e.g., "2. ANNUAL LEAVE") and capture text until next header
    sections = {}
    headers = list(re.finditer(r'^\s*(\d+)\.\s+([A-Z].*)', text, re.MULTILINE))
    for i, m in enumerate(headers):
        sec_num = m.group(1)
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        sec_text = text[start:end].strip()
        sections[sec_num] = _clean_excerpt(sec_text)

    return {"raw": text, "clauses": found, "sections": sections}


def summarize_policy(structured):
    """Produce a summary that includes every inventory clause verbatim (when found).

    If any inventory clause is missing, return (False, report) so caller can handle refusal.
    """
    found = structured.get("clauses", {})
    missing = [c for c in INVENTORY if c not in found]
    if missing:
        report = {
            "ok": False,
            "missing": missing,
            "message": "Missing required inventory clauses: " + ", ".join(missing)
        }
        return False, report

    # Build summary: show full section once, then per-clause sentence
    lines = ["# HR Leave Policy Summary", ""]
    sections = structured.get("sections", {})
    for heading, clauses in SECTION_GROUPS.items():
        lines.append(f"## {heading}")
        # Determine section number from first clause (e.g., '2.3' -> '2')
        section_num = clauses[0].split('.')[0]
        section_text = sections.get(section_num)
        if section_text:
            # Print the full section once as sub-bullets (sentences)
            sents = [s.strip() for s in re.split(r'(?<=\.)\s+', section_text) if s.strip()]
            # remove trivial numeric-only sentences like '2.' created by line breaks
            sents = [s for s in sents if not re.match(r'^\d+\.$', s)]
            lines.append("- Full section:")
            for s in sents:
                lines.append(f"  - {s}")

        # For each inventory clause, extract the specific sentence containing that clause
        for c in clauses:
            clause_sentence = ''
            if section_text:
                m = re.search(r'([^.]*\b' + re.escape(c) + r'\b[^.]*\.)', section_text)
                if m:
                    clause_sentence = m.group(1).strip()

            if not clause_sentence:
                clause_sentence = found.get(c, '')

            # Remove leading clause number from the sentence (e.g., '2.3 Employees...' -> 'Employees...')
            clause_sentence = re.sub(r'^\s*\d+\.\d+[:\s]*', '', clause_sentence)

            lines.append(f"- Clause {c}: {clause_sentence}")

        lines.append("")

    summary = "\n".join(lines)
    return True, summary


def main():
    parser = argparse.ArgumentParser(description="Generate HR leave policy summary")
    parser.add_argument("--input", required=True, help="Input policy file")
    parser.add_argument("--output", required=True, help="Output summary file")
    args = parser.parse_args()

    structured = retrieve_policy(args.input)
    ok, result = summarize_policy(structured)
    if not ok:
        # Refuse to generate summary if required clauses missing; write report to output
        report_text = ("ERROR: Required clauses missing.\n\n" +
                       "Missing clauses: " + ", ".join(result.get("missing", [])) + "\n\n" +
                       "Full document retained in `raw` field.")
        Path(args.output).write_text(report_text, encoding="utf-8")
        raise SystemExit(2)

    Path(args.output).write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()
