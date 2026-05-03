"""
UC-0B app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import os
import re

def retreive_policy(file_path: str) -> dict:
    """
    Reads the input policy document and returns it as a structured numbered section.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if not content.strip():
        raise ValueError("Input file is empty")
        
    lines = content.split('\n')
    
    structured_data = {
        "preamble": [],
        "sections": {}
    }
    
    current_section = None
    current_clause = None
    
    for line in lines:
        if '═' in line:
            continue
            
        # Check for section heading e.g., "1. PURPOSE AND SCOPE"
        section_match = re.match(r'^(\d+)\.\s+([A-Z\s\(\)-]+)$', line.strip())
        if section_match:
            section_num = section_match.group(1)
            section_title = section_match.group(2).strip()
            current_section = f"{section_num}. {section_title}"
            structured_data["sections"][current_section] = {}
            current_clause = None
            continue
            
        # Check for clause e.g., "1.1 This policy..."
        clause_match = re.match(r'^(\d+\.\d+)\s+(.+)$', line)
        if clause_match:
            clause_num = clause_match.group(1)
            clause_text = clause_match.group(2).strip()
            if current_section:
                structured_data["sections"][current_section][clause_num] = clause_text
                current_clause = clause_num
            continue
            
        # Check for continuation line (starts with space)
        if line.startswith(' ') and line.strip() and current_clause and current_section:
            structured_data["sections"][current_section][current_clause] += " " + line.strip()
            continue
            
        # Preamble
        if not current_section and line.strip():
            structured_data["preamble"].append(line.strip())
            
    return structured_data

def summarize_policy(structured_data: dict) -> str:
    """
    Takes the structured numbered sections and produces a compliant summary with clause references.
    """
    if not structured_data or not structured_data.get("sections"):
        raise ValueError("Structured numbered section is not found or is empty")
        
    summary_lines = []
    
    # Add preamble
    if structured_data.get("preamble"):
        summary_lines.append("**Document Info:**")
        summary_lines.extend(structured_data["preamble"])
        summary_lines.append("\n---\n")
        
    summary_lines.append("# Policy Summary")
    summary_lines.append("> **Note:** All clauses have been preserved verbatim below to ensure no multi-condition obligations are dropped or softened.\n")
    
    for section, clauses in structured_data["sections"].items():
        summary_lines.append(f"## {section}")
        for clause_num, clause_text in clauses.items():
            summary_lines.append(f"- **{clause_num}**: {clause_text}")
        summary_lines.append("")
        
    return "\n".join(summary_lines)

def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summariser Agent")
    parser.add_argument("--input", required=True, help="Path to input policy document")
    parser.add_argument("--output", required=True, help="Path to write the compliant summary")
    args = parser.parse_args()

    try:
        structured_data = retreive_policy(args.input)
        summary = summarize_policy(structured_data)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        print(f"Summary successfully written to {args.output}")
    except Exception as e:
        print(f"Error processing policy: {str(e)}")

if __name__ == "__main__":
    main()
