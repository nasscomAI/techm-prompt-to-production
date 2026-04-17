"""
UC-0B app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import os
import re
import sys

REQUIRED_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]

PROHIBITED_PHRASES = [
    "typically",
    "generally",
    "standard practice",
    "as is standard practice",
    "employees are generally expected to"
]

BINDING_VERBS = ["must", "requires", "will", "not permitted", "are forfeited", "may"]


# ---------------------- SKILL 1: retrieve_policy ---------------------- #
def retrieve_policy(file_path):
    if not os.path.exists(file_path):
        raise ValueError("File access error: File does not exist")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        raise ValueError("File access error: Unable to read file")

    if not lines:
        raise ValueError("Structured format error: File is empty")

    clause_dict = {}
    current_clause = None

    clause_pattern = re.compile(r'^\s*(\d+\.\d+)\b')

    for line in lines:
        match = clause_pattern.match(line)

        if match:
            current_clause = match.group(1)
            text = line.strip()

            if current_clause in clause_dict:
                clause_dict[current_clause] += " " + text
            else:
                clause_dict[current_clause] = text
        else:
            # continuation of previous clause
            if current_clause:
                clause_dict[current_clause] += " " + line.strip()

    if not clause_dict:
        raise ValueError("Structured format error: No numbered clauses found")

    structured = [
        {"clause_number": k, "clause_text": v.strip()}
        for k, v in clause_dict.items()
    ]

    return structured


# ---------------------- SKILL 2: summarize_policy ---------------------- #
def summarize_policy(structured_sections):
    if not isinstance(structured_sections, list) or not structured_sections:
        raise ValueError("Input validation error: Invalid structured input")

    clause_map = {c["clause_number"]: c["clause_text"] for c in structured_sections}

    # Enforcement: all required clauses must exist
    missing = [c for c in REQUIRED_CLAUSES if c not in clause_map]
    if missing:
        raise ValueError(f"Clause omission error: Missing clauses {missing}")

    summary_lines = []
    flags = []

    for clause in REQUIRED_CLAUSES:
        text = clause_map[clause]

        # Enforcement: preserve binding verbs
        if not any(verb in text.lower() for verb in BINDING_VERBS):
            flags.append(f"[FLAG: obligation_softening] Clause {clause} may have altered binding verb")
            summary_lines.append(f"{clause}: \"{text}\"")
            continue

        # Enforcement: multi-condition check (basic heuristic)
        if "and" in text.lower() or "AND" in text:
            # If multi-condition, do not risk summarizing → quote
            flags.append(f"[FLAG: multi_condition_preserved_verbatim] Clause {clause}")
            summary_lines.append(f"{clause}: \"{text}\"")
            continue

        # Default: keep original text (no abstraction to avoid meaning loss)
        summary_lines.append(f"{clause}: {text}")

    summary = "\n".join(summary_lines)

    # Enforcement: no scope bleed
    for phrase in PROHIBITED_PHRASES:
        if phrase in summary.lower():
            raise ValueError(f"Scope bleed error: Prohibited phrase detected -> {phrase}")

    # Final check: ensure all clauses are present in output
    for clause in REQUIRED_CLAUSES:
        if clause not in summary:
            raise ValueError(f"Clause omission error in output: {clause} missing")

    # Append flags if any
    if flags:
        summary += "\n\n" + "\n".join(flags)

    return summary


# ---------------------- MAIN APP ---------------------- #
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input policy file path")
    parser.add_argument("--output", required=True, help="Output summary file name")

    args = parser.parse_args()

    try:
        structured = retrieve_policy(args.input)
        summary = summarize_policy(structured)

        output_dir = "uc-0b"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, args.output)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"Summary successfully written to {output_path}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)




if __name__ == "__main__":
    main()
