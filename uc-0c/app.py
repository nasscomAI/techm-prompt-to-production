"""
UC-0C — Budget Growth Analyser
Reads ward_budget.csv and computes MoM or YoY spend growth for a
specific ward + category combination. Refuses aggregation. Flags nulls.
Shows formula for every row.
"""
import argparse
import csv
import sys

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}


class ColumnValidationError(Exception):
    pass


class LookupError(Exception):
    pass

#loads dataset from sample
def load_dataset(file_path: str) -> tuple[list[dict], list[dict]]:
    """
    Reads ward_budget.csv, validates columns, and reports null actual_spend rows.
    Returns (all_rows, null_rows).
    
    Args:
        file_path (str): Path to the budget CSV file.
        
    Returns:
        tuple[list[dict], list[dict]]: A tuple containing two lists: 
            - all_rows: All loaded dataset rows.
            - null_rows: Rows where 'actual_spend' is empty or null.
            
    Raises:
        FileNotFoundError: If the dataset file is not found.
        ColumnValidationError: If required columns are missing from the dataset.
    """
    try:
        with open(file_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            missing_cols = REQUIRED_COLUMNS - fieldnames
            if missing_cols:
                raise ColumnValidationError(
                    f"Missing required columns: {', '.join(sorted(missing_cols))}"
                )
            rows = [row for row in reader]
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    null_rows = [
        {
            "period":   r["period"],
            "ward":     r["ward"],
            "category": r["category"],
            "reason":   r["notes"] or "No reason provided",
        }
        for r in rows
        if r["actual_spend"].strip() == ""
    ]

    print(f"  Dataset loaded: {len(rows)} rows total, {len(null_rows)} null actual_spend rows.")
    if null_rows:
        print("\n  NULL ROWS (will be flagged — not computed):")
        for nr in null_rows:
            print(f"    [{nr['period']}] {nr['ward']} / {nr['category']} — {nr['reason']}")
    print()

    return rows, null_rows


def compute_growth(
    rows: list[dict],
    ward: str,
    category: str,
    growth_type: str,
) -> list[dict]:
    """
    Filter to ward+category, compute MoM or YoY growth per period.
    Returns list of result dicts with formula shown for every row.
    
    Args:
        rows (list[dict]): The full dataset rows.
        ward (str): The target ward name to filter by.
        category (str): The target category to filter by.
        growth_type (str): The type of growth to compute ('MoM' or 'YoY').
        
    Returns:
        list[dict]: List of result dictionaries containing period, actual_spend, 
                    growth percentage, and the formula used for calculation.
                    
    Raises:
        ValueError: If an invalid growth_type is provided.
        LookupError: If no data rows are found for the specified ward and category.
    """
    if growth_type not in ("MoM", "YoY"):
        raise ValueError(
            f"Invalid growth_type '{growth_type}'. "
            "Please specify --growth-type MoM or --growth-type YoY."
        )

    # Filter
    filtered = [
        r for r in rows
        if r["ward"].strip() == ward.strip() and r["category"].strip() == category.strip()
    ]

    if not filtered:
        available_wards = sorted({r["ward"] for r in rows})
        available_cats  = sorted({r["category"] for r in rows})
        raise LookupError(
            f"No rows found for ward='{ward}', category='{category}'.\n"
            f"  Available wards: {available_wards}\n"
            f"  Available categories: {available_cats}"
        )

    # Sort by period
    filtered.sort(key=lambda r: r["period"])

    # Build a period → actual_spend dict for lookups
    def parse_spend(r: dict) -> float | None:
        v = r["actual_spend"].strip()
        return float(v) if v else None

    # Index by period for YoY lookups
    spend_by_period: dict[str, float | None] = {r["period"]: parse_spend(r) for r in filtered}

    results = []
    for r in filtered:
        period  = r["period"]
        spend   = parse_spend(r)
        note    = r["notes"].strip() if r["notes"] else ""

        if spend is None:
            results.append({
                "period":       period,
                "actual_spend": "NULL",
                "growth_pct":   "NULL_FLAGGED",
                "formula":      f"N/A — actual_spend missing: {note}",
            })
            continue

        # Determine prior period
        if growth_type == "MoM":
            year, month = int(period[:4]), int(period[5:])
            if month == 1:
                prior_period = f"{year - 1}-12"
            else:
                prior_period = f"{year}-{month - 1:02d}"
        else:  # YoY
            year = int(period[:4])
            prior_period = f"{year - 1}-{period[5:]}"

        prior_spend = spend_by_period.get(prior_period)

        if prior_spend is None and prior_period in spend_by_period:
            # Period exists but data is null
            results.append({
                "period":       period,
                "actual_spend": f"{spend:.1f}",
                "growth_pct":   "PRIOR_NULL",
                "formula":      f"N/A — prior period {prior_period} actual_spend is null",
            })
        elif prior_spend is None:
            # Prior period not in dataset (e.g. first month)
            results.append({
                "period":       period,
                "actual_spend": f"{spend:.1f}",
                "growth_pct":   "N/A",
                "formula":      f"No prior period ({prior_period}) in dataset",
            })
        else:
            growth = (spend - prior_spend) / prior_spend * 100
            sign   = "+" if growth >= 0 else ""
            formula = (
                f"({spend:.1f} - {prior_spend:.1f}) / {prior_spend:.1f} "
                f"= {sign}{growth:.1f}%"
            )
            results.append({
                "period":       period,
                "actual_spend": f"{spend:.1f}",
                "growth_pct":   f"{sign}{growth:.1f}%",
                "formula":      formula,
            })

    return results


def main():
    """
    Main entry point for the budget growth analyser script.
    
    Parses command-line arguments, loads the dataset, computes the requested 
    growth metrics, and writes the results to a CSV file while printing a preview.
    """
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Analyser")
    parser.add_argument("--input",       required=True,  help="Path to ward_budget.csv")
    parser.add_argument("--ward",        required=True,  help="Ward name (exact string)")
    parser.add_argument("--category",    required=True,  help="Category name (exact string)")
    parser.add_argument("--growth-type", required=True,
                        help="Growth calculation type: MoM or YoY")
    parser.add_argument("--output",      required=True,  help="Path to write results CSV")
    args = parser.parse_args()

    print(f"Loading dataset: {args.input}")
    all_rows, null_rows = load_dataset(args.input)

    print(f"Computing {args.growth_type} growth for: {args.ward} / {args.category}")
    try:
        results = compute_growth(all_rows, args.ward, args.category, args.growth_type)
    except (ValueError, LookupError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    fieldnames = ["period", "actual_spend", "growth_pct", "formula"]
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Done. {len(results)} rows written to {args.output}")

    # Print a quick preview table
    print(f"\n{'Period':<12} {'Actual Spend':>14} {'Growth':>12}  Formula")
    print("-" * 80)
    for row in results:
        print(
            f"{row['period']:<12} {row['actual_spend']:>14} {row['growth_pct']:>12}  {row['formula']}"
        )


if __name__ == "__main__":
    main()
