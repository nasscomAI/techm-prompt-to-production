"""
UC-0B — Policy Summarizer
Built from agents.md (RICE: Role, Intent, Context, Enforcement) and skills.md.

Skills implemented:
  - retrieve_policy   : loads .txt policy file, returns structured numbered sections
  - summarize_policy  : takes structured sections, produces clause-accurate summary

Run:
  python app.py --input ../data/policy-documents/policy_hr_leave.txt --output summary_hr_leave.txt
"""

import argparse
import os
import re
import sys

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ---------------------------------------------------------------------------
# RICE enforcement constants — sourced directly from agents.md
# ---------------------------------------------------------------------------

# 10 high-risk clauses that MUST appear in every summary output
HIGH_RISK_CLAUSES = {
    "2.3": "14-day advance notice required (must)",
    "2.4": "Written approval required before leave commences; verbal not valid",
    "2.5": "Unapproved absence = LOP regardless of subsequent approval",
    "2.6": "Max 5 days carry-forward; above 5 forfeited on 31 December",
    "2.7": "Carry-forward days must be used January-March or forfeited",
    "3.2": "3+ consecutive sick days requires medical certificate within 48 hours",
    "3.4": "Sick leave before/after public holiday requires certificate regardless of duration",
    "5.2": "LWP requires approval from BOTH Department Head AND HR Director",
    "5.3": "LWP exceeding 30 days requires Municipal Commissioner approval",
    "7.2": "Leave encashment during service not permitted under any circumstances",
}

# Scope-bleed phrases forbidden in output — from agents.md context section
FORBIDDEN_PHRASES = [
    "as is standard practice",
    "typically in government",
    "employees are generally expected",
    "generally not permitted",
    "rarely allowed",
    "it is common practice",
    "generally understood",
    "while not explicitly covered",
]

# Obligation-softening substitutions to detect
SOFTENING_MAP = {
    "recommended": ["must", "required"],
    "expected to": ["must", "required"],
    "should": ["must", "will"],
    "may wish to": ["must"],
}

# ---------------------------------------------------------------------------
# RICE-enforced system prompt — derived from agents.md
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a Policy Summarization Agent.

ROLE:
Your only job is to summarize a structured HR leave policy document in a way
that is clause-accurate and meaning-preserving. You must treat every numbered
clause as a mandatory output element. You must never soften obligations, drop
conditions, or introduce information from outside the document.

INTENT:
Produce a structured plain-text summary where every clause appears, every
binding verb is preserved (must, will, requires, not permitted), every numeric
threshold is retained, and every named approver is listed. The following 10
clauses are high-risk and MUST appear in your output with full fidelity:

  2.3 - 14-day advance notice required (must)
  2.4 - Written approval required before leave commences; verbal not valid
  2.5 - Unapproved absence = LOP regardless of subsequent approval
  2.6 - Max 5 days carry-forward; above 5 forfeited on 31 December
  2.7 - Carry-forward days must be used January-March or forfeited
  3.2 - 3+ consecutive sick days requires medical certificate within 48 hours
  3.4 - Sick leave before/after public holiday requires certificate regardless of duration
  5.2 - LWP requires approval from BOTH Department Head AND HR Director (BOTH required)
  5.3 - LWP exceeding 30 days requires Municipal Commissioner approval
  7.2 - Leave encashment during service not permitted under any circumstances

CONTEXT:
You are given the full text of policy_hr_leave.txt. You must only use
information present in this document. You must not add phrases such as
"as is standard practice", "typically in government organisations",
or "employees are generally expected to".

ENFORCEMENT RULES:
1. Every numbered clause in the source document must appear in the summary.
2. Multi-condition obligations must preserve ALL conditions.
3. Never add information not present in the source document.
4. If a clause cannot be summarised without meaning loss — quote it verbatim
   and mark it as [DIRECT QUOTE - not summarised].
5. Clause 5.2: The summary MUST name BOTH the Department Head AND the HR Director.
   Dropping either approver is a condition-drop failure.
6. Clause 7.2: Must state "not permitted under any circumstances". Softening to
   "generally not permitted" or "rarely allowed" is a failure.
7. Clause 2.6: Must include both the 5-day cap AND the 31 December forfeiture date.
8. Clause 2.7: Must include both the January-March usage window AND the forfeiture consequence.

OUTPUT FORMAT:
Produce a structured plain-text summary with section headers matching the source
document's numbering. Each clause summary must begin with its clause number.
Example:
  2.3 Annual Leave Notice: Employees must submit leave requests at least 14 days in advance.
"""


# ---------------------------------------------------------------------------
# Skill 1: retrieve_policy
# ---------------------------------------------------------------------------

def retrieve_policy(file_path: str) -> list[dict]:
    """
    Skill: retrieve_policy
    Loads a .txt policy file and returns content as structured numbered sections.

    Input  : file path string to .txt policy document
    Output : list of dicts with keys — section_number, title, text
    Errors : FileNotFoundError halts execution; unparseable blocks included as-is
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] Policy file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    if not raw.strip():
        print(f"[ERROR] Policy file is empty: {file_path}", file=sys.stderr)
        sys.exit(1)

    sections = []
    # Match numbered sections like "2.3", "5.2", "7.2" etc.
    pattern = re.compile(r"(?m)^(\d+\.\d+)\s+(.*?)(?=^\d+\.\d+|\Z)", re.DOTALL)
    matches = list(pattern.finditer(raw))

    if not matches:
        # Fallback: return the whole document as one block
        print("[WARN] Could not parse numbered sections. Treating document as single block.",
              file=sys.stderr)
        sections.append({
            "section_number": "FULL",
            "title": "Full Document",
            "text": raw.strip(),
            "flag": "UNPARSED",
        })
        return sections

    for match in matches:
        section_number = match.group(1).strip()
        body = match.group(2).strip()
        # Split first line as title if it looks like a heading
        lines = body.splitlines()
        title = lines[0].strip() if lines else ""
        text = "\n".join(lines[1:]).strip() if len(lines) > 1 else title

        sections.append({
            "section_number": section_number,
            "title": title,
            "text": text if text else title,
            "flag": "",
        })

    print(f"[INFO] Retrieved {len(sections)} sections from '{file_path}'.")
    return sections


# ---------------------------------------------------------------------------
# Skill 2: summarize_policy
# ---------------------------------------------------------------------------

def summarize_policy(sections: list[dict], output_path: str) -> str:
    """
    Skill: summarize_policy
    Takes structured sections and produces a clause-accurate compliant summary.

    Input  : list of section dicts from retrieve_policy
    Output : plain-text summary written to output_path
    Errors : clauses that risk meaning loss are quoted verbatim and flagged
    """
    full_text = "\n\n".join(
        f"{s['section_number']} {s['title']}\n{s['text']}" for s in sections
    )

    # --- Attempt LLM summarization ---
    summary = None
    if genai is not None:
        summary = _summarize_with_llm(full_text)

    # --- Fallback: rule-based summary ---
    if summary is None:
        summary = _rule_based_summary(sections)

    # --- Post-processing enforcement ---
    summary = _enforce_output(summary, sections)

    # --- Write output ---
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"[INFO] Summary written to '{output_path}'.")
    return summary


def _summarize_with_llm(full_text: str) -> str | None:
    """Call Gemini to summarize the policy text using the RICE system prompt."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("[WARN] GOOGLE_API_KEY not set. Falling back to rule-based summarizer.",
              file=sys.stderr)
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            f"Summarize the following HR leave policy document:\n\n{full_text}"
        )
        return response.text.strip()

    except Exception as e:
        print(f"[WARN] LLM call failed: {e}. Falling back to rule-based.", file=sys.stderr)
        return None


def _rule_based_summary(sections: list[dict]) -> str:
    """
    Deterministic fallback: builds summary by directly rendering each clause.
    Quotes high-risk clauses verbatim and flags them.
    """
    lines = ["HR LEAVE POLICY — SUMMARY", "=" * 40, ""]

    for section in sections:
        num = section["section_number"]
        title = section["title"]
        text = section["text"]

        if num in HIGH_RISK_CLAUSES:
            # Quote high-risk clauses verbatim to avoid meaning loss
            lines.append(f"{num} {title}")
            lines.append(f"  {text}")
            lines.append(f"  [DIRECT QUOTE - not summarised: high-risk clause]")
        else:
            lines.append(f"{num} {title}")
            lines.append(f"  {text}")
        lines.append("")

    return "\n".join(lines)


def _enforce_output(summary: str, sections: list[dict]) -> str:
    """
    Post-processing RICE enforcement guard:
    1. Check all 10 high-risk clauses are mentioned in output.
    2. Detect and flag forbidden scope-bleed phrases.
    3. Detect obligation softening.
    """
    warnings = []

    # Rule 1: Every high-risk clause must appear in the summary
    missing_clauses = []
    for clause_num, description in HIGH_RISK_CLAUSES.items():
        if clause_num not in summary:
            missing_clauses.append(f"  - Clause {clause_num}: {description}")

    if missing_clauses:
        warnings.append("[ENFORCEMENT WARNING] The following high-risk clauses are MISSING from the summary:")
        warnings.extend(missing_clauses)

    # Rule 2: Check for forbidden scope-bleed phrases
    summary_lower = summary.lower()
    found_forbidden = [p for p in FORBIDDEN_PHRASES if p in summary_lower]
    if found_forbidden:
        warnings.append("[ENFORCEMENT WARNING] Forbidden scope-bleed phrases detected:")
        for phrase in found_forbidden:
            warnings.append(f"  - \"{phrase}\"")

    # Rule 3: Check for obligation softening in high-risk clause text
    for clause_num in HIGH_RISK_CLAUSES:
        # Find the clause block in the summary
        idx = summary.find(clause_num)
        if idx != -1:
            snippet = summary[idx:idx+300].lower()
            for soft_word in SOFTENING_MAP:
                if soft_word in snippet:
                    warnings.append(
                        f"[ENFORCEMENT WARNING] Possible obligation softening in clause {clause_num}: "
                        f"found '{soft_word}'"
                    )

    # Append warnings to summary if any
    if warnings:
        summary += "\n\n" + "\n".join(warnings)
        print("\n".join(warnings), file=sys.stderr)
    else:
        print("[INFO] Enforcement check passed — all 10 high-risk clauses present, no scope bleed detected.")

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UC-0B Policy Summarizer — built from agents.md + skills.md"
    )
    parser.add_argument("--input",  required=True,
                        help="Path to policy_hr_leave.txt")
    parser.add_argument("--output", required=True,
                        help="Path to write summary_hr_leave.txt")
    args = parser.parse_args()

    # Skill 1: retrieve_policy
    sections = retrieve_policy(args.input)

    # Skill 2: summarize_policy
    summarize_policy(sections, args.output)

    print(f"Done. Summary written to {args.output}")


if __name__ == "__main__":
    main()
