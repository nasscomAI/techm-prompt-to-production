"""
UC-0B — Policy Summary Generator
Enforces clause preservation, multi-condition integrity, no scope bleed.
"""
import argparse
import re
from pathlib import Path

# Critical clauses that MUST appear in summary
CRITICAL_CLAUSES = [
    ("2.3", "14-day advance notice"),
    ("2.4", "written approval"),
    ("2.5", "unapproved absence = LOP"),
    ("2.6", "max 5 days carry-forward"),
    ("2.7", "carry-forward jan-mar"),
    ("3.2", "3+ sick days certificate 48hrs"),
    ("3.4", "sick before/after holiday certificate"),
    ("5.2", "LWP both department head and hr director"),
    ("5.3", "LWP >30 days municipal commissioner"),
    ("7.2", "leave encashment during service not permitted"),
]

def retrieve_policy(input_path: str) -> dict:
    """
    Load policy file and parse into structured sections.
    Returns: dict with section names as keys, list of (clause_num, clause_text) as values
    """
    policy_file = Path(input_path)
    if not policy_file.exists():
        raise FileNotFoundError(f"Policy file not found: {input_path}")
    
    with open(policy_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if not content.strip():
        raise ValueError(f"Policy file is empty: {input_path}")
    
    sections = {}
    current_section = None
    current_clauses = []
    
    for line in content.split("\n"):
        # Detect section headers (lines with ═)
        if "═" in line:
            if current_section and current_clauses:
                sections[current_section] = current_clauses
            current_section = None
            current_clauses = []
        # Detect section title (after ═)
        elif current_section is None and line.strip() and not "═" in line:
            if re.match(r"^\d+\.", line.strip()):
                current_section = line.strip()
                current_clauses = []
        # Detect clause numbers (N.M format)
        elif current_section and re.match(r"^\d+\.\d+", line.strip()):
            clause_match = re.match(r"(\d+\.\d+)(.*)", line.strip())
            if clause_match:
                clause_num = clause_match.group(1)
                clause_text = clause_match.group(2).strip()
                current_clauses.append((clause_num, clause_text))
    
    # Add last section
    if current_section and current_clauses:
        sections[current_section] = current_clauses
    
    return sections


def check_multi_conditions(clause_text: str) -> bool:
    """
    Check if a clause contains multi-part conditions (e.g., 'and')
    """
    return " and " in clause_text.lower()


def summarize_policy(sections: dict) -> str:
    """
    Generate summary preserving all clauses and conditions.
    Returns: summary text with clause references and flags
    """
    summary_lines = [
        "=" * 60,
        "POLICY SUMMARY — HR LEAVE POLICY",
        "Document Reference: HR-POL-001",
        "=" * 60,
        "",
    ]
    
    found_clauses = set()
    flags = []
    
    # Iterate through sections and clauses, preserving order
    for section_name, clauses in sections.items():
        if section_name:
            summary_lines.append(f"\n{section_name}")
            summary_lines.append("-" * len(section_name))
        
        for clause_num, clause_text in clauses:
            found_clauses.add(clause_num)
            
            # Check for multi-condition obligations
            if check_multi_conditions(clause_text):
                # Flag potential condition-drop risk
                flags.append(f"[CHECK] Clause {clause_num}: Contains 'and' condition — verify all parts preserved.")
            
            # Format clause for summary
            summary_lines.append(f"  [{clause_num}] {clause_text}")
    
    # Check for missing critical clauses
    summary_lines.append("\n" + "=" * 60)
    summary_lines.append("CRITICAL CLAUSE VALIDATION")
    summary_lines.append("=" * 60)
    
    missing_clauses = []
    for clause_num, description in CRITICAL_CLAUSES:
        if clause_num in found_clauses:
            summary_lines.append(f"  ✓ {clause_num}: FOUND")
        else:
            summary_lines.append(f"  ✗ {clause_num}: MISSING")
            missing_clauses.append(clause_num)
            flags.append(f"[FLAG] CRITICAL CLAUSE {clause_num} NOT FOUND IN SOURCE")
    
    # Add flags
    if flags:
        summary_lines.append("\n" + "=" * 60)
        summary_lines.append("REVIEW FLAGS")
        summary_lines.append("=" * 60)
        for flag in flags:
            summary_lines.append(f"  {flag}")
    
    return "\n".join(summary_lines)


def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summary Generator")
    parser.add_argument("--input", required=True, help="Path to policy_hr_leave.txt")
    parser.add_argument("--output", required=True, help="Path to write summary_hr_leave.txt")
    args = parser.parse_args()
    
    try:
        # Retrieve and parse policy
        sections = retrieve_policy(args.input)
        
        # Generate summary
        summary = summarize_policy(sections)
        
        # Write output
        output_file = Path(args.output)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary)
        
        print(f"Summary written to {args.output}")
        print(f"\n{summary}")
    
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=__import__("sys").stderr)
        exit(1)


if __name__ == "__main__":
    main()
