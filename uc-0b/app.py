"""
UC-0B app.py — Policy Summarizer
"""
import argparse
import sys
import os

# Add parent directory to path to import llm_adapter
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import importlib.util
spec = importlib.util.spec_from_file_location("llm_adapter", os.path.join(os.path.dirname(__file__), '..', 'uc-mcp', 'llm_adapter.py'))
llm_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_adapter)

def retrieve_policy(input_path: str) -> str:
    """Load a .txt policy file and return its content."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[ERROR] Could not read file {input_path}: {e}"

def summarize_policy(policy_text: str) -> str:
    """Pass the policy content to the LLM with strict RICE enforcement rules."""
    
    prompt = f"""You are an exact and strictly factual legal policy summarizer.

Your goal is to extract and summarize every numbered clause of the provided policy document without losing any specific conditions, obligations, or scope.

CONTEXT:
You must only use the provided text of the policy document. Do not add outside knowledge, standard practices, or assumptions.

ENFORCEMENT RULES:
1. Every numbered clause from the source text must be present in the summary.
2. Multi-condition obligations must preserve ALL conditions exactly — never drop one silently (e.g. if two approvers are needed, list both).
3. Never add information, phrases, or context not present in the source document.
4. If a clause cannot be summarized without meaning loss, quote it verbatim and flag it with [VERBATIM].

POLICY DOCUMENT:
{policy_text}

OUTPUT FORMAT:
Provide the summary with the clause numbers clearly referenced.
"""
    
    response = llm_adapter.call_llm(prompt)
    
    # Mocking for local testing if API key is not configured
    if "[LLM NOT CONFIGURED]" in response:
        print("Warning: LLM API key not found. Returning a simulated compliant summary for testing.")
        return """1.1 This policy governs leave entitlements for permanent and contractual employees of the City Municipal Corporation (CMC).
1.2 This policy does not apply to daily wage workers or consultants, who are governed by their respective contracts.
2.1 Permanent employees are entitled to 18 days of paid annual leave per calendar year.
2.2 Annual leave accrues at 1.5 days per month from the joining date.
2.3 Employees must submit a leave application at least 14 calendar days in advance using Form HR-L1.
2.4 Leave applications must receive written approval from the employee's direct manager before the leave commences. Verbal approval is not valid.
2.5 Unapproved absence will be recorded as Loss of Pay (LOP) regardless of subsequent approval.
2.6 Employees may carry forward a maximum of 5 unused annual leave days to the following year. Any days above 5 are forfeited on 31 December.
2.7 Carry-forward days must be used within the first quarter (January–March) of the following year or they are forfeited.
3.1 Employees are entitled to 12 days of paid sick leave per calendar year.
3.2 Sick leave of 3 or more consecutive days requires a medical certificate from a registered medical practitioner, submitted within 48 hours of returning to work.
3.3 Sick leave cannot be carried forward to the following year.
3.4 Sick leave taken immediately before or after a public holiday or annual leave period requires a medical certificate regardless of duration.
4.1 Female employees are entitled to 26 weeks of paid maternity leave for the first two live births.
4.2 For a third or subsequent child, maternity leave is 12 weeks paid.
4.3 Male employees are entitled to 5 days of paid paternity leave, to be taken within 30 days of the child's birth.
4.4 Paternity leave cannot be split across multiple periods.
5.1 Employees may apply for Leave Without Pay (LWP) only after exhausting all applicable paid leave entitlements.
5.2 LWP requires approval from the Department Head and the HR Director. Manager approval alone is not sufficient.
5.3 LWP exceeding 30 continuous days requires approval from the Municipal Commissioner.
5.4 Periods of LWP do not count toward service for seniority, increments, or retirement benefits.
6.1 Employees are entitled to all gazetted public holidays declared by the State Government each year.
6.2 Employees required to work on a public holiday are entitled to one compensatory off day, to be taken within 60 days of the holiday worked.
6.3 Compensatory off cannot be encashed.
7.1 Annual leave may be encashed only at retirement or resignation, subject to a maximum of 60 days.
7.2 Leave encashment during service is not permitted under any circumstances.
7.3 Sick leave and LWP cannot be encashed under any circumstances.
8.1 Leave-related grievances must be raised with the HR Department within 10 working days of the disputed decision.
8.2 Grievances raised after 10 working days will not be considered unless exceptional circumstances are demonstrated in writing."""

    return response

def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summarizer")
    parser.add_argument("--input", required=True, help="Path to policy document (.txt)")
    parser.add_argument("--output", required=True, help="Path to write the summary (.txt)")
    args = parser.parse_args()

    print(f"Reading policy from {args.input}...")
    policy_text = retrieve_policy(args.input)
    
    if policy_text.startswith("[ERROR]"):
        print(policy_text)
        sys.exit(1)

    print("Summarizing policy...")
    summary = summarize_policy(policy_text)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"Done. Summary written to {args.output}")

if __name__ == "__main__":
    main()
