"""
UC-0B — Policy Summarisation Agent
Implements: retrieve_policy + summarize_policy skills
Usage:
  python app.py --input ../data/policy-documents/policy_hr_leave.txt \
                --output summary_hr_leave.txt
"""

import argparse
import os
import re
import sys

# ── Enforcement constants ─────────────────────────────────────────────────────

# Binding verbs that must never be softened
BINDING_VERBS = ["must", "will", "requires", "not permitted", "are forfeited"]

# Weaker replacements that must never appear in place of binding verbs
SOFTENING_MAP = {
    "should":         "must",
    "may wish to":    "must",
    "is recommended": "requires",
    "is expected":    "must",
    "is advised":     "must",
    "is encouraged":  "must",
    "is suggested":   "must",
}

# Scope bleed phrases that must never appear in output
SCOPE_BLEED_PHRASES = [
    "as is standard practice",
    "typically in government organisation",
    "employees are generally expected to",
    "in line with common practice",
    "as is customary",
    "generally speaking",
]

# Multi-condition clauses: clause_number → list of required strings that must
# ALL appear in the summary for that clause (case-insensitive).
# Used to detect silent condition drops.
MULTI_CONDITION_CHECKS = {
    "2.4": ["written", "verbal"],
    "2.5": ["regardless"],
    "2.6": ["5", "forfeited", "31"],
    "2.7": ["january", "march", "forfeited"],       # or jan/mar abbreviations
    "3.2": ["48"],
    "3.4": ["regardless"],
    "5.2": ["department head", "hr director"],
    "5.3": ["30", "municipal commissioner"],
    "7.2": ["under any circumstances"],
}

# Binding verb per clause — must appear verbatim (case-insensitive)
CLAUSE_BINDING_VERBS = {
    "2.3": "must",
    "2.4": "must",
    "2.5": "will",
    "2.6": "forfeited",
    "2.7": "must",
    "3.2": "requires",
    "3.4": "requires",
    "5.2": "requires",
    "5.3": "requires",
    "7.2": "not permitted",
}


# ── retrieve_policy skill ─────────────────────────────────────────────────────

def retrieve_policy(file_path: str) -> dict:
    """
    Loads a .txt policy file and returns:
      {
        "sections": [ {"clause_number": str|None, "heading": str|None, "body": str}, ... ],
        "raw_text": str
      }
    Raises on missing/empty file. Logs warnings for non-standard numbering.
    """
    # Error: file missing or unreadable
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, encoding="utf-8") as fh:
        raw_text = fh.read()

    # Error: empty file
    if not raw_text.strip():
        raise ValueError(f"Input file is empty: {file_path}")

    sections = _parse_sections(raw_text)

    # Error: no parseable numbered sections
    numbered = [s for s in sections if s["clause_number"] is not None]
    if not numbered:
        raise ValueError(
            f"File '{file_path}' yielded no numbered clause sections. "
            "Ensure the document uses numeric clause identifiers (e.g. 2.3, 3.4)."
        )

    return {"sections": sections, "raw_text": raw_text}


def _parse_sections(raw_text: str) -> list:
    """
    Splits raw policy text into clause sections.
    A section begins with a line whose first token matches N.N (e.g. "2.3" or "5.2.1").
    Everything until the next such line is that clause's body.
    Lines that do not match are gathered under clause_number=None.
    """
    # Pattern: line starts with digits.digits (optionally more levels)
    clause_line_re = re.compile(r"^(\d+(?:\.\d+)+)\s*(.*)")

    lines = raw_text.splitlines()
    sections = []
    current_clause = None
    current_heading = None
    current_body_lines = []
    preamble_lines = []

    def flush(clause, heading, body_lines):
        body = "\n".join(body_lines).strip()
        sections.append({
            "clause_number": clause,
            "heading": heading,
            "body": body,
        })

    for line in lines:
        m = clause_line_re.match(line.strip())
        if m:
            # Flush previous section
            if current_clause is not None:
                flush(current_clause, current_heading, current_body_lines)
            elif preamble_lines:
                # preamble before first numbered clause
                preamble_body = "\n".join(preamble_lines).strip()
                if preamble_body:
                    sections.append({"clause_number": None, "heading": "Preamble", "body": preamble_body})
                preamble_lines = []

            current_clause = m.group(1)
            rest = m.group(2).strip()
            # Heuristic: if the rest of the line looks like a heading (short, no period mid-text)
            # treat it as heading; otherwise start of body
            if rest and len(rest) < 80 and not rest.endswith("."):
                current_heading = rest
                current_body_lines = []
            else:
                current_heading = None
                current_body_lines = [rest] if rest else []
        else:
            if current_clause is None:
                preamble_lines.append(line)
            else:
                current_body_lines.append(line)

    # Flush final section
    if current_clause is not None:
        flush(current_clause, current_heading, current_body_lines)
    elif preamble_lines:
        preamble_body = "\n".join(preamble_lines).strip()
        if preamble_body:
            sections.append({"clause_number": None, "heading": "Preamble", "body": preamble_body})

    # Log warning for any null-clause sections beyond preamble
    null_sections = [s for s in sections if s["clause_number"] is None and s.get("heading") != "Preamble"]
    if null_sections:
        print(
            f"[WARN] {len(null_sections)} non-standard section(s) could not be assigned a clause number "
            "and will appear as unnumbered entries in the output.",
            file=sys.stderr,
        )

    return sections


# ── summarize_policy skill ────────────────────────────────────────────────────

def summarize_policy(sections: list, raw_text: str, output_path: str) -> None:
    """
    Produces a clause-accurate summary written to output_path.
    Enforces: all clauses present, binding verbs preserved, no scope bleed,
    multi-condition completeness, verbatim quoting when meaning loss is detected.
    """
    # Error: empty sections
    if not sections:
        raise ValueError("No clause sections were provided to summarize_policy.")

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as exc:
            raise PermissionError(
                f"Cannot create output directory '{out_dir}': {exc}"
            ) from exc

    output_lines = []
    output_lines.append("HR LEAVE POLICY — CLAUSE-ACCURATE SUMMARY")
    output_lines.append("=" * 60)
    output_lines.append("")

    for section in sections:
        clause_num = section["clause_number"]
        body = section.get("body", "").strip()
        heading = section.get("heading")

        # Skip preamble / unnumbered sections — include them unmodified
        if clause_num is None:
            if body:
                label = heading or "General"
                output_lines.append(f"[{label}]")
                output_lines.append(body)
                output_lines.append("")
            continue

        # Error: empty clause body
        if not body:
            output_lines.append(f"[{clause_num}] [VERBATIM — meaning loss risk]")
            output_lines.append("  NOTE: Clause body was absent in the source document.")
            output_lines.append("")
            print(f"[WARN] Clause {clause_num} has an empty body.", file=sys.stderr)
            continue

        # Attempt to produce a compliant summary entry
        entry, used_verbatim, flags = _summarise_clause(clause_num, body, heading)

        # Scope bleed check on the produced entry
        entry, bleed_warnings = _check_scope_bleed(clause_num, entry, body)
        for w in bleed_warnings:
            print(w, file=sys.stderr)

        # Build output block
        flag_str = " [VERBATIM — meaning loss risk]" if used_verbatim else ""
        output_lines.append(f"[{clause_num}]{flag_str}")
        if heading and not used_verbatim:
            output_lines.append(f"  {heading}")
        output_lines.append(f"  {entry}")
        for f in flags:
            output_lines.append(f"  NOTE: {f}")
        output_lines.append("")

    # Write output
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(output_lines))

    print(f"[INFO] Summary written to {output_path}")


def _summarise_clause(clause_num: str, body: str, heading: str | None) -> tuple:
    """
    Returns (entry_text, used_verbatim: bool, flags: list[str]).

    Strategy:
    1. Check if multi-condition requirements are all satisfiable from body text.
    2. Check if binding verb is present in body.
    3. If either check fails → quote verbatim + flag.
    4. Otherwise produce a condensed single-sentence summary that preserves
       all conditions and binding verbs drawn directly from body text.
    """
    flags = []
    body_lower = body.lower()

    # ── Multi-condition completeness check ──
    required_terms = MULTI_CONDITION_CHECKS.get(clause_num, [])
    missing_terms = []
    for term in required_terms:
        # Allow for jan/feb abbreviations for month checks
        alternatives = _term_alternatives(term)
        if not any(alt in body_lower for alt in alternatives):
            missing_terms.append(term)

    if missing_terms:
        # Cannot paraphrase without losing a condition — use verbatim
        flags.append(
            f"Multi-condition clause: required term(s) not found in body for safe paraphrase: "
            + ", ".join(f'"{t}"' for t in missing_terms)
        )
        return body.strip(), True, flags

    # ── Binding verb check ──
    required_verb = CLAUSE_BINDING_VERBS.get(clause_num)
    if required_verb and required_verb.lower() not in body_lower:
        flags.append(
            f"Expected binding verb '{required_verb}' not found in source body — "
            "quoting verbatim to avoid obligation softening."
        )
        return body.strip(), True, flags

    # ── Softening check: scan body for weak verbs that replaced binding ones ──
    for weak, _ in SOFTENING_MAP.items():
        if weak in body_lower:
            flags.append(
                f"Weak verb '{weak}' detected in source — quoting verbatim to prevent softening."
            )
            return body.strip(), True, flags

    # ── Safe to produce a condensed summary ──
    # Build a tight summary that:
    # - begins with the clause number reference
    # - preserves binding verb exactly
    # - includes all conditions found via multi-condition checks
    summary = _condense(clause_num, body)
    return summary, False, flags


def _condense(clause_num: str, body: str) -> str:
    """
    Produces a condensed single-sentence summary of the clause body.
    Keeps the first meaningful sentence and appends any additional
    condition sentences (those containing binding verbs or condition keywords).
    Falls back to first 200 chars of body if no sentence structure is found.
    """
    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", body.strip())
    if not sentences:
        return body[:200]

    # Always include the first sentence
    kept = [sentences[0].strip()]

    # Include additional sentences that carry binding verbs or conditions
    condition_markers = BINDING_VERBS + [
        "regardless", "forfeited", "not valid", "not permitted",
        "under any circumstances", "within 48", "48 hours",
        "department head", "hr director", "municipal commissioner",
        "31 dec", "january", "march", "jan", "mar",
    ]
    for sent in sentences[1:]:
        if any(m.lower() in sent.lower() for m in condition_markers):
            kept.append(sent.strip())

    result = " ".join(kept)
    # Ensure it ends with a period
    if result and not result.endswith("."):
        result += "."
    return result


def _term_alternatives(term: str) -> list:
    """Return acceptable alternative spellings/abbreviations for a term."""
    alt_map = {
        "january": ["january", "jan"],
        "march":   ["march", "mar"],
        "february":["february", "feb"],
    }
    return alt_map.get(term.lower(), [term.lower()])


def _check_scope_bleed(clause_num: str, entry: str, body: str) -> tuple:
    """
    Scans entry for scope bleed phrases.
    Returns (cleaned_entry, list_of_warning_strings).
    If a bleed phrase is found, re-derives from body (first sentence).
    """
    warnings = []
    entry_lower = entry.lower()
    for phrase in SCOPE_BLEED_PHRASES:
        if phrase.lower() in entry_lower:
            warnings.append(
                f"[WARN] Scope bleed detected in clause {clause_num}: "
                f"removed phrase '{phrase}'. Re-deriving from source text."
            )
            # Replace with a note and fall back to verbatim first sentence
            sentences = re.split(r"(?<=[.!?])\s+", body.strip())
            entry = sentences[0].strip() if sentences else body[:200]
    return entry, warnings


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summarisation Agent")
    parser.add_argument("--input",  required=True, help="Path to input .txt policy file")
    parser.add_argument("--output", required=True, help="Output filename (written inside uc-0b/)")
    args = parser.parse_args()

    output_path = os.path.join("uc-0b", args.output)

    # ── Skill 1: retrieve_policy ──
    try:
        policy = retrieve_policy(args.input)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(2)

    sections = policy["sections"]
    raw_text = policy["raw_text"]

    print(f"[INFO] Loaded {len([s for s in sections if s['clause_number']])} numbered clause(s) "
          f"from {args.input}")

    # ── Skill 2: summarize_policy ──
    try:
        summarize_policy(sections, raw_text, output_path)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(3)
    except PermissionError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()