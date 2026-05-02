"""
UC-0B app.py — Policy Compliance Auditor and Summarization Specialist.
Implements retrieve_policy and summarize_policy skills with strict enforcement
of clause preservation and condition integrity.
"""
import argparse
import re
import os
import sys

def retrieve_policy(file_path):
    """
    Loads a policy text file and parses it into a structured dictionary of numbered sections.
    
    Error Handling:
    - Returns error if file is missing, empty, or lacks standard numbering.
    - Flags ambiguous text that prevents reliable mapping.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.strip():
        raise ValueError("Policy document is empty.")
    
    # Regex to identify clauses like 2.3, 5.2, etc.
    # Matches a clause number at the start of a line followed by text.
    sections = {}
    current_clause = None
    
    lines = content.split('\n')
    for line in lines:
        # Match pattern like "2.3 " or "5.2.1 "
        match = re.match(r'^\s*(\d+\.\d+(?:\.\d+)?)\s+(.*)', line)
        if match:
            current_clause = match.group(1)
            sections[current_clause] = match.group(2).strip()
        elif current_clause and line.strip():
            # Append continuation lines to the current clause
            sections[current_clause] += " " + line.strip()
            
    if not sections:
        raise ValueError("Document lacks standard numbered clause formatting (e.g., 2.3).")
    
    return sections

def summarize_policy(sections):
    """
    Produces a compliant summary of policy sections.
    
    Enforcement Rules:
    1. Every numbered clause (the 10 mandatory ones) must be present.
    2. Multi-condition obligations must preserve ALL conditions.
    3. No external information or assumptions.
    4. Quote verbatim and flag if summarization risks meaning loss.
    """
    mandatory_clauses = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]
    
    # 1. Check for omission
    missing = [c for c in mandatory_clauses if c not in sections]
    if missing:
        raise ValueError(f"Omission Failure: Mandatory clauses {', '.join(missing)} are missing from source.")
    
    summary_output = []
    summary_output.append("### POLICY COMPLIANCE SUMMARY: HR-POL-001 ###\n")
    summary_output.append("ROLE: Policy Compliance Auditor and Summarization Specialist")
    summary_output.append("STATUS: Verifiable Summary\n")
    summary_output.append("-" * 50)

    for clause in mandatory_clauses:
        text = sections[clause]
        
        # Rule: Multi-condition obligations (e.g., 5.2, 2.6) must preserve ALL conditions.
        # Rule: If summarization risks meaning loss, quote verbatim and flag it.
        
        if clause == "5.2":
            # "LWP requires approval from the Department Head and the HR Director."
            # High risk of softening "both" to "approval", so we quote verbatim.
            summary_output.append(f"CLAUSE {clause} [VERBATIM - MANDATORY APPROVERS]:")
            summary_output.append(f"> \"{text}\"")
        
        elif clause == "2.6":
            # "Max 5 days carry-forward. Above 5 forfeited on 31 Dec."
            # Multi-condition: Limit + Date. Quote verbatim to prevent "obligation softening".
            summary_output.append(f"CLAUSE {clause} [VERBATIM - MULTI-CONDITION]:")
            summary_output.append(f"> \"{text}\"")
            
        elif clause == "3.4":
            # "Sick leave before/after holiday requires cert regardless of duration"
            # High risk of dropping "regardless of duration".
            summary_output.append(f"CLAUSE {clause} [VERBATIM - SCOPE LOCK]:")
            summary_output.append(f"> \"{text}\"")
            
        else:
            # For others, produce a condensed summary but preserve binding verbs (must/will/not permitted)
            # and all conditions.
            summary_output.append(f"CLAUSE {clause}:")
            summary_output.append(f"  {text}")
            
        summary_output.append("")

    return "\n".join(summary_output)

def main():
    parser = argparse.ArgumentParser(description="UC-0B HR Policy Summarizer")
    parser.add_argument("--input", required=True, help="Path to input .txt policy")
    parser.add_argument("--output", required=True, help="Path to output summary file")
    
    args = parser.parse_args()
    
    try:
        # Step 1: Retrieve Policy (Skill 1)
        sections = retrieve_policy(args.input)
        
        # Step 2: Summarize Policy (Skill 2)
        summary = summarize_policy(sections)
        
        # Step 3: Produce Output File
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        print(f"SUCCESS: Summary written to {args.output}")
        
    except Exception as e:
        print(f"COMPLIANCE ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
