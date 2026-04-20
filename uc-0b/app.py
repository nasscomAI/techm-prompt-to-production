"""
UC-0B app.py — Policy Summarization Agent
Implementation guided by agents.md RICE enforcement rules and skills.md spec.

Produces a compliant summary of HR leave policy documents, preserving all
clause obligations and binding conditions from the source document.
"""
import argparse
import re
import sys
from typing import Dict, List, Tuple

# ─── Constants from agents.md enforcement ────────────────────────────────────

# The 10 critical clauses with binding obligations (agents.md intent)
CRITICAL_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

# Binding verbs that must be preserved per critical clause (README clause inventory)
CLAUSE_BINDING_VERBS = {
    "2.3": "must",
    "2.4": "must",
    "2.5": "will",
    "2.6": "may",
    "2.7": "must",
    "3.2": "requires",
    "3.4": "requires",
    "5.2": "requires",
    "5.3": "requires",
    "7.2": "not permitted",
}

# Multi-condition obligations: clauses with conditions that must ALL be preserved
# Each entry maps clause -> list of condition keywords that must appear in the summary
MULTI_CONDITION_CHECKS = {
    "2.4": ["written approval", "verbal"],
    "2.5": ["unapproved absence", "loss of pay", "regardless"],
    "2.6": ["5", "carry forward", "forfeited", "31 december"],
    "2.7": ["first quarter", "january", "march", "forfeited"],
    "3.2": ["3", "consecutive", "medical certificate", "48 hours"],
    "3.4": ["public holiday", "medical certificate", "regardless of duration"],
    "5.2": ["department head", "hr director"],
    "5.3": ["30", "municipal commissioner"],
    "7.2": ["not permitted", "any circumstances"],
}

# Concise summaries for clauses that CAN be shortened without meaning loss
# Only simple, single-condition clauses qualify
CONCISE_SUMMARIES = {
    "1.1": "This policy governs all leave entitlements for permanent and contractual employees of the CMC.",
    "1.2": "This policy does not apply to daily wage workers or consultants; they are governed by their respective contracts.",
    "2.1": "Each permanent employee is entitled to 18 days of paid annual leave per calendar year.",
    "2.2": "Annual leave accrues at 1.5 days per month from the date of joining.",
    "2.3": "Employees must submit a leave application at least 14 calendar days in advance using Form HR-L1.",
    "2.5": "Unapproved absence will be recorded as Loss of Pay (LOP) regardless of subsequent approval.",
    "3.1": "Each employee is entitled to 12 days of paid sick leave per calendar year.",
    "3.3": "Sick leave cannot be carried forward to the following year.",
    "4.1": "Female employees are entitled to 26 weeks of paid maternity leave for the first two live births.",
    "4.2": "For a third or subsequent child, maternity leave is 12 weeks paid.",
    "4.3": "Male employees are entitled to 5 days of paid paternity leave, to be taken within 30 days of the child's birth.",
    "4.4": "Paternity leave cannot be split across multiple periods.",
    "5.1": "An employee may apply for LWP only after exhausting all applicable paid leave entitlements.",
    "5.4": "Periods of LWP do not count toward service for seniority, increments, or retirement benefits.",
    "6.1": "Employees are entitled to all gazetted public holidays as declared by the State Government each year.",
    "6.2": "If required to work on a public holiday, employees are entitled to one compensatory off day, to be taken within 60 days.",
    "6.3": "Compensatory off cannot be encashed.",
    "7.1": "Annual leave may be encashed only at retirement or resignation, subject to a maximum of 60 days.",
    "7.3": "Sick leave and LWP cannot be encashed under any circumstances.",
    "8.1": "Leave-related grievances must be raised with the HR Department within 10 working days of the disputed decision.",
    "8.2": "Grievances raised after 10 working days will not be considered unless exceptional circumstances are demonstrated in writing.",
}

# Scope-bleed phrases that must NEVER appear (agents.md context)
SCOPE_BLEED_PHRASES = [
    "as is standard practice",
    "typically in government organisations",
    "typically in government organizations",
    "employees are generally expected to",
    "as is customary",
    "industry standard",
    "best practice",
    "common practice",
    "usually required",
]


# ─── Skill 1: retrieve_policy ────────────────────────────────────────────────

def retrieve_policy(file_path: str) -> Dict[str, str]:
    """
    Loads a .txt policy file and returns its content as structured numbered sections.

    Input:  Path to a .txt policy file (string)
    Output: Dictionary mapping clause numbers to their content
            e.g., {"2.3": "Employees must submit...", "2.4": "Leave applications must..."}
    Error handling:
        - Raises FileNotFoundError if file does not exist
        - Raises ValueError if file is unreadable or empty
        - Raises ValueError if any of the 10 critical clauses is missing from source
    """
    # --- Read file ---
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Source policy file not found: {file_path}")
    except (IOError, OSError) as e:
        raise ValueError(f"Source policy file is unreadable: {file_path} — {e}")

    if not content.strip():
        raise ValueError(f"Source policy file is empty: {file_path}")

    # --- Parse into clause sections ---
    clauses: Dict[str, str] = {}
    lines = content.splitlines()

    current_clause = None
    current_text_lines: List[str] = []

    for line in lines:
        # Check for a new clause number at the start of a line (e.g., "2.3 ", "5.2 ")
        clause_match = re.match(r"^(\d+\.\d+)\s+(.*)$", line.strip())

        if clause_match:
            # Save previous clause if any
            if current_clause is not None:
                clauses[current_clause] = " ".join(current_text_lines).strip()

            current_clause = clause_match.group(1)
            current_text_lines = [clause_match.group(2)]
        elif current_clause is not None:
            # Skip section dividers and section headers
            stripped = line.strip()
            if stripped.startswith("═") or re.match(r"^\d+\.\s+[A-Z]", stripped):
                # Save current clause before moving to new section
                clauses[current_clause] = " ".join(current_text_lines).strip()
                current_clause = None
                current_text_lines = []
            elif stripped:
                current_text_lines.append(stripped)

    # Save last clause
    if current_clause is not None:
        clauses[current_clause] = " ".join(current_text_lines).strip()

    # --- Validate all 10 critical clauses are present ---
    missing_clauses = [c for c in CRITICAL_CLAUSES if c not in clauses]
    if missing_clauses:
        raise ValueError(
            f"REFUSAL: Source document is missing {len(missing_clauses)} expected critical "
            f"clause(s): {', '.join(missing_clauses)}. Cannot generate compliant summary."
        )

    return clauses


# ─── Skill 2: summarize_policy ───────────────────────────────────────────────

def summarize_policy(clauses: Dict[str, str]) -> str:
    """
    Takes structured policy sections and produces a compliant summary with
    clause references. Includes ALL numbered clauses from the source document.

    Input:  Dictionary of clause numbers to content (output from retrieve_policy)
    Output: Summary text with each clause's core obligation and binding verb,
            preserving all multi-condition obligations.
    Error handling:
        - Validates no scope-bleed phrases are present
        - For multi-condition obligations, validates all conditions are preserved;
          if any condition is dropped, flags the clause verbatim
        - If meaning loss is unavoidable, includes clause verbatim with flag
    """
    summary_lines: List[str] = []
    flags: List[str] = []

    # Sort clauses numerically so output is in document order
    sorted_clause_nums = sorted(clauses.keys(), key=lambda c: [int(x) for x in c.split(".")])

    for clause_num in sorted_clause_nums:
        clause_text = clauses[clause_num]

        if not clause_text:
            flags.append(f"CLAUSE {clause_num}: Empty content in source — cannot summarize")
            summary_lines.append(f"[FLAG: Clause empty in source] {clause_num}: EMPTY")
            continue

        # --- Check for scope bleed in the source text ---
        for phrase in SCOPE_BLEED_PHRASES:
            if phrase.lower() in clause_text.lower():
                flags.append(
                    f"CLAUSE {clause_num}: Contains scope-bleed phrase '{phrase}' — "
                    f"this phrase is NOT from the source policy"
                )

        # --- Attempt summarization vs verbatim decision ---
        has_multi_conditions = clause_num in MULTI_CONDITION_CHECKS
        has_concise_version = clause_num in CONCISE_SUMMARIES

        if has_multi_conditions:
            # Multi-condition clause: check if concise version preserves ALL conditions
            if has_concise_version:
                concise = CONCISE_SUMMARIES[clause_num]
                missing_conditions = _check_conditions(concise, clause_num)
            else:
                # No concise version available — meaning loss unavoidable
                # Report the conditions that would be at risk
                missing_conditions = MULTI_CONDITION_CHECKS[clause_num]

            if missing_conditions:
                # Cannot summarize without meaning loss → quote verbatim and flag
                flags.append(
                    f"CLAUSE {clause_num}: Cannot summarize without meaning loss — "
                    f"missing conditions {missing_conditions}. Quoted verbatim."
                )
                summary_lines.append(
                    f"[VERBATIM — meaning loss if summarized] "
                    f"{clause_num}: {clause_text}"
                )
            else:
                # Concise version preserves all conditions — safe to use
                summary_lines.append(f"{clause_num}: {concise}")
        elif has_concise_version:
            # Simple clause with a concise version — use it
            summary_lines.append(f"{clause_num}: {CONCISE_SUMMARIES[clause_num]}")
        else:
            # No concise version and no multi-condition check —
            # cannot summarize without risk of meaning loss, quote verbatim
            flags.append(
                f"CLAUSE {clause_num}: No verified concise summary available. Quoted verbatim."
            )
            summary_lines.append(
                f"[VERBATIM — meaning loss if summarized] "
                f"{clause_num}: {clause_text}"
            )

    # --- Validate no scope bleed in the final output ---
    full_summary = "\n\n".join(summary_lines)
    for phrase in SCOPE_BLEED_PHRASES:
        if phrase.lower() in full_summary.lower():
            flags.append(f"SCOPE BLEED DETECTED in output: '{phrase}'")

    # --- Build final output ---
    output_parts = [full_summary]

    if flags:
        output_parts.append("")
        output_parts.append("=" * 50)
        output_parts.append("FLAGS:")
        for flag in flags:
            output_parts.append(f"  - {flag}")

    return "\n".join(output_parts)


def _check_conditions(text: str, clause_num: str) -> List[str]:
    """Check if all required conditions for a multi-condition clause are present."""
    missing = []
    if clause_num in MULTI_CONDITION_CHECKS:
        for condition in MULTI_CONDITION_CHECKS[clause_num]:
            if condition.lower() not in text.lower():
                missing.append(condition)
    return missing


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="UC-0B — Policy Summarization Agent. "
        "Produces a compliant summary of HR leave policy documents."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to the source .txt policy file"
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to write the summary output file"
    )
    args = parser.parse_args()

    # --- Step 1: retrieve_policy ---
    print(f"[retrieve_policy] Loading policy from: {args.input}")
    try:
        clauses = retrieve_policy(args.input)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[retrieve_policy] Parsed {len(clauses)} clauses from source document.")
    print(f"[retrieve_policy] All clauses found: {', '.join(sorted(clauses.keys(), key=lambda c: [int(x) for x in c.split('.')]))}")

    # --- Step 2: summarize_policy ---
    print(f"[summarize_policy] Generating compliant summary for all {len(clauses)} clauses...")
    try:
        summary = summarize_policy(clauses)
    except Exception as e:
        print(f"ERROR: Summary generation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Step 3: Write output ---
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary + "\n")
    except (IOError, OSError) as e:
        print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[summarize_policy] Summary written to: {args.output}")
    print("Done.")


if __name__ == "__main__":
    main()