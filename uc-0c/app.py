"""
UC-0C — Number That Looks Right
app.py — Municipal Budget Growth Analysis Agent

Implements:
  - load_dataset skill  (skills.md)
  - compute_growth skill (skills.md)
  - All enforcement rules from agents.md
"""

import argparse
import csv
import os
import sys
from typing import Optional

# ── CONSTANTS ────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}
VALID_GROWTH_TYPES = {"MoM", "YoY"}

# Aggregation-trigger words — any ward/category matching these is refused
AGGREGATION_WILDCARDS = {"all", "any", "*", "every", "total", "aggregate"}


# ── SKILL: load_dataset ───────────────────────────────────────────────────────

def load_dataset(file_path: str) -> dict:
    """
    Reads the ward_budget CSV, validates all required columns are present,
    and reports the total null count and every null row (with reason) before
    returning the dataset.

    Returns:
        {
            "data": list of row dicts,
            "null_report": list of {period, ward, category, null_reason},
            "null_count": int,
            "row_count": int
        }

    Halts (sys.exit) on: missing file, missing columns, empty file.
    """

    # ── error: missing file
    if not os.path.exists(file_path):
        print(f"[ERROR] load_dataset: File not found — '{file_path}'", file=sys.stderr)
        print("        Verify the --input path and try again.", file=sys.stderr)
        sys.exit(1)

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_columns = set(reader.fieldnames or [])

        # ── error: missing columns
        missing = REQUIRED_COLUMNS - raw_columns
        if missing:
            print("[ERROR] load_dataset: Schema validation failed.", file=sys.stderr)
            print(f"        Missing column(s): {', '.join(sorted(missing))}", file=sys.stderr)
            print(f"        Expected: {', '.join(sorted(REQUIRED_COLUMNS))}", file=sys.stderr)
            sys.exit(1)

        rows = list(reader)

    # ── error: empty file
    if len(rows) == 0:
        print("[ERROR] load_dataset: The CSV file contains zero data rows.", file=sys.stderr)
        print("        This is anomalous — verify the input file is not empty.", file=sys.stderr)
        sys.exit(1)

    # ── null detection — must run before returning data
    null_report = []
    for row in rows:
        spend = row.get("actual_spend", "").strip()
        if spend == "" or spend.lower() == "null":
            null_reason = row.get("notes", "").strip()
            if not null_reason:
                null_reason = "no reason provided"
                row["_operator_review"] = True  # flag for operator review
            null_report.append({
                "period":      row["period"].strip(),
                "ward":        row["ward"].strip(),
                "category":    row["category"].strip(),
                "null_reason": null_reason,
            })

    # ── print null report to stdout before any computation
    print("=" * 60)
    print("LOAD DATASET — NULL REPORT")
    print("=" * 60)
    print(f"Total rows      : {len(rows)}")
    print(f"Null actual_spend: {len(null_report)}")
    print()
    if null_report:
        print("Flagged rows (must not be computed):")
        for i, nr in enumerate(null_report, 1):
            flag = "  ⚠ operator review required" if nr["null_reason"] == "no reason provided" else ""
            print(f"  {i}. {nr['period']} | {nr['ward']} | {nr['category']}")
            print(f"     Reason: {nr['null_reason']}{flag}")
    else:
        print("  No null rows found.")
    print("=" * 60)
    print()

    return {
        "data":        rows,
        "null_report": null_report,
        "null_count":  len(null_report),
        "row_count":   len(rows),
    }


# ── SKILL: compute_growth ─────────────────────────────────────────────────────

def compute_growth(data: list, ward: str, category: str, growth_type: str) -> dict:
    """
    Computes per-period growth for a single ward + category combination.
    Prints formula alongside every computed row.
    Flags null rows — never interpolates, zeroes, or skips them.

    Returns:
        {
            "ward": str,
            "category": str,
            "growth_type": str,
            "rows": list of row dicts
        }

    Halts (sys.exit) on: missing/invalid growth_type, unrecognised ward/category,
    aggregation attempt, insufficient non-null periods.
    """

    # ── enforcement: growth_type must be explicit
    if not growth_type or growth_type not in VALID_GROWTH_TYPES:
        print("[ERROR] compute_growth: --growth-type was not specified or is invalid.",
              file=sys.stderr)
        print(f"        Received: '{growth_type}'", file=sys.stderr)
        print("        Please specify --growth-type MoM  or  --growth-type YoY",
              file=sys.stderr)
        print("        This agent never guesses the growth type.", file=sys.stderr)
        sys.exit(1)

    # ── enforcement: refuse aggregation wildcards
    if ward.lower().strip() in AGGREGATION_WILDCARDS or \
       category.lower().strip() in AGGREGATION_WILDCARDS:
        print("[ERROR] compute_growth: Cross-ward or cross-category aggregation is not permitted.",
              file=sys.stderr)
        print("        --ward and --category must each identify a single, specific value.",
              file=sys.stderr)
        print("        Returning a combined figure for all wards/categories is a critical failure.",
              file=sys.stderr)
        sys.exit(1)

    # ── collect known wards and categories for helpful errors
    known_wards      = sorted({r["ward"].strip() for r in data})
    known_categories = sorted({r["category"].strip() for r in data})

    # ── enforcement: ward must exist exactly
    if ward not in known_wards:
        print(f"[ERROR] compute_growth: Ward '{ward}' not found in dataset.", file=sys.stderr)
        print("        Valid wards:", file=sys.stderr)
        for w in known_wards:
            print(f"          • {w}", file=sys.stderr)
        print("        Fuzzy or partial matching is not permitted.", file=sys.stderr)
        sys.exit(1)

    # ── enforcement: category must exist exactly
    if category not in known_categories:
        print(f"[ERROR] compute_growth: Category '{category}' not found in dataset.",
              file=sys.stderr)
        print("        Valid categories:", file=sys.stderr)
        for c in known_categories:
            print(f"          • {c}", file=sys.stderr)
        print("        Fuzzy or partial matching is not permitted.", file=sys.stderr)
        sys.exit(1)

    # ── filter to single ward + category, sorted by period
    subset = [
        r for r in data
        if r["ward"].strip() == ward and r["category"].strip() == category
    ]
    subset.sort(key=lambda r: r["period"].strip())

    # ── enforcement: insufficient non-null periods
    non_null_periods = [
        r for r in subset
        if r.get("actual_spend", "").strip() not in ("", "null", "NULL")
    ]
    if len(non_null_periods) < 2:
        print("[ERROR] compute_growth: Fewer than two non-null periods found for "
              f"'{ward}' / '{category}'.", file=sys.stderr)
        print("        Growth cannot be computed with fewer than two data points.",
              file=sys.stderr)
        sys.exit(1)

    # ── build output rows
    output_rows = []

    def parse_spend(raw: str) -> Optional[float]:
        s = raw.strip()
        if s == "" or s.lower() == "null":
            return None
        try:
            return float(s)
        except ValueError:
            return None

    def is_null_row(row: dict) -> bool:
        return parse_spend(row.get("actual_spend", "")) is None

    for i, row in enumerate(subset):
        period   = row["period"].strip()
        raw_ward = row["ward"].strip()
        raw_cat  = row["category"].strip()
        spend    = parse_spend(row.get("actual_spend", ""))
        notes    = row.get("notes", "").strip()

        # ── current row is null — flag, never compute
        if spend is None:
            null_reason = notes if notes else "no reason provided"
            output_rows.append({
                "period":       period,
                "ward":         raw_ward,
                "category":     raw_cat,
                "actual_spend": None,
                "growth_value": None,
                "formula_used": None,
                "null_flag":    True,
                "null_reason":  null_reason,
            })
            continue

        # ── determine lookback index based on growth_type
        if growth_type == "MoM":
            lookback = 1
        else:  # YoY
            lookback = 12

        prev_spend = None
        prior_is_null = False

        if i >= lookback:
            prev_row   = subset[i - lookback]
            prev_spend = parse_spend(prev_row.get("actual_spend", ""))
            if prev_spend is None:
                prior_is_null = True

        # ── prior period is null — cannot compute this row either
        if prior_is_null:
            output_rows.append({
                "period":       period,
                "ward":         raw_ward,
                "category":     raw_cat,
                "actual_spend": spend,
                "growth_value": None,
                "formula_used": None,
                "null_flag":    True,
                "null_reason":  "prior period is null",
            })
            continue

        # ── first period or lookback not available — no prior to compare
        if prev_spend is None:
            output_rows.append({
                "period":       period,
                "ward":         raw_ward,
                "category":     raw_cat,
                "actual_spend": spend,
                "growth_value": None,
                "formula_used": None,
                "null_flag":    False,
                "null_reason":  f"no prior {growth_type} period available",
            })
            continue

        # ── enforcement: formula must be shown alongside every computed value
        growth_value = (spend - prev_spend) / prev_spend * 100
        formula_used = f"({spend} - {prev_spend}) / {prev_spend} * 100"

        output_rows.append({
            "period":       period,
            "ward":         raw_ward,
            "category":     raw_cat,
            "actual_spend": spend,
            "growth_value": round(growth_value, 1),
            "formula_used": formula_used,
            "null_flag":    False,
            "null_reason":  None,
        })

    return {
        "ward":        ward,
        "category":    category,
        "growth_type": growth_type,
        "rows":        output_rows,
    }


# ── OUTPUT WRITER ─────────────────────────────────────────────────────────────

def write_output(result: dict, output_path: str) -> None:
    """
    Writes the compute_growth result to a CSV file.
    Every row includes period, ward, category, actual_spend,
    growth_value, formula_used, null_flag, null_reason.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    fieldnames = [
        "period", "ward", "category", "actual_spend",
        "growth_value", "formula_used", "null_flag", "null_reason",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({
                "period":       row["period"],
                "ward":         row["ward"],
                "category":     row["category"],
                "actual_spend": "" if row["actual_spend"] is None else row["actual_spend"],
                "growth_value": "" if row["growth_value"] is None else row["growth_value"],
                "formula_used": "" if row["formula_used"] is None else row["formula_used"],
                "null_flag":    row["null_flag"],
                "null_reason":  "" if row["null_reason"] is None else row["null_reason"],
            })

    print(f"[OK] Output written → {output_path}")
    print(f"     Rows: {len(result['rows'])} "
          f"| Computed: {sum(1 for r in result['rows'] if not r['null_flag'] and r['growth_value'] is not None)} "
          f"| Flagged null: {sum(1 for r in result['rows'] if r['null_flag'])}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Normalize dashes and whitespace for loose matching."""
    return text.replace("\u2013", "-").replace("\u2014", "-").strip().lower()


def resolve_ward(input_ward: str, known_wards: list) -> str:
    """
    Match user-supplied ward string against known wards by normalizing
    em dashes to hyphens. Returns the exact CSV ward string or exits.
    """
    for w in known_wards:
        if normalize(w) == normalize(input_ward):
            return w
    print(f"[ERROR] Ward '{input_ward}' not found even after dash normalization.", file=sys.stderr)
    print("        Valid wards:", file=sys.stderr)
    for w in known_wards:
        print(f"          • {w}", file=sys.stderr)
    print("\n        TIP: Run with --list-wards to print exact ward names from your CSV.",
          file=sys.stderr)
    sys.exit(1)


def resolve_category(input_cat: str, known_cats: list) -> str:
    """Match user-supplied category against known categories after normalization."""
    for c in known_cats:
        if normalize(c) == normalize(input_cat):
            return c
    print(f"[ERROR] Category '{input_cat}' not found.", file=sys.stderr)
    print("        Valid categories:", file=sys.stderr)
    for c in known_cats:
        print(f"          • {c}", file=sys.stderr)
    print("\n        TIP: Run with --list-wards to print exact values from your CSV.",
          file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="UC-0C Municipal Budget Growth Analysis Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python app.py \\
    --input ../data/budget/ward_budget.csv \\
    --ward "Ward 1 - Kasba" \\
    --category "Roads & Pothole Repair" \\
    --growth-type MoM \\
    --output growth_output.csv

List valid ward and category names:
  python app.py --input ../data/budget/ward_budget.csv --list-wards
        """
    )
    parser.add_argument("--input",       required=True,  help="Path to ward_budget.csv")
    parser.add_argument("--ward",        default=None,   help="Ward name (hyphen or em dash both work)")
    parser.add_argument("--category",    default=None,   help="Exact category name")
    parser.add_argument("--growth-type", dest="growth_type", default=None,
                        help="MoM or YoY (required — agent will refuse if omitted)")
    parser.add_argument("--output",      default=None,   help="Path for output CSV")
    parser.add_argument("--list-wards",  dest="list_wards", action="store_true",
                        help="Print all ward and category names from the CSV and exit")
    return parser.parse_args()


def main():
    args = parse_args()

    # ── --list-wards: print exact names from CSV and exit
    if args.list_wards:
        if not os.path.exists(args.input):
            print(f"[ERROR] File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        wards = sorted({r["ward"].strip() for r in rows})
        cats  = sorted({r["category"].strip() for r in rows})
        print("\nWards in CSV:")
        for w in wards:
            print(f"  • {w}")
        print("\nCategories in CSV:")
        for c in cats:
            print(f"  • {c}")
        print("\nCopy any value above exactly into your --ward or --category argument.")
        sys.exit(0)

    # ── validate required args for normal run
    if not args.ward or not args.category or not args.output:
        print("[ERROR] --ward, --category, and --output are required.", file=sys.stderr)
        print("        Run with --list-wards to see valid ward and category names.",
              file=sys.stderr)
        sys.exit(1)

    # ── enforcement: --growth-type must be explicit; never guess
    if args.growth_type is None:
        print("[ERROR] --growth-type was not specified.", file=sys.stderr)
        print("        This agent never guesses the growth type.", file=sys.stderr)
        print("        Please re-run with --growth-type MoM  or  --growth-type YoY",
              file=sys.stderr)
        sys.exit(1)

    # ── SKILL 1: load_dataset (null report printed before any computation)
    dataset = load_dataset(args.input)

    # ── resolve ward and category with dash normalization
    known_wards = sorted({r["ward"].strip() for r in dataset["data"]})
    known_cats  = sorted({r["category"].strip() for r in dataset["data"]})
    resolved_ward     = resolve_ward(args.ward, known_wards)
    resolved_category = resolve_category(args.category, known_cats)

    # ── SKILL 2: compute_growth (single ward, single category)
    result = compute_growth(
        data=dataset["data"],
        ward=resolved_ward,
        category=resolved_category,
        growth_type=args.growth_type,
    )

    # ── write output
    write_output(result, args.output)


if __name__ == "__main__":
    main()