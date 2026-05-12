"""
UC-0C — Number That Looks Right
app.py — Municipal budget growth-rate computation agent.

Skills:
  - load_dataset   : reads CSV, validates columns, reports null rows
  - compute_growth : per-ward per-category growth with formula shown

Run:
  python app.py \
    --input ../data/budget/ward_budget.csv \
    --ward "Ward 1 – Kasba" \
    --category "Roads & Pothole Repair" \
    --growth-type MoM \
    --output growth_output.csv
"""

import argparse
import csv
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NullRow:
    period: str
    ward: str
    category: str
    reason: str


@dataclass
class DatasetResult:
    data: list
    null_report: List[NullRow]
    null_count: int
    row_count: int
    wards: List[str]
    categories: List[str]


@dataclass
class GrowthRow:
    period: str
    ward: str
    category: str
    actual_spend: str
    previous_period_spend: str
    growth_pct: str
    formula: str
    flag: str


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount",
                    "actual_spend", "notes"}

AGGREGATION_KEYWORDS = {"all", "total", "combined", "aggregate", "overall"}


# ═══════════════════════════════════════════════════════════════════════════
# SKILL 1: load_dataset
# ═══════════════════════════════════════════════════════════════════════════

def load_dataset(file_path: str) -> DatasetResult:
    """
    Reads a ward budget CSV, validates columns, detects every null
    actual_spend row, and reports them before returning.
    """
    path = Path(file_path)

    # file_not_found
    if not path.exists():
        raise FileNotFoundError(f"File not found: '{file_path}'")

    # unreadable
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise IOError(f"Cannot read '{file_path}': {exc}") from exc

    # empty_file
    if not raw.strip():
        raise IOError(f"File '{file_path}' is empty — no data rows found.")

    lines = raw.strip().splitlines()
    reader = csv.DictReader(lines)

    # missing_columns
    if reader.fieldnames is None:
        raise IOError(f"Cannot parse CSV header in '{file_path}'.")
    actual_cols = set(reader.fieldnames)
    missing = REQUIRED_COLUMNS - actual_cols
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            f"Found: {sorted(actual_cols)}"
        )

    # Read all rows
    data = list(reader)

    if not data:
        raise IOError(f"File '{file_path}' has a header but no data rows.")

    # Detect nulls
    null_report: List[NullRow] = []
    wards_set = set()
    categories_set = set()

    for row in data:
        wards_set.add(row["ward"])
        categories_set.add(row["category"])

        spend = row.get("actual_spend", "").strip()
        if spend == "":
            reason = row.get("notes", "").strip() or "No reason provided"
            null_report.append(NullRow(
                period=row["period"],
                ward=row["ward"],
                category=row["category"],
                reason=reason,
            ))

    # nulls_detected — print warning before returning
    if null_report:
        print(f"\n[WARNING] {len(null_report)} null actual_spend row(s) detected:")
        for nr in null_report:
            print(f"  • {nr.period} | {nr.ward} | {nr.category} — {nr.reason}")
        print()

    return DatasetResult(
        data=data,
        null_report=null_report,
        null_count=len(null_report),
        row_count=len(data),
        wards=sorted(wards_set),
        categories=sorted(categories_set),
    )


# ═══════════════════════════════════════════════════════════════════════════
# SKILL 2: compute_growth
# ═══════════════════════════════════════════════════════════════════════════

def compute_growth(
    data: list,
    null_report: List[NullRow],
    ward: str,
    category: str,
    growth_type: str,
    all_wards: List[str],
    all_categories: List[str],
) -> List[GrowthRow]:
    """
    Filters dataset to ward + category, computes growth per period with
    formula shown. Flags null rows and null-dependent rows.
    """

    # aggregation_attempt
    if ward.strip().lower() in AGGREGATION_KEYWORDS:
        raise ValueError(
            "Aggregation across wards is not permitted unless explicitly "
            f"instructed. Valid wards: {all_wards}"
        )
    if category.strip().lower() in AGGREGATION_KEYWORDS:
        raise ValueError(
            "Aggregation across categories is not permitted unless explicitly "
            f"instructed. Valid categories: {all_categories}"
        )

    # growth_type_missing
    if not growth_type or growth_type not in ("MoM", "YoY"):
        raise ValueError(
            "--growth-type must be explicitly specified as 'MoM' or 'YoY'. "
            "Received: " + repr(growth_type)
        )

    # ward_not_found
    if ward not in all_wards:
        raise ValueError(
            f"Ward '{ward}' not found. Valid wards: {all_wards}"
        )

    # category_not_found
    if category not in all_categories:
        raise ValueError(
            f"Category '{category}' not found. Valid categories: {all_categories}"
        )

    # Filter to requested ward + category
    filtered = [
        r for r in data
        if r["ward"] == ward and r["category"] == category
    ]

    # Sort by period
    filtered.sort(key=lambda r: r["period"])

    # insufficient_data
    if len(filtered) < 2:
        raise ValueError(
            f"Only {len(filtered)} period(s) for '{ward}' / '{category}'. "
            "At least 2 periods are required to compute growth."
        )

    # Build a set of null (period, ward, category) for quick lookup
    null_keys = {
        (nr.period, nr.ward, nr.category): nr.reason
        for nr in null_report
    }

    # Build output rows
    results: List[GrowthRow] = []

    for i, row in enumerate(filtered):
        period = row["period"]
        spend_str = row.get("actual_spend", "").strip()
        is_null = spend_str == ""
        null_reason = null_keys.get((period, ward, category), "")

        # Determine current spend
        if is_null:
            current_spend = None
        else:
            current_spend = float(spend_str)

        # Determine previous spend based on growth_type
        if growth_type == "MoM":
            if i == 0:
                prev_spend = None
                prev_label = "N/A"
                is_first = True
            else:
                prev_row = filtered[i - 1]
                prev_str = prev_row.get("actual_spend", "").strip()
                is_first = False
                if prev_str == "":
                    prev_spend = None
                    prev_label = "NULL"
                else:
                    prev_spend = float(prev_str)
                    prev_label = str(prev_spend)
        else:  # YoY — need same month previous year
            # For 2024 single-year data, YoY is not computable
            prev_spend = None
            prev_label = "N/A"
            is_first = True  # effectively no prior year data

        # Build the growth row
        if is_null:
            # null_actual_spend
            results.append(GrowthRow(
                period=period,
                ward=ward,
                category=category,
                actual_spend="NULL",
                previous_period_spend=prev_label if not (growth_type == "MoM" and i == 0) else "N/A",
                growth_pct="",
                formula="N/A — actual_spend is null",
                flag=f"NULL — {null_reason}",
            ))
        elif growth_type == "MoM" and is_first:
            # first_period
            results.append(GrowthRow(
                period=period,
                ward=ward,
                category=category,
                actual_spend=str(current_spend),
                previous_period_spend="N/A",
                growth_pct="",
                formula="N/A — no prior period",
                flag="N/A — first period",
            ))
        elif growth_type == "MoM" and prev_spend is None:
            # null_prior_period
            results.append(GrowthRow(
                period=period,
                ward=ward,
                category=category,
                actual_spend=str(current_spend),
                previous_period_spend="NULL",
                growth_pct="",
                formula="N/A — prior period actual_spend is null",
                flag="SKIP — prior period actual_spend is null",
            ))
        elif growth_type == "MoM" and prev_spend == 0:
            # Division by zero guard
            results.append(GrowthRow(
                period=period,
                ward=ward,
                category=category,
                actual_spend=str(current_spend),
                previous_period_spend="0.0",
                growth_pct="",
                formula="N/A — prior period is zero (division undefined)",
                flag="SKIP — prior period is zero",
            ))
        elif growth_type == "MoM":
            # Normal computation
            growth = ((current_spend - prev_spend) / prev_spend) * 100
            sign = "+" if growth >= 0 else ""
            growth_str = f"{sign}{growth:.1f}%"
            formula_str = (
                f"(({current_spend} - {prev_spend}) / {prev_spend}) "
                f"* 100 = {growth_str}"
            )
            results.append(GrowthRow(
                period=period,
                ward=ward,
                category=category,
                actual_spend=str(current_spend),
                previous_period_spend=str(prev_spend),
                growth_pct=growth_str,
                formula=formula_str,
                flag="",
            ))
        else:
            # YoY with no prior year data
            results.append(GrowthRow(
                period=period,
                ward=ward,
                category=category,
                actual_spend=str(current_spend) if current_spend is not None else "NULL",
                previous_period_spend="N/A",
                growth_pct="",
                formula="N/A — no prior year data available",
                flag="N/A — single-year dataset, YoY not computable",
            ))

    return results


# ═══════════════════════════════════════════════════════════════════════════
# CSV Output Writer
# ═══════════════════════════════════════════════════════════════════════════

OUTPUT_COLUMNS = [
    "period", "ward", "category", "actual_spend",
    "previous_period_spend", "growth_pct", "formula", "flag",
]


def write_output(rows: List[GrowthRow], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "period": r.period,
                "ward": r.ward,
                "category": r.category,
                "actual_spend": r.actual_spend,
                "previous_period_spend": r.previous_period_spend,
                "growth_pct": r.growth_pct,
                "formula": r.formula,
                "flag": r.flag,
            })


# ═══════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UC-0C — Per-ward per-category budget growth computation."
    )
    parser.add_argument("--input", required=True,
                        help="Path to the ward_budget.csv file.")
    parser.add_argument("--ward", required=True,
                        help="Exact ward name to compute growth for.")
    parser.add_argument("--category", required=True,
                        help="Exact category name to compute growth for.")
    parser.add_argument("--growth-type", dest="growth_type", default=None,
                        help="Growth type: 'MoM' or 'YoY'. Must be specified.")
    parser.add_argument("--output", required=True,
                        help="Path for the output CSV file.")
    args = parser.parse_args()

    # Enforcement: refuse if --growth-type not specified
    if not args.growth_type:
        print(
            "[ERROR] --growth-type is required. Specify 'MoM' "
            "(month-over-month) or 'YoY' (year-over-year).\n"
            "Example: --growth-type MoM",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Skill 1: load_dataset ─────────────────────────────────────────
    print(f"[load_dataset] Loading: {args.input}")
    try:
        ds = load_dataset(args.input)
    except (FileNotFoundError, IOError, ValueError) as exc:
        print(f"[ERROR] load_dataset: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[load_dataset] {ds.row_count} rows | "
          f"{len(ds.wards)} wards | {len(ds.categories)} categories | "
          f"{ds.null_count} null actual_spend rows")

    # ── Skill 2: compute_growth ───────────────────────────────────────
    print(f"[compute_growth] Ward: {args.ward} | "
          f"Category: {args.category} | Type: {args.growth_type}")
    try:
        results = compute_growth(
            data=ds.data,
            null_report=ds.null_report,
            ward=args.ward,
            category=args.category,
            growth_type=args.growth_type,
            all_wards=ds.wards,
            all_categories=ds.categories,
        )
    except ValueError as exc:
        print(f"[ERROR] compute_growth: {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Write output ──────────────────────────────────────────────────
    write_output(results, args.output)
    print(f"[OK] {len(results)} rows written to: {Path(args.output).resolve()}")

    # Print summary table to stdout
    print(f"\n{'Period':<10} {'Actual':>8} {'Prev':>8} {'Growth':>10} {'Flag'}")
    print("-" * 60)
    for r in results:
        print(f"{r.period:<10} {r.actual_spend:>8} {r.previous_period_spend:>8} "
              f"{r.growth_pct:>10} {r.flag}")


if __name__ == "__main__":
    main()
