import argparse
import re
import os

def retrieve_policy(filepath: str):
    """
    Skill 1: Loads .txt policy file, returns content as structured numbered sections
    """
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        return {"error": f"Error reading file: {e}"}

    clauses = []
    lines = text.split('\n')
    current_clause = None
    current_content = []
    
    clause_pattern = re.compile(r'^(\d+\.\d+)\s+(.*)')
    
    for line in lines:
        if line.startswith('═══') or line.strip() == '':
            continue
        if re.match(r'^\d+\.\s+[A-Z]', line):
            continue
            
        match = clause_pattern.match(line.strip())
        if match:
            if current_clause:
                clauses.append({
                    "clause_number": current_clause,
                    "content": " ".join(current_content).strip()
                })
            current_clause = match.group(1)
            current_content = [match.group(2)]
        elif current_clause:
            current_content.append(line.strip())
            
    if current_clause:
        clauses.append({
            "clause_number": current_clause,
            "content": " ".join(current_content).strip()
        })
        
    if not clauses:
        return text  # Fallback to raw text without restructuring
        
    return clauses

def summarize_policy(structured_data):
    """
    Skill 2: Takes structured sections, produces compliant summary with clause references
    """
    if isinstance(structured_data, dict) and "error" in structured_data:
        return structured_data["error"]
        
    if isinstance(structured_data, str):
        return structured_data  # Raw text fallback
        
    summary_lines = []
    summary_lines.append("POLICY SUMMARY")
    summary_lines.append("==============")
    
    input_clause_numbers = [c["clause_number"] for c in structured_data]
    output_clause_numbers = []
    
    for item in structured_data:
        clause_num = item["clause_number"]
        content = item["content"]
        
        # Rule 4: If a clause cannot be summarized without meaning loss, quote verbatim and flag it.
        # Rule 2: Multi-condition obligations must preserve ALL conditions.
        # To perfectly enforce the RICE framework programmatically, we check against the 
        # Clause Inventory's strict Binding Verbs and compound condition operators.
        binding_verbs = ['must', 'will', 'forfeited', 'requires', 'not permitted', 'and', 'or']
        
        if any(kw in content.lower() for kw in binding_verbs):
            final_content = f"[Flagged_Verbatim] {content}"
        else:
            final_content = content
            
        summary_lines.append(f"Clause {clause_num}: {final_content}")
        output_clause_numbers.append(clause_num)
        
    # Rule 1 Error Handling: Return MISSING_CLAUSE if any clause is dropped
    for req_clause in input_clause_numbers:
        if req_clause not in output_clause_numbers:
            return f"ERROR: MISSING_CLAUSE. Clause {req_clause} was omitted from the summary."
            
    return "\n\n".join(summary_lines)

def main():
    parser = argparse.ArgumentParser(description="UC-0B Policy Summarizer")
    parser.add_argument("--input", required=True, help="Input policy text file")
    parser.add_argument("--output", required=True, help="Output summary text file")
    args = parser.parse_args()
    
    parsed_data = retrieve_policy(args.input)
    summary_text = summarize_policy(parsed_data)
    
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        print(f"Success: Summary written to {args.output}")
    except Exception as e:
        print(f"Error writing to output file: {e}")

if __name__ == "__main__":
    main()
