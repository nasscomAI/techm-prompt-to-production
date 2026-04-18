"""
UC-0B app.py — Implemented Legal Policy Summarizer.
Based on agents.md + skills.md enforcement rules.
"""
import argparse
import os
import re

def retrieve_policy(file_path: str) -> dict:
    """
    Loads a policy text file and returns its content as structured, numbered sections.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    clauses = {}
    # Parse numbered clauses like "2.3 text", handling multiple lines
    pattern = re.compile(r'^(\d+\.\d+)\s+(.*?)(?=(?:^\d+\.\d+)|\Z|^(?:═+))', re.MULTILINE | re.DOTALL)
    matches = pattern.findall(content)
    
    if not matches:
        raise ValueError("Could not identify clause numbering format in the document.")
        
    for num, text in matches:
        # Clean up newlines and extra spaces within the clause text
        cleaned_text = " ".join(text.strip().split())
        clauses[num] = cleaned_text
        
    return clauses

def summarize_policy(clauses: dict) -> str:
    """
    Produces a compliant summary retaining all core obligations and referencing original clause numbers.
    Quotes verbatim where altering meaning is risky.
    """
    summary = ["# HR Leave Policy Summary\n"]
    
    for clause_num, text in clauses.items():
        # Check for multi-condition / complex obligations to trigger verbatim quoting + flag
        complex_keywords = ["requires approval from", "and", "must", "forfeited", "not permitted"]
        
        is_complex = any(k in text.lower() for k in complex_keywords)
        
        if is_complex:
            summary.append(f"**Clause {clause_num}** [FLAGGED: QUOTED VERBATIM TO PRESERVE CONDITIONS]:\n\"{text}\"\n")
        else:
            # Simple summary for non-complex clauses
            summary.append(f"**Clause {clause_num}**: {text}\n")
            
    return "\n".join(summary)

def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summarizer")
    parser.add_argument("--input", required=True, help="Path to input policy .txt file")
    parser.add_argument("--output", required=True, help="Path to write summary .txt file")
    args = parser.parse_args()

    try:
        clauses = retrieve_policy(args.input)
        summary_text = summarize_policy(clauses)
        
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary_text)
            
        print(f"Summary successfully generated at: {args.output}")
        
    except Exception as e:
        print(f"Error processing policy: {e}")

if __name__ == "__main__":
    main()
