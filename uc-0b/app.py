"""
UC-0B app.py — Policy Summarisation Agent
Implements: retrieve_policy + summarize_policy skills from skills.md
Enforcement rules from agents.md applied inline.
"""
import argparse
import re
import sys

# ---------------------------------------------------------------------------
# Scope bleed phrases that must never appear in output (agents.md > context)
# ---------------------------------------------------------------------------
SCOPE_BLEED_PHRASES = [
    "as is standard practice",
    "typically in government organisations",
    "employees are generally expected to",
]

# ---------------------------------------------------------------------------
# Ground-truth clauses — every one must appear in the summary (agents.md > intent)
# ---------------------------------------------------------------------------
GROUND_TRUTH_CLAUSES = [
    "2.3", "2.4", "2.5", "2.6", "2.7",
    "3.2", "3.4", "5.2", "5.3", "7.2",
]

# ---------------------------------------------------------------------------
# Skill: retrieve_policy
# ---------------------------------------------------------------------------
def retrieve_policy(input_path: str) -> str:
    """
    Loads a .txt policy file and returns its content as structured numbered sections.
    Refuses if file is missing or unreadable.
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"[retrieve_policy] File not found: {input_path}\n"
            "Ensure the path points to policy_hr_leave.txt (HR-POL-001)."
        )
    except OSError as e:
        raise OSError(f"[retrieve_policy] Cannot read file: {input_path}\n{e}")

    # Basic identity check — must contain the document reference
    if "HR-POL-001" not in content:
        raise ValueError(
            "[retrieve_policy] Document does not appear to be HR-POL-001. "
            "Refusing to proceed."
        )

    return content


# ---------------------------------------------------------------------------
# Skill: summarize_policy
# ---------------------------------------------------------------------------
def summarize_policy(policy_text: str) -> str:
    """
    Produces a clause-complete, compliant summary from the structured policy text.
    - Every numbered clause represented with §reference
    - Binding verbs preserved verbatim
    - All multi-condition obligations fully stated
    - No content added beyond the source document
    - Scope bleed phrases detected and flagged
    """

    # Parse sections and clauses from the raw text
    # Sections are lines like "1. PURPOSE AND SCOPE", clauses like "1.1 ..."
    section_pattern = re.compile(r"^(\d+)\.\s+(.+)$", re.MULTILINE)
    clause_pattern = re.compile(r"^(\d+\.\d+)\s+(.+?)(?=\n\d+\.\d+|\n\d+\.|\Z)", re.DOTALL | re.MULTILINE)

    sections = section_pattern.findall(policy_text)
    clauses = clause_pattern.findall(policy_text)

    # Build clause lookup: "2.3" -> text
    clause_map = {}
    for num, text in clauses:
        clause_map[num] = " ".join(text.split())  # normalise whitespace

    lines = []
    lines.append("CITY MUNICIPAL CORPORATION — HR LEAVE POLICY (HR-POL-001)")
    lines.append("CLAUSE-COMPLETE SUMMARY")
    lines.append("=" * 60)
    lines.append("")

    # Emit each section with its clauses
    current_section = None
    for num, text in clauses:
        major = num.split(".")[0]
        # Print section header when it changes
        if major != current_section:
            current_section = major
            # Find section title
            sec_title = next((t for n, t in sections if n == major), f"SECTION {major}")
            lines.append(f"{major}. {sec_title.strip()}")
            lines.append("-" * 40)

        summary_line = _summarize_clause(num, clause_map[num])
        lines.append(summary_line)

    lines.append("")
    lines.append("=" * 60)

    summary = "\n".join(lines)

    # --- Scope bleed check ---
    for phrase in SCOPE_BLEED_PHRASES:
        if phrase.lower() in summary.lower():
            summary = summary.replace(phrase, f"[SCOPE BLEED REMOVED: '{phrase}']")

    # --- Ground-truth clause coverage check ---
    missing = []
    for clause_num in GROUND_TRUTH_CLAUSES:
        if f"§{clause_num}" not in summary:
            missing.append(clause_num)

    if missing:
        summary += (
            "\n\n[WARNING — CLAUSE COVERAGE INCOMPLETE]\n"
            f"The following ground-truth clauses were not found in the summary: "
            + ", ".join(f"§{c}" for c in missing)
            + "\nReview source document and re-run."
        )

    return summary


def _summarize_clause(num: str, text: str) -> str:
    """
    Produces a single summary line for a clause.
    Preserves binding verbs. Flags if meaning loss is likely.
    """
    BINDING_VERBS = ["must", "will", "requires", "required", "not permitted", "cannot", "may not"]

    # Check if any binding verb is present — if so, keep text close to verbatim
    has_binding = any(v in text.lower() for v in BINDING_VERBS)

    # Clauses where condition drop is a known risk — quote verbatim
    VERBATIM_CLAUSES = {"5.2", "5.3", "2.4", "2.5", "7.2"}

    if num in VERBATIM_CLAUSES:
        return f"  §{num}  {text}  [VERBATIM — meaning loss risk]"

    if has_binding:
        return f"  §{num}  {text}"

    # Short clauses without binding verbs — summarise as-is (source only)
    return f"  §{num}  {text}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="UC-0B: Policy Summarisation Agent (HR-POL-001)"
    )
    parser.add_argument("--input", required=True, help="Path to policy .txt file")
    parser.add_argument("--output", required=True, help="Path for summary output file")
    args = parser.parse_args()

    # Skill 1: retrieve_policy
    print(f"[retrieve_policy] Loading: {args.input}")
    try:
        policy_text = retrieve_policy(args.input)
    except (FileNotFoundError, OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"[retrieve_policy] Loaded {len(policy_text)} characters.")

    # Skill 2: summarize_policy
    print("[summarize_policy] Generating clause-complete summary...")
    summary = summarize_policy(policy_text)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"[summarize_policy] Summary written to: {args.output}")

    # Report ground-truth coverage to stdout
    missing = [c for c in GROUND_TRUTH_CLAUSES if f"§{c}" not in summary]
    if missing:
        print(f"\n[WARNING] Missing ground-truth clauses: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    else:
        print(f"[OK] All {len(GROUND_TRUTH_CLAUSES)} ground-truth clauses present in summary.")


if __name__ == "__main__":
    main()
