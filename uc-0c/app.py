"""
UC-0C — Number That Looks Right
Computes per-ward per-category budget growth with null detection and formula display.

Enforcement:
  1. Never aggregate across wards or categories — refuse if not specified
  2. Flag every null row before computing — report null reason from notes column
  3. Show the formula used in every output row alongside the result
  4. If --growth-type not specified — refuse and ask; never guess a formula
"""
import argparse
import csv
import sys


def load_dataset(csv_path: str):
    """
    Read CSV, validate columns, report null count and which rows before returning.
    Returns (rows, null_rows).
    null_rows is a list of dicts: {period, ward, category, notes}.
    """
    required_cols = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print("ERROR: CSV file is empty or has no headers.", file=sys.stderr)
                sys.exit(1)
            missing_cols = required_cols - set(reader.fieldnames)
            if missing_cols:
                print(f"ERROR: Missing required columns: {missing_cols}", file=sys.stderr)
                sys.exit(1)
            rows = list(reader)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    null_rows = [
        {
            "period":   r["period"],
            "ward":     r["ward"],
            "category": r["category"],
            "notes":    r.get("notes", "").strip(),
        }
        for r in rows
        if not r.get("actual_spend", "").strip()
    ]

    return rows, null_rows


def compute_growth(rows: list, ward: str, category: str, growth_type: str) -> list:
    """
    Filter to a single ward + category, compute per-period growth.
    Each result row includes period, actual_spend, growth, formula, null_reason.
    Null rows are flagged, not skipped.
    """
    filtered = [
        r for r in rows
        if r["ward"].strip() == ward.strip()
        and r["category"].strip() == category.strip()
    ]

    if not filtered:
        return []

    filtered.sort(key=lambda r: r["period"])

    results = []
    for i, row in enumerate(filtered):
        period    = row["period"]
        raw_spend = row.get("actual_spend", "").strip()
        notes     = row.get("notes", "").strip()

        # Null actual_spend — flag, do not compute
        if not raw_spend:
            results.append({
                "period":       period,
                "ward":         ward,
                "category":     category,
                "actual_spend": "NULL",
                "growth":       "NULL — FLAGGED",
                "formula":      "Not computed — actual_spend is null",
                "null_reason":  notes or "No reason recorded in notes column",
            })
            continue

        try:
            current = float(raw_spend)
        except ValueError:
            results.append({
                "period":       period,
                "ward":         ward,
                "category":     category,
                "actual_spend": raw_spend,
                "growth":       "ERROR",
                "formula":      f"Could not parse actual_spend value '{raw_spend}'",
                "null_reason":  "",
            })
            continue

        # Compute growth
        if growth_type == "MoM":
            if i == 0:
                growth  = "N/A"
                formula = "First period in dataset — no prior month available"
            else:
                prev_row = filtered[i - 1]
                prev_raw = prev_row.get("actual_spend", "").strip()
                prev_period = prev_row["period"]
                if not prev_raw:
                    growth  = "NULL — FLAGGED"
                    formula = (
                        f"Prior month {prev_period} actual_spend is null — "
                        "MoM not computable"
                    )
                else:
                    prev = float(prev_raw)
                    if prev == 0:
                        growth  = "UNDEFINED"
                        formula = (
                            f"({current} − {prev}) / {prev} × 100 "
                            "— division by zero"
                        )
                    else:
                        pct     = (current - prev) / prev * 100
                        growth  = f"{pct:+.1f}%"
                        formula = f"({current} − {prev}) / {prev} × 100"

        elif growth_type == "YoY":
            year, month = period.split("-")
            prev_period = f"{int(year) - 1}-{month}"
            prev_match  = [r for r in filtered if r["period"] == prev_period]
            if not prev_match:
                growth  = "N/A"
                formula = f"No data found for prior year period {prev_period}"
            else:
                prev_raw = prev_match[0].get("actual_spend", "").strip()
                if not prev_raw:
                    growth  = "NULL — FLAGGED"
                    formula = (
                        f"Prior year period {prev_period} actual_spend is null — "
                        "YoY not computable"
                    )
                else:
                    prev = float(prev_raw)
                    if prev == 0:
                        growth  = "UNDEFINED"
                        formula = (
                            f"({current} − {prev}) / {prev} × 100 "
                            "— division by zero"
                        )
                    else:
                        pct     = (current - prev) / prev * 100
                        growth  = f"{pct:+.1f}%"
                        formula = f"({current} − {prev}) / {prev} × 100"
        else:
            growth  = "ERROR"
            formula = f"Unknown growth_type '{growth_type}'"

        results.append({
            "period":       period,
            "ward":         ward,
            "category":     category,
            "actual_spend": str(current),
            "growth":       growth,
            "formula":      formula,
            "null_reason":  "",
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Calculator")
    parser.add_argument("--input",       required=True,
                        help="Path to ward_budget.csv")
    parser.add_argument("--ward",
                        help="Ward name — required; all-ward aggregation is refused")
    parser.add_argument("--category",
                        help="Category name — required; all-category aggregation is refused")
    parser.add_argument("--growth-type", dest="growth_type",
                        help="Growth formula: MoM (month-over-month) or YoY (year-over-year)")
    parser.add_argument("--output",      required=True,
                        help="Path to write results CSV")
    args = parser.parse_args()

    # Enforcement: refuse missing or all-ward/all-category inputs
    if not args.ward:
        print(
            "REFUSED: --ward is required.\n"
            "Aggregating across all wards is not permitted.\n"
            "Please specify a single ward, e.g.: --ward \"Ward 1 – Kasba\"",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.category:
        print(
            "REFUSED: --category is required.\n"
            "Aggregating across all categories is not permitted.\n"
            "Please specify a single category, e.g.: --category \"Roads & Pothole Repair\"",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.growth_type:
        print(
            "REFUSED: --growth-type not specified.\n"
            "This system does not assume a formula. Please provide:\n"
            "  --growth-type MoM   (month-over-month)\n"
            "  --growth-type YoY   (year-over-year)",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.growth_type not in ("MoM", "YoY"):
        print(
            f"ERROR: --growth-type must be 'MoM' or 'YoY', got '{args.growth_type}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load dataset and report nulls before computing
    print(f"Loading dataset: {args.input}")
    rows, null_rows = load_dataset(args.input)
    print(f"Loaded {len(rows)} rows.")

    print(f"\n[NULL REPORT] {len(null_rows)} row(s) with null actual_spend "
          f"(flagged — not computed):")
    if null_rows:
        for nr in null_rows:
            note = f"  — {nr['notes']}" if nr["notes"] else ""
            print(f"  {nr['period']}  |  {nr['ward']}  |  {nr['category']}{note}")
    else:
        print("  None.")

    # Compute growth for the specified ward + category
    print(
        f"\nComputing {args.growth_type} growth for:\n"
        f"  Ward    : {args.ward}\n"
        f"  Category: {args.category}"
    )
    results = compute_growth(rows, args.ward, args.category, args.growth_type)

    if not results:
        print(
            f"\nERROR: No data found for ward='{args.ward}' "
            f"category='{args.category}'.\n"
            "Check that names match the dataset exactly (case-sensitive).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write output CSV
    fieldnames = [
        "period", "ward", "category", "actual_spend",
        "growth", "formula", "null_reason",
    ]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults ({len(results)} rows) written to: {args.output}")

    flagged = [r for r in results if "FLAGGED" in r.get("growth", "")]
    if flagged:
        print(f"\n[FLAGGED ROWS] {len(flagged)} row(s) with null or uncomputable growth:")
        for r in flagged:
            print(f"  {r['period']}  growth={r['growth']}  —  {r['formula']}")


if __name__ == "__main__":
    main()
