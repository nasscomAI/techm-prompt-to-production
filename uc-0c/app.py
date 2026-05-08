"""
UC-0C app.py — Budget growth analyst for municipal ward spending data.
Computes per-ward per-category MoM or YoY growth from ward_budget.csv.
See README.md for run command and expected behaviour.
"""
import argparse
import csv
import sys


REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}


# --- Skill: load_dataset ---

def load_dataset(file_path):
    """Reads CSV, validates columns, reports null rows before returning data."""
    try:
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - columns
            if missing:
                print(f"ERROR: Missing required columns: {sorted(missing)}")
                print(f"       Found columns: {sorted(columns)}")
                sys.exit(1)
            rows = list(reader)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    null_rows = [
        r for r in rows if r["actual_spend"].strip() == ""
    ]

    if null_rows:
        print(f"NULL REPORT — {len(null_rows)} row(s) with missing actual_spend:")
        for r in null_rows:
            reason = r["notes"].strip() or "no reason given"
            print(f"  {r['period']} · {r['ward']} · {r['category']} → {reason}")
        print()

    return rows, null_rows


# --- Skill: compute_growth ---

def compute_growth(rows, ward, category, growth_type):
    """
    Computes per-period growth for a single ward and category.
    Returns a list of result dicts with formula shown.
    Null rows are flagged, not computed.
    """
    filtered = [
        r for r in rows
        if r["ward"].strip() == ward and r["category"].strip() == category
    ]

    if not filtered:
        print(f"ERROR: No data found for ward='{ward}' category='{category}'.")
        print("       Check that ward and category match dataset values exactly.")
        sys.exit(1)

    filtered.sort(key=lambda r: r["period"])

    results = []

    if growth_type == "MoM":
        for i, row in enumerate(filtered):
            period = row["period"].strip()
            spend_raw = row["actual_spend"].strip()

            if spend_raw == "":
                results.append({
                    "period": period,
                    "ward": ward,
                    "category": category,
                    "actual_spend": "NULL",
                    "growth_value": "NULL",
                    "formula": f"NULL — {row['notes'].strip() or 'missing data'}",
                })
                continue

            current = float(spend_raw)

            # find previous non-null
            prev_row = None
            for j in range(i - 1, -1, -1):
                if filtered[j]["actual_spend"].strip() != "":
                    prev_row = filtered[j]
                    break

            if prev_row is None:
                results.append({
                    "period": period,
                    "ward": ward,
                    "category": category,
                    "actual_spend": current,
                    "growth_value": "N/A",
                    "formula": "No prior period available",
                })
            else:
                previous = float(prev_row["actual_spend"])
                growth = (current - previous) / previous * 100
                results.append({
                    "period": period,
                    "ward": ward,
                    "category": category,
                    "actual_spend": current,
                    "growth_value": f"{growth:+.1f}%",
                    "formula": f"({current} - {previous}) / {previous} × 100",
                })

    elif growth_type == "YoY":
        # Build lookup by period for same ward/category
        spend_by_period = {
            r["period"].strip(): float(r["actual_spend"])
            for r in filtered if r["actual_spend"].strip() != ""
        }

        for row in filtered:
            period = row["period"].strip()
            spend_raw = row["actual_spend"].strip()
            year, month = period.split("-")
            prior_period = f"{int(year) - 1}-{month}"

            if spend_raw == "":
                results.append({
                    "period": period,
                    "ward": ward,
                    "category": category,
                    "actual_spend": "NULL",
                    "growth_value": "NULL",
                    "formula": f"NULL — {row['notes'].strip() or 'missing data'}",
                })
                continue

            current = float(spend_raw)

            if prior_period not in spend_by_period:
                results.append({
                    "period": period,
                    "ward": ward,
                    "category": category,
                    "actual_spend": current,
                    "growth_value": "N/A",
                    "formula": f"No data for prior year period {prior_period}",
                })
            else:
                previous = spend_by_period[prior_period]
                growth = (current - previous) / previous * 100
                results.append({
                    "period": period,
                    "ward": ward,
                    "category": category,
                    "actual_spend": current,
                    "growth_value": f"{growth:+.1f}%",
                    "formula": f"({current} - {previous}) / {previous} × 100",
                })

    return results


def write_output(results, output_path):
    fieldnames = ["period", "ward", "category", "actual_spend", "growth_value", "formula"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Output written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Analyst")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Ward name (exact match)")
    parser.add_argument("--category", required=True, help="Category name (exact match)")
    parser.add_argument(
        "--growth-type",
        choices=["MoM", "YoY"],
        default=None,
        help="Growth type: MoM or YoY",
    )
    parser.add_argument("--output", required=True, help="Output CSV file path")
    args = parser.parse_args()

    # Enforcement: refuse if --growth-type not specified
    if args.growth_type is None:
        print("ERROR: --growth-type is required. Please specify 'MoM' or 'YoY'.")
        print("       Example: --growth-type MoM")
        sys.exit(1)

    rows, _ = load_dataset(args.input)
    results = compute_growth(rows, args.ward, args.category, args.growth_type)
    write_output(results, args.output)


if __name__ == "__main__":
    main()

