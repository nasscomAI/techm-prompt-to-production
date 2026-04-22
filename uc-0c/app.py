"""
UC-0C app.py — Computes growth metrics for ward-level budget data.

Build from agents.md + skills.md + README:
- Never aggregate across wards/categories unless explicitly asked
- Flag null actual_spend rows and report notes
- Show formula for every computed growth value
- Refuse if --growth-type is missing or invalid
"""
import argparse
import csv
from typing import List, Dict, Tuple


REQUIRED_COLUMNS = [
    "period",
    "ward",
    "category",
    "budgeted_amount",
    "actual_spend",
    "notes",
]


def load_dataset(input_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Load ward_budget.csv, validate columns, and report null rows.

    Returns:
      rows: list of dicts
      null_rows: list of dicts with null actual_spend
    """
    rows: List[Dict] = []
    null_rows: List[Dict] = []

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Validate columns
        missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for row in reader:
            # Normalize keys just in case
            row = {k: (v if v is not None else "") for k, v in row.items()}
            actual_spend_raw = row.get("actual_spend", "").strip()

            # Track null actual_spend
            if actual_spend_raw == "":
                null_rows.append(row)
                row["actual_spend"] = None
            else:
                try:
                    row["actual_spend"] = float(actual_spend_raw)
                except ValueError:
                    # Treat invalid numbers as nulls and flag
                    row["actual_spend"] = None
                    null_rows.append(row)

            # Convert budgeted_amount to float if possible
            ba_raw = row.get("budgeted_amount", "").strip()
            try:
                row["budgeted_amount"] = float(ba_raw) if ba_raw != "" else None
            except ValueError:
                row["budgeted_amount"] = None

            rows.append(row)

    # Optional: print or log null summary to console
    if null_rows:
        print(f"Found {len(null_rows)} rows with null actual_spend:")
        for r in null_rows:
            print(
                f"  {r.get('period')} · {r.get('ward')} · {r.get('category')} "
                f"→ notes: {r.get('notes')}"
            )

    return rows, null_rows


def compute_growth(
    rows: List[Dict],
    ward: str,
    category: str,
    growth_type: str,
) -> List[Dict]:
    """
    Compute growth per period for the given ward and category.

    For MoM (month-over-month):
      growth_value = (current - previous) / previous
    - If current or previous actual_spend is null, do not compute growth.
    - Return list of dicts with: period, ward, category, actual_spend,
      growth_value (as percentage string or blank), growth_formula, flag.
    """
    if not growth_type:
        raise ValueError("growth_type is required (e.g. --growth-type MoM).")

    growth_type = growth_type.strip()
    if growth_type != "MoM":
        # Enforce: do not guess formula
        raise ValueError(f"Unsupported growth_type='{growth_type}'. Only 'MoM' is supported.")

    # Filter rows
    filtered = [
        r for r in rows
        if r.get("ward") == ward and r.get("category") == category
    ]

    if not filtered:
        print(f"No data found for ward='{ward}' and category='{category}'.")
        return []

    # Sort by period string (YYYY-MM), lexicographic works here for 2024-01..12
    filtered.sort(key=lambda r: r.get("period", ""))

    results: List[Dict] = []
    prev_row = None

    for row in filtered:
        period = row.get("period")
        actual = row.get("actual_spend")
        notes = row.get("notes", "")

        result_row = {
            "period": period,
            "ward": ward,
            "category": category,
            "actual_spend": "" if actual is None else f"{actual:.1f}",
            "growth_value": "",
            "growth_formula": "",
            "flag": "",
            "notes": notes,
        }

        # Decide whether we can compute MoM growth
        if prev_row is None:
            # First period has no previous; cannot compute growth
            result_row["growth_formula"] = "N/A (no previous period)"
            result_row["flag"] = "NO_PREVIOUS_PERIOD"
        else:
            prev_period = prev_row.get("period")
            prev_actual = prev_row.get("actual_spend")

            if actual is None:
                # Current null: must flag and not compute
                result_row["growth_formula"] = "N/A (current actual_spend is null)"
                result_row["flag"] = "NULL_CURRENT_ACTUAL_SPEND"
            elif prev_actual is None:
                # Previous null: must flag and not compute
                result_row["growth_formula"] = (
                    f"N/A (previous actual_spend is null for {prev_period})"
                )
                result_row["flag"] = "NULL_PREVIOUS_ACTUAL_SPEND"
            else:
                # Both non-null → compute MoM
                diff = actual - prev_actual
                if prev_actual == 0:
                    result_row["growth_formula"] = (
                        f"N/A (previous actual_spend is 0 for {prev_period})"
                    )
                    result_row["flag"] = "ZERO_PREVIOUS_ACTUAL_SPEND"
                else:
                    growth = diff / prev_actual
                    # Represent as percentage with one decimal place
                    growth_pct = growth * 100
                    result_row["growth_value"] = f"{growth_pct:.1f}%"
                    result_row["growth_formula"] = (
                        f"({actual:.1f} - {prev_actual:.1f}) / {prev_actual:.1f}"
                    )

        results.append(result_row)
        prev_row = row

    return results


def write_output(output_path: str, results: List[Dict]) -> None:
    """
    Write growth_output.csv with per-period rows.
    """
    if not results:
        print("No results to write.")
        return

    fieldnames = [
        "period",
        "ward",
        "category",
        "actual_spend",
        "growth_value",
        "growth_formula",
        "flag",
        "notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"Done. Results written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="UC-0C — Growth calculator")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Ward name (e.g. 'Ward 1 – Kasba')")
    parser.add_argument(
        "--category",
        required=True,
        help="Category name (e.g. 'Roads & Pothole Repair')",
    )
    parser.add_argument(
        "--growth-type",
        required=True,
        help="Growth type, e.g. 'MoM' for month-over-month",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write growth_output.csv",
    )

    args = parser.parse_args()

    # Load and validate dataset
    rows, null_rows = load_dataset(args.input)

    # Compute growth for the requested ward/category
    results = compute_growth(rows, args.ward, args.category, args.growth_type)

    # Write output CSV
    write_output(args.output, results)


if __name__ == "__main__":
    main()
