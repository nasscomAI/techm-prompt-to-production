"""
UC-0B app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import re

def retrieve_policy(filepath: str) -> dict:
    """
    Load a .txt policy file and return its content parsed into structured numbered sections.
    """
    sections = {}
    current_clause = None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip decorative lines, pure uppercase headers, and metadata
                if not line or line.startswith('═') or line.isupper() or line.startswith('Document') or line.startswith('Version'):
                    continue
                
                # Match clause numbers like "1.1", "2.3", etc.
                m = re.match(r'^(\d+\.\d+)\s+(.*)', line)
                if m:
                    current_clause = m.group(1)
                    sections[current_clause] = m.group(2)
                elif current_clause:
                    sections[current_clause] += " " + line
        return sections
    except Exception as e:
        raise RuntimeError(f"Failed to parse policy file: {e}")

def summarize_policy(sections: dict) -> str:
    """
    Take structured sections and produce a compliant summary with clause references.
    If a clause cannot be summarized without losing meaning or dropping conditions, quote verbatim and flag it.
    """
    summary = ["# HR Leave Policy Summary\n"]
    
    for clause, text in sections.items():
        # Check for complex multi-condition or critical obligations to flag and quote verbatim
        if "and the" in text or "must" in text or "requires" in text or "not permitted" in text:
            summary.append(f"- **Clause {clause}** [VERBATIM - HIGH RISK OF MEANING LOSS]: \"{text}\"")
        else:
            # For simpler clauses, provide a clean text representation
            summary.append(f"- **Clause {clause}**: {text}")
            
    return "\n".join(summary)

def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summarizer")
    parser.add_argument("--input", required=True, help="Path to policy txt file")
    parser.add_argument("--output", required=True, help="Path to output summary txt file")
    args = parser.parse_args()
    
    try:
        sections = retrieve_policy(args.input)
        summary = summarize_policy(sections)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        print(f"Done. Compliant summary written to {args.output}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
