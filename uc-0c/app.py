"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""

import argparse
import csv
import sys

def load_dataset(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames
            expected = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
            missing = [c for c in expected if c not in columns]
            if missing:
                raise ValueError(f"Missing columns: {missing}")

            data = []
            null_rows = []
            for row in reader:
                val = row['actual_spend'].strip()
                if not val:
                    row['actual_spend'] = None
                    null_rows.append(row)
                else:
                    row['actual_spend'] = float(val)
                data.append(row)

            print(f"Dataset loaded. Total nulls: {len(null_rows)}")
            for nr in null_rows:
                print(f"  Null row flagged: {nr['period']} | {nr['ward']} | {nr['category']} | Reason: {nr['notes']}")

            return {
                "data": data,
                "null_report": {
                    "total_nulls": len(null_rows),
                    "null_rows": null_rows
                }
            }
    except FileNotFoundError:
        print(f"FileNotFoundError: Cannot find {path}", file=sys.stderr)
        sys.exit(1)

def compute_growth(dataset_info, ward, category, growth_type):
    if not growth_type:
        raise ValueError("Growth type not specified. Please provide --growth-type (e.g., MoM). Never guess.")

    if not ward or not category:
        raise ValueError("AggregationError: Refusing to aggregate across wards or categories. Please specify --ward and --category.")

    # Filter data for ward and category
    filtered = [r for r in dataset_info['data'] if r['ward'] == ward and r['category'] == category]

    # Sort by period
    filtered.sort(key=lambda x: x['period'])

    results = []

    for i in range(len(filtered)):
        row = filtered[i]
        period = row['period']
        actual = row['actual_spend']
        notes = row['notes']

        if actual is None:
            results.append({
                "period": period,
                "actual_spend": "NULL",
                "growth": "NULL",
                "formula": f"NULL - {notes}"
            })
            continue

        if growth_type.upper() == 'MOM':
            if i == 0:
                results.append({
                    "period": period,
                    "actual_spend": actual,
                    "growth": "n/a",
                    "formula": "First period (no baseline)"
                })
            else:
                prev_actual = filtered[i-1]['actual_spend']
                if prev_actual is None:
                    results.append({
                        "period": period,
                        "actual_spend": actual,
                        "growth": "n/a",
                        "formula": "Previous period was NULL"
                    })
                else:
                    growth_val = ((actual - prev_actual) / prev_actual) * 100
                    sign = "+" if growth_val > 0 else ""
                    results.append({
                        "period": period,
                        "actual_spend": actual,
                        "growth": f"{sign}{growth_val:.1f}%",
                        "formula": f"(({actual} - {prev_actual}) / {prev_actual}) * 100"
                    })
        elif growth_type.upper() == 'YOY':
            results.append({
                "period": period,
                "actual_spend": actual,
                "growth": "n/a",
                "formula": "YoY not fully implemented in this example"
            })
        else:
            raise ValueError(f"Unsupported growth_type: {growth_type}")

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--ward', help="Specific ward to analyze")
    parser.add_argument('--category', help="Specific category to analyze")
    parser.add_argument('--growth-type', help="Type of growth (e.g., MoM)")

    args = parser.parse_args()

    try:
        dataset_info = load_dataset(args.input)

        if not args.growth_type:
            print("Error: --growth-type not specified. Refusing to guess.", file=sys.stderr)
            sys.exit(1)

        results = compute_growth(dataset_info, args.ward, args.category, args.growth_type)

        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['period', 'actual_spend', 'growth', 'formula'])
            writer.writeheader()
            writer.writerows(results)

        print(f"Done. Output written to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        

if __name__ == "__main__":
    main()
