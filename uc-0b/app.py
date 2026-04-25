"""
UC-0B app.py — Policy summarizer that preserves legal meaning.
Built using RICE + agents.md + skills.md + CRAFT workflow.
"""
import argparse
import re
import sys
import anthropic

TRACKED_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

SYSTEM_PROMPT = """You are a policy summarization agent for City Municipal Corporation HR documents (HR-POL-001).

ROLE: Summarize only what is explicitly stated in the source document. You have no external knowledge of HR practice and must not use it.

INTENT: Produce a structured summary where every numbered clause is present, every binding obligation uses the exact modal verb from the source, and every multi-condition requirement preserves all conditions. A compliance officer must be able to verify each clause without consulting the original document.

CONTEXT: Use only the text provided. Never add phrases like "as is standard practice", "typically", "generally expected to", or any information not explicitly in the source. Scope bleed is a violation.

ENFORCEMENT RULES — non-negotiable:
1. Every clause in this list MUST appear in the summary with its clause number as a prefix: [2.3] [2.4] [2.5] [2.6] [2.7] [3.2] [3.4] [5.2] [5.3] [7.2]
2. Multi-condition obligations must preserve ALL conditions. Clause [5.2] requires approval from BOTH the Department Head AND the HR Director — dropping either approver is a violation even if "approval" is mentioned.
3. Binding verbs must not be softened: must stays must, will stays will, requires stays requires, "not permitted" stays "not permitted". Never substitute should, may, or "is expected to".
4. If a clause cannot be paraphrased without meaning loss, quote it verbatim and append: [VERBATIM — summarisation would alter meaning]
5. Refuse to produce output if the source text is empty or unreadable — respond only with: ERROR: Source document unavailable or unreadable.

FORMAT: Group clauses under their section headings. Prefix each clause with its number in brackets, e.g. [2.3]. For multi-condition clauses, list each condition as a separate bullet under the clause."""

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def retrieve_policy(file_path: str) -> list[dict]:
    """Load .txt policy file and return ordered list of clause dicts."""
    try:
        with open(file_path, encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    if not raw.strip():
        raise ValueError("Policy file is empty.")

    sections = []
    current_heading = ""
    # Match lines like "2.3 Employees must..." or "  2.3 Employees must..."
    clause_pattern = re.compile(r"^\s*(\d+\.\d+)\s+(.*)")
    heading_pattern = re.compile(r"^\d+\.\s+[A-Z]")

    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect section headings (e.g. "2. ANNUAL LEAVE")
        if heading_pattern.match(line.strip()):
            current_heading = line.strip()
        else:
            m = clause_pattern.match(line)
            if m:
                clause_num = m.group(1)
                text_lines = [m.group(2).strip()]
                # Collect continuation lines (indented, not a new clause)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if clause_pattern.match(next_line) or heading_pattern.match(next_line.strip()):
                        break
                    stripped = next_line.strip()
                    if stripped and not stripped.startswith("═"):
                        text_lines.append(stripped)
                    j += 1
                sections.append({
                    "section_number": clause_num,
                    "heading": current_heading,
                    "text": " ".join(text_lines),
                })
                i = j
                continue
        i += 1

    if not sections:
        raise ValueError("Could not parse any numbered clauses from the policy file.")

    return sections


def summarize_policy(sections: list[dict]) -> str:
    """Call Claude to produce a compliant clause-by-clause summary."""
    if not sections:
        raise ValueError("Section list is empty — cannot summarize.")

    present = {s["section_number"] for s in sections}
    missing = [c for c in TRACKED_CLAUSES if c not in present]
    if missing:
        raise ValueError(f"Source document is missing tracked clauses: {missing}")

    # Build readable input for the model
    doc_text = ""
    current_heading = None
    for s in sections:
        if s["heading"] != current_heading:
            current_heading = s["heading"]
            doc_text += f"\n{current_heading}\n"
        doc_text += f"{s['section_number']} {s['text']}\n"

    message = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Summarize the following policy document:\n\n{doc_text}"}],
    )

    return message.content[0].text.strip()


def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summarizer")
    parser.add_argument("--input", required=True, help="Path to policy .txt file")
    parser.add_argument("--output", required=True, help="Path to write summary .txt file")
    args = parser.parse_args()

    try:
        sections = retrieve_policy(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR (retrieve_policy): {e}", file=sys.stderr)
        sys.exit(1)

    try:
        summary = summarize_policy(sections)
    except ValueError as e:
        print(f"ERROR (summarize_policy): {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Done. Summary written to {args.output}")


if __name__ == "__main__":
    main()
