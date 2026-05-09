"""
UC-0B app.py — Policy summarizer.
Reads a .txt policy file and writes a clause-faithful summary.

Run:
    python app.py --input ../data/policy-documents/policy_hr_leave.txt --output summary_hr_leave.txt
"""
import argparse
import os
import re
import sys

REQUIRED_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

SYSTEM_PROMPT = """You are an HR leave policy summarization agent.

Your role: Produce a clause-faithful summary of the provided policy document.
Operational boundary: You may only use content from the source document — no external knowledge, no additions.

Rules you must follow:
1. Every numbered clause must appear in the summary: 2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2. No clause may be silently omitted.
2. Multi-condition obligations must preserve ALL conditions. Clause 5.2 requires approval from BOTH Department Head AND HR Director — dropping either approver is a condition drop, not a simplification. Clause 2.6 has two sub-conditions (5-day cap AND forfeiture on 31 Dec) — both must appear.
3. Never add information not present in the source document. Do not use phrases like "as is standard practice", "typically in government organisations", or "employees are generally expected to".
4. If a clause cannot be summarised without meaning loss (e.g. dual-approver conditions, precise date thresholds, absolute prohibitions), quote the clause verbatim and mark it [VERBATIM].

Output format: One labelled entry per clause.
Example: "Clause 2.3: Employees must provide 14 days advance notice before taking leave."
"""


# --- skill: retrieve_policy ---

def retrieve_policy(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    if not raw_text.strip():
        raise ValueError("Policy file is empty")

    sections = []
    for match in re.finditer(r"(\d+\.\d+)\b(.+?)(?=\n\s*\d+\.\d+|\Z)", raw_text, re.DOTALL):
        sections.append({
            "clause_number": match.group(1),
            "clause_text": match.group(2).strip(),
        })

    return {"raw_text": raw_text, "sections": sections}


# --- skill: summarize_policy ---

def summarize_policy(policy: dict, client) -> str:
    if not policy.get("raw_text", "").strip() or not policy.get("sections"):
        raise ValueError("No policy content to summarise")

    user_message = f"Summarise the following HR leave policy document:\n\n{policy['raw_text']}"
    summary = _call_claude(client, user_message)

    missing = _missing_clauses(summary)
    if missing:
        retry_message = (
            f"{user_message}\n\n"
            f"IMPORTANT: Your previous summary was missing these required clauses: "
            f"{', '.join(missing)}. You must include all of them in the output."
        )
        summary = _call_claude(client, retry_message)
        missing = _missing_clauses(summary)
        if missing:
            raise RuntimeError(
                f"Summary still missing required clauses after retry: {', '.join(missing)}"
            )

    return summary


def _call_claude(client, user_message: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def _missing_clauses(summary: str) -> list:
    return [c for c in REQUIRED_CLAUSES if c not in summary]


# --- main ---

def main():
    parser = argparse.ArgumentParser(description="UC-0B: Clause-faithful policy summarizer")
    parser.add_argument("--input", required=True, help="Path to policy .txt file")
    parser.add_argument("--output", required=True, help="Path for output summary file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Load and parse the policy file only — no API call")
    args = parser.parse_args()

    policy = retrieve_policy(args.input)
    print(f"Loaded {len(policy['sections'])} sections from {args.input}", file=sys.stderr)

    no_key = not os.environ.get("ANTHROPIC_API_KEY")
    if args.dry_run or no_key:
        if no_key and not args.dry_run:
            print("No ANTHROPIC_API_KEY set.", file=sys.stderr)
        print("\n sections parsed ---")
        for s in policy["sections"]:
            print(f"  Clause {s['clause_number']}: {s['clause_text'][:80]}...")
        print("\n system prompt that would be sent ---")
        print(SYSTEM_PROMPT)
        dry_run_output = "\n Sections parsed:\n"
        for s in policy["sections"]:
            dry_run_output += f"  Clause {s['clause_number']}: {s['clause_text'][:80]}...\n"
        dry_run_output += "\nSystem prompt that would be sent:\n" + SYSTEM_PROMPT
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(dry_run_output)
        print(f"Dry-run output written to {args.output}")
        return

    import anthropic
    client = anthropic.Anthropic()
    summary = summarize_policy(policy, client)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
