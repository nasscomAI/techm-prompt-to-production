"""
UC-0B app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse


def retrieve_policy(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections = []
    for line in lines:
        line = line.strip()
        if line:
            sections.append(line)

    return sections


def summarize_policy(sections):
    summary = []

    for clause in sections:
        # keep original clause to avoid meaning loss
        summary.append(clause)

    return "\n".join(summary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sections = retrieve_policy(args.input)
    summary = summarize_policy(sections)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)

    print("Done")


if __name__ == "__main__":
    main()