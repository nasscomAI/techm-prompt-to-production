"""
UC-0B app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import pathlib
import re
import sys
from typing import Dict, List


def retrieve_policy(file_path: pathlib.Path) -> List[Dict[str, str]]:
    """Loads a policy text file and returns numbered clauses as structured sections."""
    if file_path.suffix.lower() != ".txt":
        raise ValueError("Input must be a .txt policy document")
    if not file_path.exists():
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    clause_pattern = re.compile(r'^\s*(?:Clause\s+)?(\d+(?:\.\d+)*)\s*(?:[\.\)]\s*|\|\s*|\s+)(.*\S.*)$')

    clauses: List[Dict[str, str]] = []
    current_clause: Dict[str, str] = {}

    for line in lines:
        match = clause_pattern.match(line)
        if match:
            if current_clause:
                clauses.append(current_clause)
            current_clause = {"number": match.group(1), "text": match.group(2).strip()}
        elif current_clause and line.strip():
            current_clause["text"] += " " + line.strip()

    if current_clause:
        clauses.append(current_clause)

    if not clauses:
        raise ValueError("No numbered clauses found in policy document")

    return clauses


def summarize_policy(clauses: List[Dict[str, str]]) -> str:
    """Produces a compliant summary from structured policy clauses."""
    summary_lines = [
        "Policy Summary",
        "",
        "This summary preserves each numbered clause from the source policy and keeps all conditions intact.",
        "",
    ]

    for clause in clauses:
        summary_lines.append(f"Clause {clause['number']}: {clause['text']}")
        summary_lines.append("")

    return "\n".join(summary_lines).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UC-0B policy summarizer")
    parser.add_argument("--input", required=True, help="Path to input policy text file")
    parser.add_argument("--output", required=True, help="Path to summary output file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)

    try:
        clauses = retrieve_policy(input_path)
        summary = summarize_policy(clauses)
        output_path.write_text(summary + "\n", encoding="utf-8")
        print(f"Wrote summary to {output_path}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
