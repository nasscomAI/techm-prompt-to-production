"""UC-0C — Number That Looks Right

CLI utility to compute growth (MoM / YoY) for a single ward + category.
Enforcement rules from README.md are applied:
- refuse aggregation across wards/categories
- flag and report all NULL `actual_spend` rows (show `notes`)
- always show formula used in each output row
- require `--growth-type` to be provided

Usage example (see README.md):
  python app.py --input ../data/budget/ward_budget.csv \
    --ward "Ward 1 – Kasba" --category "Roads & Pothole Repair" \
    --growth-type MoM --output growth_output.csv
"""
from __future__ import annotations

import argparse
import csv
from typing import List, Optional, Dict, Any


REQUIRED_COLUMNS = ["period", "ward", "category", "budgeted_amount", "actual_spend", "notes"]


def load_dataset(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        for r in reader:
            period = r.get("period", "").strip()
            ward = r.get("ward", "").strip()
            category = r.get("category", "").strip()
            budgeted = r.get("budgeted_amount", "").strip()
            actual_raw = r.get("actual_spend", "").strip()
            notes = r.get("notes", "").strip()
            try:
                actual = float(actual_raw) if actual_raw != "" else None
            except Exception:
                actual = None
            rows.append({
                "period": period,
                "ward": ward,
                "category": category,
                "budgeted_amount": budgeted,
                "actual_spend": actual,
                "notes": notes,
            })
    return rows


def report_nulls(rows: List[Dict[str, Any]]) -> List[dict]:
    return [
        {"period": r["period"], "ward": r["ward"], "category": r["category"], "notes": r["notes"]}
        for r in rows
        if r["actual_spend"] is None
    ]


def refuse_aggregation(ward: str, category: str) -> None:
    lowered = f"{ward}".lower()
    if "all" in lowered or "*" in lowered:
        raise SystemExit("Refusing to aggregate across wards — provide a single ward.")
    cl = f"{category}".lower()
    if "all" in cl or "*" in cl:
        raise SystemExit("Refusing to aggregate across categories — provide a single category.")


def compute_growth(rows: List[Dict[str, Any]], ward: str, category: str, growth_type: str = "MoM") -> List[Dict[str, Any]]:
    subset = [r for r in rows if r["ward"] == ward and r["category"] == category]
    if not subset:
        raise SystemExit(f"No rows found for ward={ward!s} category={category!s}")
    # Sort by period YYYY-MM lexicographically
    subset = sorted(subset, key=lambda r: r["period"])
    out_rows: List[Dict[str, Any]] = []
    prev_value: Optional[float] = None
    for r in subset:
        period = r["period"]
        actual = r["actual_spend"]
        notes = r.get("notes", "") or ""
        row: Dict[str, Any] = {"period": period, "actual_spend": actual, "notes": "", "formula": "", "growth_percent": ""}

        if actual is None:
            row["notes"] = f"NULL — {notes}" if notes else "NULL"
            row["formula"] = "skipped (NULL actual_spend)"
            row["growth_percent"] = "NULL"
        else:
            if growth_type.upper() == "MOM":
                formula = "(current - previous) / previous * 100"
                row["formula"] = "MoM: " + formula
                if prev_value is None:
                    row["growth_percent"] = "N/A"
                else:
                    if prev_value == 0:
                        row["growth_percent"] = "DIV_BY_ZERO"
                    else:
                        val = (actual - prev_value) / prev_value * 100.0
                        row["growth_percent"] = f"{val:+.1f}%"
            elif growth_type.upper() == "YOY":
                row["formula"] = "YoY: (current - previous_year_same_month) / previous_year_same_month * 100"
                row["growth_percent"] = "UNSUPPORTED (data range)"
            else:
                raise SystemExit(f"Unsupported growth-type: {growth_type}")

        if actual is not None:
            prev_value = actual
        out_rows.append(row)
    return out_rows


def write_output(rows: List[Dict[str, Any]], out_path: str) -> None:
    fieldnames = ["period", "actual_spend", "notes", "formula", "growth_percent"]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fieldnames})


def main():
    p = argparse.ArgumentParser(description="UC-0C growth calculator — per-ward per-category only")
    p.add_argument("--input", required=True)
    p.add_argument("--ward", required=True)
    p.add_argument("--category", required=True)
    p.add_argument("--growth-type", required=True, help="MoM or YoY")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    # Enforcement: require growth-type
    if not args.growth_type:
        raise SystemExit("--growth-type is required; refuse to guess")

    refuse_aggregation(args.ward, args.category)

    df = load_dataset(args.input)
    nulls = report_nulls(df)
    if nulls:
        print(f"Found {len(nulls)} NULL actual_spend rows in dataset:")
        for r in nulls:
            print(f" - {r['period']} · {r['ward']} · {r['category']} — notes: {r['notes']}")
    else:
        print("No NULL actual_spend rows found.")

    result = compute_growth(df, args.ward, args.category, args.growth_type)
    # Show formula used once (all rows will include formula field per row). Print head for quick check.
    print("Writing output to:", args.output)
    write_output(result, args.output)
    print("Done. Sample output: ")
    # Print up to first 12 rows for a quick sample
    for r in result[:12]:
        print(f"{r['period']} | actual_spend={r['actual_spend']} | growth={r['growth_percent']} | {r['formula']} | notes={r['notes']}")


if __name__ == "__main__":
    main()
