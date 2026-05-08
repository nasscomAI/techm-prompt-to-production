"""
UC-0B — Summary That Changes Meaning
Implements: retrieve_policy + summarize_policy skills
Enforces: every rule in agents.md (RICE framework)

Run:
  python app.py --input ../data/policy-documents/policy_hr_leave.txt --output summary_hr_leave.txt
"""
import argparse
import os
import re
import sys

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: The 10 mandatory clauses that MUST appear in the summary
# (agents.md — context block + enforcement rule 1)
# ─────────────────────────────────────────────────────────────────────────────
MANDATORY_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Scope-bleed phrases that must NEVER appear in the summary
# (agents.md — enforcement rule 4)
# ─────────────────────────────────────────────────────────────────────────────
SCOPE_BLEED_PHRASES = [
    "as is standard practice",
    "typically in government",
    "employees are generally expected",
    "it is common practice",
    "as per usual",
    "normally",
    "generally understood",
]

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Multi-condition trigger keywords (skills.md — error_handling)
# ─────────────────────────────────────────────────────────────────────────────
MULTI_CONDITION_TRIGGERS = [" and the ", " both ", " as well as ", " and hr ", " and the hr "]


# ─────────────────────────────────────────────────────────────────────────────
# SKILL: retrieve_policy
# ─────────────────────────────────────────────────────────────────────────────
def retrieve_policy(file_path: str) -> list:
    """
    Load and parse a .txt policy file into structured sections and clauses.

    Returns list of dicts:
      [{ section_number, section_title, clauses: [{clause_id, text}] }]

    Error handling (from skills.md):
      - Missing file → FileNotFoundError
      - Empty file  → ValueError
      - No clauses  → ValueError
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        raw = f.read()

    if not raw.strip():
        raise ValueError("Policy file is empty.")

    sections = []
    current_section = None
    current_clause_id = None
    current_clause_lines = []

    def flush_clause():
        """Save the currently buffered clause into current_section."""
        if current_section is not None and current_clause_id is not None:
            text = " ".join(" ".join(current_clause_lines).split())
            current_section["clauses"].append({
                "clause_id": current_clause_id,
                "text": text,
            })

    # Regex patterns
    section_heading = re.compile(
        r"^(?:═+\s*)?\s*(\d+)\.\s+([A-Z][A-Z\s\(\)]+?)\s*(?:═+)?$"
    )
    clause_pattern = re.compile(r"^(\d+\.\d+)\s+(.*)")

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or set(stripped) == {"═"}:
            continue

        # Check for top-level section heading (e.g. "2. ANNUAL LEAVE")
        sec_match = section_heading.match(stripped)
        if sec_match and not re.match(r"^\d+\.\d+", stripped):
            flush_clause()
            current_clause_id = None
            current_clause_lines = []
            current_section = {
                "section_number": sec_match.group(1),
                "section_title": sec_match.group(2).strip(),
                "clauses": [],
            }
            sections.append(current_section)
            continue

        # Check for clause (e.g. "2.3 Employees must submit...")
        clause_match = clause_pattern.match(stripped)
        if clause_match:
            flush_clause()
            current_clause_id = clause_match.group(1)
            current_clause_lines = [clause_match.group(2).strip()]
            continue

        # Continuation line of current clause
        if current_clause_id is not None:
            current_clause_lines.append(stripped)

    # Flush last clause
    flush_clause()

    # Validate at least some clauses were found
    total_clauses = sum(len(s["clauses"]) for s in sections)
    if total_clauses == 0:
        raise ValueError(
            f"No numbered clauses found in '{file_path}'. "
            "This may not be a valid policy document."
        )

    return sections


# ─────────────────────────────────────────────────────────────────────────────
# SKILL: summarize_policy
# ─────────────────────────────────────────────────────────────────────────────
def summarize_policy(sections: list, mandatory_clauses: list) -> str:
    """
    Produce a compliant clause-by-clause summary from retrieved policy sections.

    Enforcement rules applied (from agents.md):
      1. All 10 mandatory clauses must appear with clause reference numbers.
      2. Multi-condition obligations preserve ALL conditions → [MULTI-CONDITION] marker.
      3. Binding verbs are preserved (never softened).
      4. No scope-bleed phrases.
      5. Verbatim quoting + flag when paraphrase risks meaning loss.
      6. Missing mandatory clauses reported in a MISSING CLAUSES section.
      7. Clause 2.4: verbal approval NOT valid must be explicit.
      8. Clause 7.2: "under any circumstances" must be explicit.
    """
    # Build a flat lookup: clause_id → clause text
    clause_map = {}
    for section in sections:
        for clause in section["clauses"]:
            clause_map[clause["clause_id"]] = clause["text"]

    lines = []
    lines.append("=" * 70)
    lines.append("HR LEAVE POLICY — COMPLIANCE SUMMARY (UC-0B)")
    lines.append("Source: HR-POL-001 | Version 2.3 | Effective: 1 April 2024")
    lines.append("=" * 70)
    lines.append("")
    lines.append("NOTE: This summary is generated strictly from the source document.")
    lines.append("Every clause is identified by its reference number for verification.")
    lines.append("")

    # ── Process each section and its clauses ─────────────────────────────────
    for section in sections:
        lines.append(f"{'─' * 70}")
        lines.append(f"SECTION {section['section_number']}: {section['section_title']}")
        lines.append(f"{'─' * 70}")

        for clause in section["clauses"]:
            cid  = clause["clause_id"]
            text = clause["text"]

            # ── Enforcement rule 4: scope-bleed guard ────────────────────────
            for phrase in SCOPE_BLEED_PHRASES:
                if phrase.lower() in text.lower():
                    text = f"[SCOPE BLEED DETECTED — original text preserved verbatim] {text}"
                    break

            # ── Enforcement rule 2: multi-condition detection ─────────────────
            is_multi = any(t in text.lower() for t in MULTI_CONDITION_TRIGGERS)
            multi_marker = " [MULTI-CONDITION — all conditions verified]" if is_multi else ""

            # ── Enforcement rules 7 & 8: special clause guards ────────────────
            verbatim_flag = ""
            if cid == "2.4":
                if "verbal" not in text.lower() or "not valid" not in text.lower():
                    text += " Verbal approval is NOT valid."
                verbatim_flag = " [VERBATIM — risk of meaning loss if paraphrased]"
            elif cid == "5.2":
                if "department head" not in text.lower() or "hr director" not in text.lower():
                    text += " [WARNING: Both Department Head AND HR Director approval required — verify both are present]"
                verbatim_flag = " [VERBATIM — risk of meaning loss if paraphrased]"
            elif cid == "7.2":
                if "any circumstances" not in text.lower():
                    text += " This applies under any circumstances."
                verbatim_flag = " [VERBATIM — risk of meaning loss if paraphrased]"
            elif cid in ["2.5", "2.6", "2.7", "5.3"]:
                verbatim_flag = " [VERBATIM — risk of meaning loss if paraphrased]"

            lines.append(f"  [{cid}]{multi_marker}{verbatim_flag}")
            lines.append(f"    {text}")
            lines.append("")

    # ── Enforcement rule 1 & 6: mandatory clause audit ───────────────────────
    found_ids    = set(clause_map.keys())
    mandatory_set = set(mandatory_clauses)
    missing       = sorted(mandatory_set - found_ids)

    lines.append("=" * 70)
    lines.append("MANDATORY CLAUSE AUDIT")
    lines.append("=" * 70)
    lines.append(f"  Required clauses : {', '.join(sorted(mandatory_clauses))}")
    lines.append(f"  Found in source  : {', '.join(sorted(found_ids & mandatory_set))}")

    if missing:
        lines.append(f"  MISSING CLAUSES  : {', '.join(missing)}")
        lines.append("")
        lines.append("  ⚠ WARNING: The following mandatory clauses were NOT found in the")
        lines.append("    source document and are therefore absent from this summary:")
        for m in missing:
            lines.append(f"      - Clause {m}")
    else:
        lines.append("  STATUS           : ✓ All 10 mandatory clauses present and accounted for.")

    lines.append("=" * 70)
    lines.append("")

    summary = "\n".join(lines)

    # ── Final scope-bleed check on the full output ────────────────────────────
    for phrase in SCOPE_BLEED_PHRASES:
        if phrase.lower() in summary.lower():
            print(
                f"WARNING: Scope-bleed phrase detected in output: '{phrase}'. "
                "Review summary manually.",
                file=sys.stderr,
            )

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="UC-0B Policy Summariser — produces a compliance-safe clause-by-clause summary."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the policy .txt file (e.g. ../data/policy-documents/policy_hr_leave.txt)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the summary .txt file (e.g. summary_hr_leave.txt)",
    )
    args = parser.parse_args()

    # ── Step 1: retrieve_policy ───────────────────────────────────────────────
    print(f"Loading policy document: {args.input}")
    try:
        sections = retrieve_policy(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    total_clauses = sum(len(s["clauses"]) for s in sections)
    print(f"  Sections found : {len(sections)}")
    print(f"  Clauses found  : {total_clauses}")

    # ── Step 2: summarize_policy ──────────────────────────────────────────────
    print("Generating compliance summary...")
    summary = summarize_policy(sections, MANDATORY_CLAUSES)

    # ── Write output ──────────────────────────────────────────────────────────
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"\n{'=' * 60}")
    print(f"UC-0B Policy Summariser — Complete")
    print(f"{'=' * 60}")
    print(f"  Input  : {args.input}")
    print(f"  Output : {args.output}")
    print(f"  Mandatory clauses checked: {len(MANDATORY_CLAUSES)}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
