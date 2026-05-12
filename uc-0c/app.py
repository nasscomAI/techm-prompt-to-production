import argparse

import csv
import sys


REQUIRED_COLUMNS = [
    "period",
    "ward",
    "category",
    "budgeted_amount",
    "actual_spend",
    "notes",
]


def load_dataset(file_path):
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames

            if columns is None:
                print("ERROR: CSV has no header.")
                sys.exit(1)

            # Validate columns
            missing = [col for col in REQUIRED_COLUMNS if col not in columns]
            if missing:
                print(f"ERROR: Missing required columns: {missing}")
                sys.exit(1)

            data = list(reader)

    except Exception as e:
        print(f"ERROR: Unable to read file - {e}")
        sys.exit(1)

    # Validate row count (aggregation failure detection)
    if len(data) != 300:
        print("ERROR: Dataset row count mismatch (expected 300). Possible aggregation detected.")
        sys.exit(1)

    null_rows = []
    for row in data:
        actual = row["actual_spend"].strip()
        if actual == "":
            null_rows.append({
                "period": row["period"],
                "ward": row["ward"],
                "category": row["category"],
                "notes": row["notes"]
            })

    # Report nulls (enforcement)
    if len(null_rows) > 0:
        print("INFO: Null actual_spend rows detected:")
        for r in null_rows:
            print(f"- {r['period']} | {r['ward']} | {r['category']} | reason: {r['notes']}")

    return {
        "data": data,
        "null_summary": {
            "count": len(null_rows),
            "rows": null_rows
        }
    }


def parse_float(value):
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return float(value)
    except:
        return None


def compute_growth(data, ward, category, growth_type):
    # Validate growth_type
    if growth_type is None:
        print("ERROR: --growth-type must be specified. Refusing to guess.")
        sys.exit(1)

    if growth_type != "MoM":
        print(f"ERROR: Unsupported growth_type '{growth_type}'. Only 'MoM' is allowed.")
        sys.exit(1)

    # Filter dataset
    filtered = [row for row in data if row["ward"] == ward and row["category"] == category]

    if len(filtered) == 0:
        print("ERROR: Invalid ward or category. No matching records found.")
        sys.exit(1)

    # Sort by period
    filtered.sort(key=lambda x: x["period"])

    results = []

    for i in range(len(filtered)):
        row = filtered[i]
        period = row["period"]
        actual = parse_float(row["actual_spend"])
        notes = row["notes"]

        # NULL handling
        if actual is None:
            results.append({
                "period": period,
                "actual_spend": "",
                "growth_value": "",
                "formula": f"NULL actual_spend → not computed; reason: {notes}"
            })
            continue

        # First row
        if i == 0:
            results.append({
                "period": period,
                "actual_spend": actual,
                "growth_value": "",
                "formula": "No prior period → growth not computed"
            })
            continue

        prev_row = filtered[i - 1]
        prev_actual = parse_float(prev_row["actual_spend"])

        # Previous NULL
        if prev_actual is None:
            results.append({
                "period": period,
                "actual_spend": actual,
                "growth_value": "",
                "formula": "Previous period actual_spend is NULL → growth not computed"
            })
            continue

        # Compute MoM
        growth = ((actual - prev_actual) / prev_actual) * 100
        formula = f"(({actual} - {prev_actual}) / {prev_actual}) * 100"

        results.append({
            "period": period,
            "actual_spend": actual,
            "growth_value": round(growth, 2),
            "formula": formula
        })

    return results


def write_output(results, output_path):
    try:
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["period", "actual_spend", "growth_value", "formula"]
            )
            writer.writeheader()
            for row in results:
                writer.writerow(row)
    except Exception as e:
        print(f"ERROR: Failed to write output - {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--ward", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--growth-type", dest="growth_type", required=False)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    # Enforcement: must not guess growth-type
    if args.growth_type is None:
        print("ERROR: --growth-type not specified. Refusing to proceed.")
        sys.exit(1)

    dataset = load_dataset(args.input)

    results = compute_growth(
        dataset["data"],
        ward=args.ward,
        category=args.category,
        growth_type=args.growth_type
    )

    write_output(results, args.output)

    print(f"SUCCESS: Output written to {args.output}")

if __name__ == "__main__":
    main()
