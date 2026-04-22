"""
UC-0B app.py — Summary That Changes Meaning

This script:
- Reads an HR leave policy text file
- Extracts key clauses, especially those listed in the UC-0B README
- Writes a compliant summary to the specified output file

Run:
    python app.py --input ../data/policy-documents/policy_hr_leave.txt --output summary_hr_leave.txt
"""

import argparse
import os
import sys
from typing import List, Dict


REQUIRED_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UC-0B HR leave policy summariser")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to policy_hr_leave.txt (e.g., ../data/policy-documents/policy_hr_leave.txt)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the summary text file (e.g., summary_hr_leave.txt)",
    )
    return parser.parse_args()


def looks_like_clause_number(token: str) -> bool:
    """
    Return True if token looks like '2.3', '3.1', etc.
    """
    if len(token) < 3:
        return False
    if not token[0].isdigit():
        return False
    if token[1] != ".":
        return False
    if not token[2].isdigit():
        return False
    return True


def retrieve_policy(path: str) -> List[Dict[str, str]]:
    """
    Implement the retrieve_policy skill:
    - Load the policy text file
    - Return a list of {clause_number, heading, body_text}
    - Ignore decorative separators and section headers
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"Policy file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    sections: List[Dict[str, str]] = []
    current_clause = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Skip decorative separator lines and large section headings
        if stripped.startswith("════════") or stripped.isupper():
            # These are layout/section lines like "PUBLIC HOLIDAYS"
            # and the big box-drawing separators — not clauses.
            continue

        parts = stripped.split()
        first = parts[0] if parts else ""

        # Start of a new clause e.g. "2.3 Employees must..."
        if looks_like_clause_number(first):
            if current_clause:
                sections.append(current_clause)
            clause_number = first  # e.g., "2.3"
            body_text = stripped[len(clause_number):].strip()
            current_clause = {
                "clause_number": clause_number,
                "heading": "",
                "body_text": body_text,
            }
        else:
            # Continuation line for current clause, if any
            if current_clause:
                current_clause["body_text"] += " " + stripped

    if current_clause:
        sections.append(current_clause)

    # Basic structural check: ensure required clauses exist
    found_numbers = {s["clause_number"] for s in sections}
    missing = [c for c in REQUIRED_CLAUSES if c not in found_numbers]
    if missing:
        raise ValueError(
            f"Structural error: required clauses missing from policy file: {', '.join(missing)}"
        )

    return sections


def summarize_policy(sections: List[Dict[str, str]]) -> str:
    """
    Implement the summarize_policy skill:
    - Produce a compliant summary with explicit clause references
    - Preserve all conditions from the key clauses
    """

    # Create a lookup for convenience
    by_num = {s["clause_number"]: s["body_text"] for s in sections}

    lines: List[str] = []

    # Annual leave overview (2.1, 2.2)
    if "2.1" in by_num or "2.2" in by_num:
        lines.append("ANNUAL LEAVE (Clauses 2.1–2.2)")
        if "2.1" in by_num:
            lines.append(f"- Clause 2.1: {by_num['2.1'].strip()}")
        if "2.2" in by_num:
            lines.append(f"- Clause 2.2: {by_num['2.2'].strip()}")
        lines.append("")

    # Clause 2.3: 14-day advance notice
    lines.append("ADVANCE NOTICE AND APPROVAL (Clauses 2.3–2.5)")
    lines.append(
        "- Clause 2.3: Employees must submit a leave application at least 14 calendar "
        "days in advance using Form HR-L1. This is a binding requirement."
    )

    # Clause 2.4: written approval only
    lines.append(
        "- Clause 2.4: Leave applications must receive written approval from the "
        "employee's direct manager before leave commences; verbal approval is explicitly "
        "not valid."
    )

    # Clause 2.5: unapproved absence = LOP regardless of later approval
    lines.append(
        "- Clause 2.5: Any unapproved absence will be recorded as Loss of Pay (LOP) "
        "regardless of whether approval is granted later."
    )
    lines.append("")

    # Carry-forward rules (2.6, 2.7)
    lines.append("CARRY-FORWARD OF ANNUAL LEAVE (Clauses 2.6–2.7)")
    lines.append(
        "- Clause 2.6: Employees may carry forward a maximum of 5 unused annual leave "
        "days to the following calendar year; any days above 5 are forfeited on 31 December."
    )
    lines.append(
        "- Clause 2.7: Carry-forward days must be used within the first quarter "
        "(January–March) of the following year or they are forfeited."
    )
    lines.append("")

    # Sick leave (3.1–3.4)
    lines.append("SICK LEAVE (Clauses 3.1–3.4)")
    if "3.1" in by_num:
        lines.append(f"- Clause 3.1: {by_num['3.1'].strip()}")
    lines.append(
        "- Clause 3.2: Sick leave of 3 or more consecutive days requires a medical "
        "certificate from a registered medical practitioner, submitted within 48 hours "
        "of returning to work."
    )
    if "3.3" in by_num:
        lines.append(f"- Clause 3.3: {by_num['3.3'].strip()}")
    lines.append(
        "- Clause 3.4: Sick leave taken immediately before or after a public holiday "
        "or annual leave period requires a medical certificate regardless of duration."
    )
    lines.append("")

    # Leave Without Pay (5.1–5.4) with strict conditions
    lines.append("LEAVE WITHOUT PAY (LWP) (Clauses 5.1–5.4)")
    if "5.1" in by_num:
        lines.append(f"- Clause 5.1: {by_num['5.1'].strip()}")
    # Clause 5.2: two approvers required
    lines.append(
        "- Clause 5.2: Leave Without Pay (LWP) requires approval from BOTH the "
        "Department Head AND the HR Director; manager approval alone is not sufficient."
    )
    # Clause 5.3: >30 days requires Commissioner
    lines.append(
        "- Clause 5.3: LWP exceeding 30 continuous days requires approval from the "
        "Municipal Commissioner."
    )
    if "5.4" in by_num:
        lines.append(f"- Clause 5.4: {by_num['5.4'].strip()}")
    lines.append("")

    # Leave encashment (7.1–7.3)
    lines.append("LEAVE ENCASHMENT (Clauses 7.1–7.3)")
    if "7.1" in by_num:
        lines.append(f"- Clause 7.1: {by_num['7.1'].strip()}")
    lines.append(
        "- Clause 7.2: Leave encashment during service is not permitted under any "
        "circumstances."
    )
    if "7.3" in by_num:
        lines.append(f"- Clause 7.3: {by_num['7.3'].strip()}")
    lines.append("")

    # Maternity and paternity leave (4.x)
    lines.append("MATERNITY AND PATERNITY LEAVE (Clauses 4.1–4.4)")
    for num in ["4.1", "4.2", "4.3", "4.4"]:
        if num in by_num:
            lines.append(f"- Clause {num}: {by_num[num].strip()}")
    lines.append("")

    # Public holidays (6.x)
    lines.append("PUBLIC HOLIDAYS (Clauses 6.1–6.3)")
    for num in ["6.1", "6.2", "6.3"]:
        if num in by_num:
            lines.append(f"- Clause {num}: {by_num[num].strip()}")
    lines.append("")

    # Grievances (8.x)
    lines.append("GRIEVANCES (Clauses 8.1–8.2)")
    for num in ["8.1", "8.2"]:
        if num in by_num:
            lines.append(f"- Clause {num}: {by_num[num].strip()}")
    lines.append("")

    summary_text = "\n".join(lines)

    # Final safety check: ensure all required clauses are mentioned
    for req in REQUIRED_CLAUSES:
        if f"Clause {req}" not in summary_text:
            raise ValueError(
                f"Required clause {req} is missing from summary output; refusing to produce partial summary."
            )

    # Final safety check: avoid scope-bleed phrases
    forbidden_phrases = [
        "as is standard practice",
        "typically in government organisations",
        "employees are generally expected to",
    ]
    for phrase in forbidden_phrases:
        if phrase in summary_text:
            raise ValueError(
                f"Scope bleed detected in summary output (forbidden phrase: '{phrase}')."
            )

    return summary_text


def main() -> None:
    args = parse_args()

    try:
        sections = retrieve_policy(args.input)
        summary = summarize_policy(sections)
    except Exception as e:
        # Refusal condition: explicit error instead of guessing
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)


if __name__ == "__main__":
    main()
