import argparse

CLAUSE_SUMMARIES = {
    "2.3": "Employees must provide 14-day advance notice before taking leave.",
    "2.4": "Written approval must be obtained before leave commences. Verbal approval is not valid.",
    "2.5": "Unapproved absence will be treated as Loss of Pay regardless of subsequent approval.",
    "2.6": "A maximum of 5 leave days may be carried forward. Any balance above 5 days is forfeited on 31 December.",
    "2.7": "Carry-forward leave days must be used between January and March or they are forfeited.",
    "3.2": "Three or more consecutive sick leave days requires a medical certificate within 48 hours.",
    "3.4": "Sick leave taken before or after a holiday requires a medical certificate regardless of duration.",
    "5.2": "Leave Without Pay requires approval from BOTH the Department Head AND the HR Director.",
    "5.3": "Leave Without Pay exceeding 30 days requires Municipal Commissioner approval.",
    "7.2": "Leave encashment during service is not permitted under any circumstances."
}

def retrieve_policy(input_file):
    with open(input_file, "r", encoding="utf-8") as file:
        return file.read()

def summarize_policy(policy_text):
    summary_lines = []

    for clause, summary in CLAUSE_SUMMARIES.items():
        summary_lines.append(f"{clause}: {summary}")

    return "\n".join(summary_lines)

def save_summary(output_file, summary):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(summary)

def main(input_file, output_file):
    policy_text = retrieve_policy(input_file)

    summary = summarize_policy(policy_text)

    save_summary(output_file, summary)

    print(f"Summary saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    main(args.input, args.output)