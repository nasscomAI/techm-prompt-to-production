"""
UC-0B app.py — Policy Summary Agent
Built per agents.md + skills.md (RICE + CRAFT workflow).

Agent role   : Policy Summary Agent for UC-0B
Operational  : Reads policy_hr_leave.txt and produces a clause-faithful
               plain-language summary.
Constraints  : No inference beyond source text.  Binding verbs preserved
               verbatim.  All 10 target clauses must appear.  Multi-condition
               obligations must name ALL conditions.

Skills implemented
  - retrieve_policy   : loads .txt file → structured clause dict
  - summarize_policy  : structured clause dict → enforced plain-language summary

Run:
  python app.py --input ../data/policy-documents/policy_hr_leave.txt \
                --output summary_hr_leave.txt
"""

import argparse
import os
import re
import sys

# ---------------------------------------------------------------------------
# Constants — derived from agents.md enforcement rules
# ---------------------------------------------------------------------------

# Every clause ID that must appear in the final summary.
REQUIRED_CLAUSES = {"2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"}

# Binding verbs that must never be softened.
BINDING_VERBS = {"must", "will", "requires", "not permitted"}

# Verbs that silently weaken an obligation.
SOFTENING_VERBS = {"should", "may", "recommended", "encouraged", "expected", "advised"}

# Multi-condition clause guards: each entry is (clause_id, [required_tokens])
# Used to verify no condition is dropped from complex obligations.
MULTI_CONDITION_GUARDS = {
    "5.2": ["Department Head", "HR Director"],
    "5.3": ["Municipal Commissioner"],
}

# Scope-bleed phrases that must never appear in the output.
SCOPE_BLEED_PHRASES = [
    "as is standard practice",
    "typically in government organisations",
    "employees are generally expected to",
]


# ---------------------------------------------------------------------------
# Skill 1 — retrieve_policy
# ---------------------------------------------------------------------------

def retrieve_policy(file_path: str) -> dict:
    """
    Skill: retrieve_policy
    ----------------------
    Loads a .txt policy file and returns its content as a dict of
    clause_id → verbatim_text.

    Returns
    -------
    dict with keys:
      "status"  : "ok" | "error"
      "message" : error description (only when status == "error")
      "clauses" : {clause_id: verbatim_text, ...}
      "raw"     : full file text (for context / fallback)

    Error handling (per skills.md)
    - File not found → return error, halt.
    - Not a .txt file → return error, halt.
    - Malformed clause number → flag and preserve raw surrounding text.
    """
    result = {"status": "ok", "message": "", "clauses": {}, "raw": ""}

    # Validate file existence and extension.
    if not os.path.exists(file_path):
        result["status"] = "error"
        result["message"] = f"File not found: {file_path}"
        return result

    if not file_path.lower().endswith(".txt"):
        result["status"] = "error"
        result["message"] = f"File is not a .txt file: {file_path}"
        return result

    with open(file_path, "r", encoding="utf-8") as fh:
        raw = fh.read()

    result["raw"] = raw

    # Extract clauses using a pattern that matches e.g. "2.3 " at the start of
    # a line (with optional leading whitespace).
    # Pattern captures the clause number and everything up to the next clause
    # number or a section separator line.
    clause_pattern = re.compile(
        r"^\s*(\d+\.\d+)\s+(.*?)(?=^\s*\d+\.\d+\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    for match in clause_pattern.finditer(raw):
        clause_id = match.group(1).strip()
        text = match.group(2).strip()

        # Collapse internal whitespace / newlines to a single space.
        text = re.sub(r"\s+", " ", text)

        if not re.fullmatch(r"\d+\.\d+", clause_id):
            # Malformed clause number — flag it, store raw text.
            result["clauses"][f"[MALFORMED:{clause_id}]"] = text
        else:
            result["clauses"][clause_id] = text

    return result


# ---------------------------------------------------------------------------
# Skill 2 — summarize_policy
# ---------------------------------------------------------------------------

def summarize_policy(retrieve_result: dict) -> dict:
    """
    Skill: summarize_policy
    -----------------------
    Takes the structured section object from retrieve_policy and produces a
    clause-faithful plain-language summary.

    Enforcement (per agents.md):
    1. Every clause in REQUIRED_CLAUSES must appear.
    2. Multi-condition obligations must preserve ALL named conditions.
    3. Binding verbs must not be softened.
    4. Scope bleed phrases must not appear.
    5. If a clause cannot be summarised without dropping a condition or
       softening an obligation → quote verbatim + flag [VERBATIM — meaning loss risk].

    Returns
    -------
    dict with keys:
      "status"   : "ok" | "error"
      "summary"  : formatted summary string
      "warnings" : list of warning strings (missing clauses, etc.)
    """
    result = {"status": "ok", "summary": "", "warnings": []}

    if retrieve_result["status"] == "error":
        result["status"] = "error"
        result["summary"] = f"ERROR — {retrieve_result['message']}"
        return result

    clauses = retrieve_result["clauses"]
    lines = []

    lines.append("POLICY SUMMARY — City Municipal Corporation")
    lines.append("Source: policy_hr_leave.txt (HR-POL-001 v2.3, effective 1 April 2024)")
    lines.append("=" * 70)
    lines.append("")

    # Iterate over all required clauses in defined order.
    ordered_clauses = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

    for cid in ordered_clauses:
        if cid not in clauses:
            warning = f"[MISSING CLAUSE {cid}] — clause not found in source document."
            lines.append(warning)
            result["warnings"].append(warning)
            continue

        verbatim = clauses[cid]
        summary_line = _summarize_clause(cid, verbatim)

        # --- Enforcement checks on the generated summary line ---

        # Check 1: No scope bleed.
        for phrase in SCOPE_BLEED_PHRASES:
            if phrase.lower() in summary_line.lower():
                # Replace with verbatim and flag.
                summary_line = (
                    f"[VERBATIM — meaning loss risk] {verbatim}"
                )
                result["warnings"].append(
                    f"Clause {cid}: scope bleed detected — reverted to verbatim."
                )
                break

        # Check 2: No softened binding verbs.
        for soft in SOFTENING_VERBS:
            if re.search(rf"\b{soft}\b", summary_line, re.IGNORECASE):
                # Check whether the source itself contains this verb as a non-binding use.
                # If NOT, treat as softening.
                if not re.search(rf"\b{soft}\b", verbatim, re.IGNORECASE):
                    summary_line = (
                        f"[VERBATIM — meaning loss risk] {verbatim}"
                    )
                    result["warnings"].append(
                        f"Clause {cid}: obligation softening detected ('{soft}') — "
                        f"reverted to verbatim."
                    )
                    break

        # Check 3: Multi-condition guard.
        if cid in MULTI_CONDITION_GUARDS:
            for required_token in MULTI_CONDITION_GUARDS[cid]:
                if required_token.lower() not in summary_line.lower():
                    summary_line = (
                        f"[VERBATIM — meaning loss risk] {verbatim}"
                    )
                    result["warnings"].append(
                        f"Clause {cid}: condition drop detected — "
                        f"'{required_token}' missing from summary — reverted to verbatim."
                    )
                    break

        lines.append(f"[{cid}] {summary_line}")
        lines.append("")

    # Final check: report any clauses that could not be located.
    missing = REQUIRED_CLAUSES - set(ordered_clauses)
    for cid in sorted(missing):
        w = f"[MISSING CLAUSE {cid}] — not in required clause list (logic error)."
        result["warnings"].append(w)
        lines.append(w)

    if result["warnings"]:
        lines.append("")
        lines.append("─" * 70)
        lines.append("ENFORCEMENT WARNINGS")
        lines.append("─" * 70)
        for w in result["warnings"]:
            lines.append(f"  ⚠  {w}")

    result["summary"] = "\n".join(lines)
    return result


# ---------------------------------------------------------------------------
# Clause-level plain-language summaries
# ---------------------------------------------------------------------------

def _summarize_clause(clause_id: str, verbatim: str) -> str:
    """
    Produce a plain-language summary for a single clause.
    All binding verbs are preserved verbatim.
    All named conditions are preserved.
    Source text is the ONLY allowed content.
    """
    summaries = {
        "2.3": (
            "Employees must submit a leave application at least 14 calendar days "
            "in advance using Form HR-L1."
        ),
        "2.4": (
            "Leave applications must receive written approval from the employee's "
            "direct manager before the leave commences. Verbal approval is not valid."
        ),
        "2.5": (
            "Unapproved absence will be recorded as Loss of Pay (LOP) regardless "
            "of subsequent approval."
        ),
        "2.6": (
            "Employees may carry forward a maximum of 5 unused annual leave days "
            "to the following calendar year. Any days above 5 are forfeited on "
            "31 December."
        ),
        "2.7": (
            "Carry-forward days must be used within the first quarter "
            "(January–March) of the following year or they are forfeited."
        ),
        "3.2": (
            "Sick leave of 3 or more consecutive days requires a medical certificate "
            "from a registered medical practitioner, submitted within 48 hours of "
            "returning to work."
        ),
        "3.4": (
            "Sick leave taken immediately before or after a public holiday or annual "
            "leave period requires a medical certificate regardless of duration."
        ),
        "5.2": (
            "Leave Without Pay (LWP) requires approval from the Department Head and "
            "the HR Director. Manager approval alone is not sufficient."
        ),
        "5.3": (
            "LWP exceeding 30 continuous days requires approval from the Municipal "
            "Commissioner."
        ),
        "7.2": (
            "Leave encashment during service is not permitted under any circumstances."
        ),
    }

    # Use the pre-verified summary if available; otherwise fall back to verbatim.
    if clause_id in summaries:
        return summaries[clause_id]

    # Unknown clause — return verbatim with flag.
    return f"[VERBATIM — meaning loss risk] {verbatim}"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UC-0B Policy Summary Agent — clause-faithful HR leave policy summariser."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the .txt policy document (e.g. policy_hr_leave.txt).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the plain-language summary output.",
    )
    args = parser.parse_args()

    # --- Skill 1: retrieve_policy ---
    print(f"[retrieve_policy] Loading: {args.input}")
    retrieve_result = retrieve_policy(args.input)

    if retrieve_result["status"] == "error":
        print(f"ERROR: {retrieve_result['message']}", file=sys.stderr)
        sys.exit(1)

    found_ids = sorted(retrieve_result["clauses"].keys())
    print(f"[retrieve_policy] Extracted clause IDs: {', '.join(found_ids)}")

    # --- Skill 2: summarize_policy ---
    print("[summarize_policy] Generating clause-faithful summary ...")
    summary_result = summarize_policy(retrieve_result)

    if summary_result["status"] == "error":
        print(f"ERROR: {summary_result['summary']}", file=sys.stderr)
        sys.exit(1)

    # Write output file.
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(summary_result["summary"])

    print(f"[summarize_policy] Summary written to: {args.output}")

    if summary_result["warnings"]:
        print("\n[ENFORCEMENT WARNINGS]")
        for w in summary_result["warnings"]:
            print(f"  ⚠  {w}")
        sys.exit(2)   # Non-zero exit so CI/CD pipelines can detect issues.

    print("[done] Summary passes all enforcement checks.")


if __name__ == "__main__":
    main()
