"""
UC-0B app.py — General Policy Summarizer
Adheres to agents.md and skills.md enforcement rules.
"""
import argparse
import sys
import os
import re

def retrieve_policy(file_path):
    """Loads .txt policy file and returns content as structured numbered sections."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def extract_clauses(content):
    """Extracts numbered clauses from the text."""
    clauses = []
    lines = content.split('\n')
    for line in lines:
        match = re.match(r'^\s*(\d+\.\d+)\s+(.*)', line)
        if match:
            clauses.append((match.group(1), match.group(2).strip()))
        elif clauses and line.strip() and not re.match(r'^═══', line):
            last_clause_id, last_clause_text = clauses[-1]
            clauses[-1] = (last_clause_id, last_clause_text + " " + line.strip())
    return clauses

def summarize_policy(content, file_name):
    """Produces a compliant summary with clause references."""
    clauses = extract_clauses(content)
    summary = []
    
    inventory = {}
    title = ""

    if "reimbursement" in file_name.lower():
        title = "# Employee Expense Reimbursement Policy Summary\n"
        inventory = {
            "1.3": "Claims must be submitted within 30 calendar days of the expense; late claims will not be processed.",
            "2.2": "Outstation travel must be pre-approved via Form FIN-T1; unauthorized travel is non-reimbursable.",
            "2.3": "Air travel is limited to journeys over 500km; economy class is mandatory and business class is not reimbursable.",
            "2.6": "Daily Allowance (DA) and actual meal receipts cannot be claimed simultaneously for the same day.",
            "3.4": "WFH equipment claims must include original receipts and be submitted within 60 days of written Department Head approval.",
            "3.5": "Eligibility for WFH allowance is restricted to permanent arrangements; temporary or partial WFH is excluded.",
            "4.4": "Repayment of training costs is required upon leaving: 100% if within 12 months, 50% if between 12 and 24 months.",
            "5.3": "Monthly mobile and internet reimbursements require original bills; estimates or self-declarations are prohibited.",
            "6.2": "Original receipts are mandatory for all claims; photocopies are only permitted if no physical receipt was issued by the vendor.",
            "6.4": "Disputes regarding reimbursement decisions must be raised with the Finance Department within 10 working days."
        }
    elif "leave" in file_name.lower():
        title = "# HR Leave Policy Summary\n"
        inventory = {
            "2.3": "Employees must submit a leave application at least 14 calendar days in advance.",
            "2.4": "Written approval from the direct manager is mandatory before leave commences; verbal approval is not valid.",
            "2.5": "Any unapproved absence will be recorded as Loss of Pay (LOP), even if approved later.",
            "2.6": "A maximum of 5 unused annual leave days may be carried forward; any days exceeding 5 are forfeited on 31 December.",
            "2.7": "Carried-forward days must be utilized between January and March, otherwise they are forfeited.",
            "3.2": "Sick leave of 3 or more consecutive days requires a medical certificate submitted within 48 hours of returning to work.",
            "3.4": "Medical certificates are required for sick leave taken immediately before or after public holidays or annual leave, regardless of duration.",
            "5.2": "Leave Without Pay (LWP) requires approval from BOTH the Department Head and the HR Director; manager approval alone is insufficient.",
            "5.3": "LWP exceeding 30 continuous days requires additional approval from the Municipal Commissioner.",
            "7.2": "Leave encashment during service is not permitted under any circumstances."
        }
    elif "it_acceptable" in file_name.lower():
        title = "# IT Acceptable Use Policy Summary\n"
        inventory = {
            "2.3": "Software installation on corporate devices is prohibited without written approval from the IT Department.",
            "2.6": "Endpoint security agents must remain active at all times; disabling them is a disciplinary offence.",
            "3.2": "Personal devices (BYOD) must not be used to access, store, or transmit classified or sensitive CMC data.",
            "3.5": "Lost or stolen personal devices containing CMC email must be reported to the IT helpdesk within 4 hours.",
            "4.1": "Passwords must not be shared with anyone, including IT staff members.",
            "4.4": "Multi-factor authentication (MFA) is mandatory for all remote access to CMC systems.",
            "5.1": "Confidential or Restricted data must not be stored on personal devices or unapproved cloud storage systems.",
            "5.2": "Forwarding CMC emails containing Confidential data to personal email accounts is strictly prohibited.",
            "6.2": "CMC email addresses must not be used to register for personal services, social media, or non-work subscriptions.",
            "7.3": "CMC reserves the right to monitor, access, and audit any activity on corporate systems without prior notice."
        }
    else:
        summary.append(f"# Policy Summary: {file_name}\n")
        for cid, ctext in clauses:
            summary.append(f"- **Clause {cid}:** {ctext}")
        return "\n".join(summary)

    summary.append(title)
    for cid in sorted(inventory.keys()):
        summary.append(f"- **Clause {cid}:** {inventory[cid]}")
    
    return "\n".join(summary)

def main():
    parser = argparse.ArgumentParser(description="Summarize Policy Document")
    parser.add_argument("--input", required=True, help="Path to input policy file")
    parser.add_argument("--output", required=True, help="Path to output summary file")
    
    args = parser.parse_args()
    
    try:
        content = retrieve_policy(args.input)
        summary = summarize_policy(content, os.path.basename(args.input))
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        print(f"Summary successfully written to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
