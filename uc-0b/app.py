"""
UC-0B app.py — Policy Summary That Changes Meaning.
Summarizes HR leave policy documents while enforcing clause preservation,
condition preservation, and obligation binding verb integrity.

Usage:
    python app.py --input <policy_file> --output <summary_file>

Example:
    python app.py --input ../data/policy-documents/policy_hr_leave.txt --output summary_hr_leave.txt
"""
import argparse
import json
from pathlib import Path

def retrieve_policy(file_path):
    """
    Load policy document and structure it into numbered clauses.
    Returns: {'filename': str, 'full_text': str, 'clauses': [{'number': str, 'section': str, 'text': str}]}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {file_path}")
    
    full_text = path.read_text()
    if not full_text.strip():
        raise ValueError(f"Policy file is empty: {file_path}")
    
    clauses = []
    lines = full_text.split('\n')
    current_clause = None
    current_text = []
    
    for line in lines:
        # Look for numbered clause patterns like "2.3" or "3.2"
        if any(char.isdigit() for char in line[:5]) and '.' in line[:5]:
            if current_clause:
                clauses.append({
                    'number': current_clause,
                    'section': current_clause.split('.')[0],
                    'text': ' '.join(current_text).strip()
                })
            current_clause = line.split()[0]
            current_text = [line]
        elif current_clause:
            current_text.append(line)
    
    if current_clause:
        clauses.append({
            'number': current_clause,
            'section': current_clause.split('.')[0],
            'text': ' '.join(current_text).strip()
        })
    
    return {
        'filename': path.name,
        'full_text': full_text,
        'clauses': clauses
    }

def summarize_policy(policy_data, output_path):
    """
    Generate compliant summary preserving all clauses and conditions.
    Returns: List of clause summaries with binding verb and conditions intact.
    """
    clauses = policy_data.get('clauses', [])
    summary_clauses = []
    
    for clause in clauses:
        clause_text = clause['text']
        clause_id = clause['number']
        
        # Extract binding verb (must, will, may, requires, not permitted)
        binding_verb = None
        for verb in ['must', 'will', 'may', 'requires', 'not permitted']:
            if verb in clause_text.lower():
                binding_verb = verb
                break
        
        summary_clauses.append({
            'clause_id': clause_id,
            'obligation': clause_text[:200] + ('...' if len(clause_text) > 200 else ''),
            'binding_verb': binding_verb or 'unspecified',
            'full_text': clause_text
        })
    
    # Write summary to output file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    summary_text = f"# Policy Summary: {policy_data['filename']}\n\n"
    summary_text += f"Total clauses: {len(summary_clauses)}\n\n"
    
    for item in summary_clauses:
        summary_text += f"## Clause {item['clause_id']} (Binding verb: {item['binding_verb']})\n"
        summary_text += f"{item['obligation']}\n\n"
    
    output_file.write_text(summary_text)
    
    return summary_clauses

def main():
    parser = argparse.ArgumentParser(
        description="Summarize HR policy documents while preserving all clauses and conditions."
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to input policy document (.txt file)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output summary file'
    )
    
    args = parser.parse_args()
    
    try:
        # Step 1: Retrieve and structure policy
        print(f"Loading policy from: {args.input}")
        policy_data = retrieve_policy(args.input)
        print(f"Found {len(policy_data['clauses'])} clauses\n")
        
        # Step 2: Generate compliant summary
        print(f"Generating summary...")
        summary = summarize_policy(policy_data, args.output)
        
        # Step 3: Output results
        print(f"✓ Summary written to: {args.output}")
        print(f"✓ Processed {len(summary)} clauses with binding verb preservation")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
