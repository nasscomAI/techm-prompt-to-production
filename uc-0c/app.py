"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import csv
import sys

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--output", required=True, help="Path to write output")
    parser.add_argument("--ward", required=False)
    parser.add_argument("--category", required=False)
    parser.add_argument("--growth-type", required=False)
    args = parser.parse_args()

    # 1. Enforcement: Refuse if required arguments are missing (Never Guess)
    if not args.ward or not args.category or not getattr(args, 'growth_type', None):
        print("ERROR: System REFUSES to aggregate. Ward, category, and growth-type must be explicitly provided.")
        sys.exit(1)
        
    if args.growth_type != "MoM":
        print(f"ERROR: Only MoM growth is supported in this strict implementation. Provided: {args.growth_type}")
        sys.exit(1)

    filtered_data = []
    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ward'] == args.ward and row['category'] == args.category:
                filtered_data.append(row)

    if not filtered_data:
        print("ERROR: No data found for the specified Ward and Category.")
        sys.exit(1)

    # Sort by period to calculate MoM
    filtered_data.sort(key=lambda x: x['period'])

    results = []
    prev_actual = None

    for row in filtered_data:
        period = row['period']
        actual_str = row['actual_spend'].strip()
        notes = row.get('notes', '')
        
        # 2. Enforcement: Null Reporting
        if not actual_str:
            results.append({
                'Ward': args.ward,
                'Category': args.category,
                'Period': period,
                'Actual Spend': 'NULL',
                'MoM Growth': 'NULL_FOUND',
                'Formula': 'Not Computed due to NULL',
                'Notes': f"Flagged Null: {notes}"
            })
            prev_actual = None # Break the chain
            continue

        try:
            actual = float(actual_str)
        except ValueError:
            actual = 0.0

        growth_str = "n/a (First Month)"
        formula_str = "n/a"
        if prev_actual is not None and prev_actual != 0:
            growth_val = ((actual - prev_actual) / prev_actual) * 100
            growth_str = f"{growth_val:+.1f}%"
            formula_str = f"(({actual} - {prev_actual}) / {prev_actual}) * 100"

        results.append({
            'Ward': args.ward,
            'Category': args.category,
            'Period': period,
            'Actual Spend': actual_str,
            'MoM Growth': growth_str,
            'Formula': formula_str,
            'Notes': ''
        })
        
        prev_actual = actual

    # 3. Specific Output Format
    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Ward', 'Category', 'Period', 'Actual Spend', 'MoM Growth', 'Formula', 'Notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Done. Strict calculation written to {args.output}")

if __name__ == "__main__":
    main()
