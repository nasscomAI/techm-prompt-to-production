"""
UC-0C — Number That Looks Right
Budget Growth Computation Agent

Implements the two skills defined in skills.md:
  - load_dataset   : reads ward_budget.csv, validates columns, reports nulls
  - compute_growth : per-ward per-category MoM or YoY growth table with formula

Enforcement rules from agents.md:
  1. Never aggregate across wards/categories without explicit instruction — REFUSE
  2. Flag every null row before computing — report reason from notes column
  3. Show formula used in every output row alongside the result
  4. If --growth-type not specified — REFUSE and ask, never guess

Run:
    python app.py \\
      --input ../data/budget/ward_budget.csv \\
      --ward "Ward 1 - Kasba" \\
      --category "Roads & Pothole Repair" \\
      --growth-type MoM \\
      --output growth_output.csv
"""

import argparse
import csv
import os
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}

VALID_GROWTH_TYPES = {"MoM", "YoY"}

# Reference values from README — used for post-compute validation
REFERENCE_CHECKS = [
    {
        "ward": "Ward 1",          # partial match key
        "category": "Roads",       # partial match key
        "period": "2024-07",
        "growth_type": "MoM",
        "expected_pct": 33.1,
        "label": "Ward 1 Kasba / Roads & Pothole Repair / 2024-07 (monsoon spike)",
    },
    {
        "ward": "Ward 1",
        "category": "Roads",
        "period": "2024-10",
        "growth_type": "MoM",
        "expected_pct": -34.8,
        "label": "Ward 1 Kasba / Roads & Pothole Repair / 2024-10 (post-monsoon)",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Skill 1: load_dataset
# ─────────────────────────────────────────────────────────────────────────────

def load_dataset(file_path: str) -> list:
    """
    Reads the ward budget CSV, validates that required columns are present,
    reports the count and identity of every null actual_spend row before
    returning the full dataset.

    Returns:
        list of dicts — one per row, with actual_spend as float or None.

    Raises:
        FileNotFoundError — file path does not exist
        ValueError        — required columns are missing or file is empty
    """
    resolved = str(Path(file_path).resolve())
    if not Path(file_path).exists():
        raise FileNotFoundError(
            f"load_dataset: file not found at resolved path: {resolved}"
        )

    with open(file_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("load_dataset: file appears to be empty — no header row found.")

        actual_cols = {c.strip() for c in reader.fieldnames}
        missing_cols = REQUIRED_COLUMNS - actual_cols
        if missing_cols:
            raise ValueError(
                f"load_dataset: required columns missing from CSV: {sorted(missing_cols)}"
            )

        rows = []
        for raw in reader:
            row = {k.strip(): v.strip() if v else "" for k, v in raw.items()}
            # Parse actual_spend — blank becomes None
            spend_raw = row.get("actual_spend", "")
            row["actual_spend"] = float(spend_raw) if spend_raw else None
            # Parse budgeted_amount
            budget_raw = row.get("budgeted_amount", "")
            row["budgeted_amount"] = float(budget_raw) if budget_raw else None
            rows.append(row)

    if not rows:
        raise ValueError("load_dataset: the CSV contains no data rows.")

    # Report nulls before returning (enforcement rule 2)
    null_rows = [r for r in rows if r["actual_spend"] is None]
    if null_rows:
        print(f"\n[load_dataset] WARNING: {len(null_rows)} null actual_spend row(s) detected:")
        for nr in null_rows:
            reason = nr.get("notes") or "no reason provided"
            print(f"  NULL: {nr['period']} | {nr['ward']} | {nr['category']} | Reason: {reason}")
        print()

    print(f"[load_dataset] Loaded {len(rows)} rows ({len(null_rows)} null).\n")
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Skill 2: compute_growth
# ─────────────────────────────────────────────────────────────────────────────

def compute_growth(rows: list, ward: str, category: str, growth_type: str) -> list:
    """
    Filters the dataset to the specified ward + category slice, then computes
    MoM or YoY growth for each period. Every output row includes the formula
    string used to derive the result. Null rows are flagged — not computed.

    Returns:
        list of output dicts with keys:
            period, ward, category, actual_spend, growth_pct, formula, null_flag, null_reason

    Raises:
        ValueError — growth_type not in {MoM, YoY}
        ValueError — no data found for the specified ward + category
    """
    if growth_type not in VALID_GROWTH_TYPES:
        raise ValueError(
            f"compute_growth: growth_type must be one of {VALID_GROWTH_TYPES}, "
            f"got '{growth_type}'. REFUSING — please specify --growth-type explicitly."
        )

    # Filter to the requested ward + category slice
    slice_rows = [
        r for r in rows
        if r["ward"].strip() == ward.strip() and r["category"].strip() == category.strip()
    ]

    if not slice_rows:
        raise ValueError(
            f"compute_growth: no data found for ward='{ward}', category='{category}'. "
            "Check spelling exactly as it appears in the CSV."
        )

    # Sort by period chronologically
    slice_rows.sort(key=lambda r: r["period"])

    results = []

    for i, row in enumerate(slice_rows):
        period = row["period"]
        actual = row["actual_spend"]
        null_reason = row.get("notes", "") if actual is None else ""

        if actual is None:
            # Enforcement rule 2: flag null rows — do not compute
            results.append({
                "period": period,
                "ward": row["ward"],
                "category": row["category"],
                "actual_spend": "NULL",
                "growth_pct": "NULL — not computed",
                "formula": "NULL — not computed",
                "null_flag": "TRUE",
                "null_reason": null_reason or "no reason provided",
            })
            continue

        # Determine the reference period and value for the chosen growth type
        prev_actual = None
        prev_period = None

        if growth_type == "MoM":
            if i == 0:
                prev_actual = None
                prev_period = None
            else:
                prev_row = slice_rows[i - 1]
                prev_actual = prev_row["actual_spend"]
                prev_period = prev_row["period"]

        elif growth_type == "YoY":
            # Find same month, prior year
            year, month = period.split("-")
            target_period = f"{int(year) - 1}-{month}"
            prior = next(
                (r for r in slice_rows if r["period"] == target_period), None
            )
            if prior:
                prev_actual = prior["actual_spend"]
                prev_period = target_period
            else:
                prev_actual = None
                prev_period = None

        # Compute growth if we have a valid prior value
        if prev_actual is None:
            growth_pct = "N/A — no prior period"
            formula_str = f"N/A — no prior period ({growth_type})"
        elif prev_actual == 0:
            growth_pct = "N/A — prior period is zero (division undefined)"
            formula_str = f"{growth_type} = ({actual} - 0) / 0 * 100 [undefined]"
        else:
            pct = round(((actual - prev_actual) / prev_actual) * 100, 1)
            growth_pct = f"{'+' if pct >= 0 else ''}{pct}%"
            formula_str = (
                f"{growth_type} = ({actual} - {prev_actual}) / {prev_actual} * 100 "
                f"= {'+' if pct >= 0 else ''}{pct}%"
            )

        results.append({
            "period": period,
            "ward": row["ward"],
            "category": row["category"],
            "actual_spend": actual,
            "growth_pct": growth_pct,
            "formula": formula_str,
            "null_flag": "FALSE",
            "null_reason": "",
        })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Reference value validation (agents.md enforcement)
# ─────────────────────────────────────────────────────────────────────────────

def validate_reference_values(results: list, ward: str, category: str, growth_type: str):
    """
    Checks computed results against the reference values specified in the README.
    Prints a warning if any reference value does not match, but does not abort —
    the mismatch is surfaced as a data quality issue for the user.
    """
    for ref in REFERENCE_CHECKS:
        if growth_type != ref["growth_type"]:
            continue
        if ref["ward"].lower() not in ward.lower():
            continue
        if ref["category"].lower() not in category.lower():
            continue

        match = next((r for r in results if r["period"] == ref["period"]), None)
        if match is None:
            print(
                f"[VALIDATION WARNING] Reference period {ref['period']} not found in results "
                f"for {ref['label']}."
            )
            continue

        if match["null_flag"] == "TRUE":
            print(
                f"[VALIDATION WARNING] {ref['label']}: row is flagged NULL — "
                "cannot verify reference value."
            )
            continue

        actual_pct_str = match["growth_pct"].replace("%", "").replace("+", "")
        try:
            actual_pct = float(actual_pct_str)
            if abs(actual_pct - ref["expected_pct"]) > 0.15:  # tolerance: 0.15pp
                print(
                    f"[VALIDATION WARNING] {ref['label']}: "
                    f"expected {ref['expected_pct']}%, got {match['growth_pct']}. "
                    "Possible formula or aggregation error."
                )
            else:
                print(f"[VALIDATION OK] {ref['label']}: {match['growth_pct']} (matches reference)")
        except ValueError:
            pass  # growth_pct is N/A string — skip numeric check


# ─────────────────────────────────────────────────────────────────────────────
# Output writer
# ─────────────────────────────────────────────────────────────────────────────

def write_output(results: list, output_path: str):
    """
    Writes the growth computation results to a CSV file.

    Raises:
        FileNotFoundError — output directory does not exist
    """
    out_dir = Path(output_path).parent
    if str(out_dir) != "." and not out_dir.exists():
        raise FileNotFoundError(
            f"write_output: output directory does not exist: {out_dir.resolve()}"
        )

    fieldnames = ["period", "ward", "category", "actual_spend",
                  "growth_pct", "formula", "null_flag", "null_reason"]

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[write_output] Results written to: {output_path}")
    print(f"[write_output] Rows written: {len(results)}")
    null_count = sum(1 for r in results if r["null_flag"] == "TRUE")
    if null_count:
        print(f"[write_output] Null rows flagged (not computed): {null_count}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "UC-0C — Budget Growth Computation Agent\n"
            "Computes MoM or YoY growth for a specified ward + category.\n\n"
            "Enforcement (agents.md):\n"
            "  - Never aggregates across wards/categories without explicit instruction\n"
            "  - Flags every null row before computing (with reason from notes column)\n"
            "  - Shows formula in every output row\n"
            "  - REFUSES if --growth-type is not specified"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to ward_budget.csv (e.g. ../data/budget/ward_budget.csv)"
    )
    parser.add_argument(
        "--ward", required=True,
        help='Ward name exactly as in CSV (e.g. "Ward 1 - Kasba")'
    )
    parser.add_argument(
        "--category", required=True,
        help='Category name exactly as in CSV (e.g. "Roads & Pothole Repair")'
    )
    parser.add_argument(
        "--growth-type", dest="growth_type", default=None,
        choices=list(VALID_GROWTH_TYPES),
        help="Growth type: MoM (month-on-month) or YoY (year-on-year). REQUIRED."
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to write the output CSV (e.g. growth_output.csv)"
    )

    args = parser.parse_args()

    # Enforcement rule 4: REFUSE if --growth-type not provided
    if args.growth_type is None:
        print(
            "[ERROR] --growth-type is required. REFUSING to proceed.\n"
            "Please specify --growth-type MoM or --growth-type YoY.\n"
            "Guessing a growth type is not permitted (agents.md enforcement rule 4).",
            file=sys.stderr,
        )
        sys.exit(4)

    # ── Skill 1: load_dataset ─────────────────────────────────────────────────
    try:
        rows = load_dataset(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Skill 2: compute_growth ───────────────────────────────────────────────
    try:
        results = compute_growth(rows, args.ward, args.category, args.growth_type)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(2)

    # Print summary to console
    print(f"[compute_growth] Computed {args.growth_type} growth for:")
    print(f"  Ward    : {args.ward}")
    print(f"  Category: {args.category}")
    print(f"  Periods : {len(results)}")
    print()
    print(f"  {'Period':<10} {'Actual Spend':>13} {'Growth':>12}  Formula")
    print(f"  {'-'*10} {'-'*13} {'-'*12}  {'-'*45}")
    for r in results:
        spend_str = str(r["actual_spend"])
        print(
            f"  {r['period']:<10} {spend_str:>13} {str(r['growth_pct']):>12}  {r['formula']}"
        )
    print()

    # ── Reference value validation ────────────────────────────────────────────
    validate_reference_values(results, args.ward, args.category, args.growth_type)

    # ── Write output CSV ──────────────────────────────────────────────────────
    try:
        write_output(results, args.output)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
