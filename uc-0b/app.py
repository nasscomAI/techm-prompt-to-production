"""
UC-0B app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import re

def parse_clauses(input_file):
    """Parse clauses from the input file."""
    clauses = {}
    with open(input_file, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
        lines = file.readlines()
        clause_pattern = re.compile(r'^(\d+\.\d+)\s+(.*)$')
        for line in lines:
            match = clause_pattern.match(line.strip())
            if match:
                clause_number, clause_text = match.groups()
                clauses[clause_number] = clause_text
    return clauses

def summarize_clauses(clauses):
    """Summarize clauses while preserving all conditions."""
    summaries = {}
    for clause_number, clause_text in clauses.items():
        summaries[clause_number] = clause_text  # For now, keep the full text
    return summaries

def write_summary(output_file, summaries):
    """Write the summarized clauses to the output file."""
    with open(output_file, 'w') as file:
        for clause_number, summary in summaries.items():
            file.write(f"{clause_number}: {summary}\n")

def main():
    parser = argparse.ArgumentParser(description="Summarize HR Leave Policy clauses.")
    parser.add_argument('--input', required=True, help="Path to the input file.")
    parser.add_argument('--output', required=True, help="Path to the output file.")
    args = parser.parse_args()

    # Parse, summarize, and write clauses
    clauses = parse_clauses(args.input)
    summaries = summarize_clauses(clauses)
    write_summary(args.output, summaries)

if __name__ == "__main__":
    main()
