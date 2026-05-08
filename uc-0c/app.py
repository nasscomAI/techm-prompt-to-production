"""
UC-0C — Number That Looks Right
Implements: load_dataset + compute_growth skills
Enforces: every rule in agents.md (RICE framework)

Run:
  python app.py --input ../data/budget/ward_budget.csv \
    --ward "Ward 1 – Kasba" \
    --category "Roads & Pothole Repair" \
    --growth-type MoM \
    --output growth_output.csv
"""
import argparse
import csv
import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Required CSV columns (agents.md — context block)
# ─────────────────────────────────────────────────────────────────────────────
REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Allowed growth types — never guess (agents.md rule 4)
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_GROWTH_TYPES = {"MoM", "YoY"}


# ─────────────────────────────────────────────────────────────────────────────
# SKILL: load_dataset
# ─────────────────────────────────────────────────────────────────────────────
def load_dataset(file_path: str) -> dict:
    """
    Read ward_budget.csv, validate columns, census null actual_spend rows.

    Enforcement:
      - Missing file → error + exit
      - Missing columns → error + exit
      - Null rows surfaced BEFORE any computation (agents.md rule 2)
      - Non-numeric actual_spend treated as null

    Returns: { records: [...], null_rows: [...] }
    """
    if not os.path.exists(file_path):
        print(f"ERROR: Input file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = set(fn.strip() for fn in (reader.fieldnames or []))

        missing_cols = REQUIRED_COLUMNS - fieldnames
        if missing_cols:
            print(
                f"ERROR: Missing required columns: {sorted(missing_cols)}\n"
                f"       Found columns: {sorted(fieldnames)}",
                file=sys.stderr,
            )
            sys.exit(1)

        raw_rows = list(reader)

    if not raw_rows:
        print("ERROR: Dataset is empty after header.", file=sys.stderr)
        sys.exit(1)

    records  = []
    null_rows = []

    for row in raw_rows:
        period   = row["period"].strip()
        ward     = row["ward"].strip()
        category = row["category"].strip()
        notes    = row["notes"].strip()
        raw_spend = row["actual_spend"].strip()

        # Parse actual_spend — treat blank or non-numeric as null
        actual_spend = None
        null_reason  = ""
        if raw_spend == "":
            null_reason = notes if notes else "No reason provided"
        else:
            try:
                actual_spend = float(raw_spend)
            except ValueError:
                null_reason = f"Non-numeric value: {raw_spend}"

        record = {
            "period":           period,
            "ward":             ward,
            "category":         category,
            "budgeted_amount":  row["budgeted_amount"].strip(),
            "actual_spend":     actual_spend,
            "notes":            notes,
        }
        records.append(record)

        if actual_spend is None:
            null_rows.append({
                "period":    period,
                "ward":      ward,
                "category":  category,
                "null_reason": null_reason,
            })

    return {"records": records, "null_rows": null_rows}


# ─────────────────────────────────────────────────────────────────────────────
# SKILL: compute_growth
# ─────────────────────────────────────────────────────────────────────────────
def compute_growth(
    records: list,
    null_rows: list,
    ward: str,
    category: str,
    growth_type: str,
    output_path: str,
) -> None:
    """
    Compute per-period growth for a specific ward + category + growth_type.

    Enforcement rules applied (from agents.md):
      1. Refuse cross-ward/cross-category aggregation.
      2. Flag null rows BEFORE computation.
      3. Show formula used in every output row.
      4. Refuse if growth_type not MoM or YoY.
      5. Output is per-ward per-category table, never a single number.
      6. Error if ward or category not found.
      7. First period → N/A (no prior period).
    """
    # ── Enforcement rule 4: validate growth_type ──────────────────────────────
    if growth_type not in ALLOWED_GROWTH_TYPES:
        print(
            "ERROR: Growth type not specified or invalid.\n"
            "Please provide --growth-type MoM or --growth-type YoY. Do not guess.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Enforcement rule 6: validate ward and category exist ──────────────────
    all_wards      = sorted(set(r["ward"] for r in records))
    all_categories = sorted(set(r["category"] for r in records))

    if ward not in all_wards:
        print(
            f"ERROR: Ward '{ward}' not found in dataset.\n"
            f"Valid wards: {all_wards}",
            file=sys.stderr,
        )
        sys.exit(1)

    if category not in all_categories:
        print(
            f"ERROR: Category '{category}' not found in dataset.\n"
            f"Valid categories: {all_categories}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Filter to ward + category (enforcement rule 1 & 5) ────────────────────
    filtered = [
        r for r in records
        if r["ward"] == ward and r["category"] == category
    ]
    filtered.sort(key=lambda r: r["period"])

    if not filtered:
        print(
            f"ERROR: No records found for ward='{ward}', category='{category}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Enforcement rule 2: print null-row report BEFORE computation ──────────
    relevant_nulls = [
        n for n in null_rows
        if n["ward"] == ward and n["category"] == category
    ]
    print(f"\n{'=' * 60}")
    print(f"NULL ROW REPORT (flagged before computation)")
    print(f"{'=' * 60}")
    if relevant_nulls:
        for n in relevant_nulls:
            print(f"  [NULL] {n['period']} | {n['ward']} | {n['category']}")
            print(f"         Reason: {n['null_reason']}")
    else:
        print(f"  [OK] No null actual_spend rows for this ward/category.")
    print(f"{'=' * 60}\n")

    # ── Build lookup: period → actual_spend ───────────────────────────────────
    spend_by_period = {r["period"]: r["actual_spend"] for r in filtered}

    # ── Compute growth per period (enforcement rules 3, 7) ───────────────────
    output_rows = []

    for i, row in enumerate(filtered):
        period       = row["period"]
        actual_spend = row["actual_spend"]
        null_flag    = "NULL" if actual_spend is None else ""
        null_reason  = row["notes"] if actual_spend is None else ""

        growth_pct   = ""
        formula_used = ""

        if null_flag == "NULL":
            # Enforcement rule 2: no computation for null rows
            growth_pct   = "NULL_FLAGGED"
            formula_used = f"NULL_FLAGGED — actual_spend missing ({null_reason})"

        elif i == 0:
            # Enforcement rule 7: first period has no prior
            growth_pct   = "N/A"
            formula_used = "N/A — no prior period"

        else:
            if growth_type == "MoM":
                prev_period  = filtered[i - 1]["period"]
                prev_spend   = spend_by_period.get(prev_period)

                if prev_spend is None:
                    growth_pct   = "NULL_FLAGGED"
                    formula_used = f"NULL_FLAGGED — reference period {prev_period} has no actual_spend"
                else:
                    pct = ((actual_spend - prev_spend) / prev_spend) * 100
                    growth_pct   = f"{pct:+.1f}%"
                    formula_used = f"(({actual_spend} - {prev_spend}) / {prev_spend}) * 100"

            elif growth_type == "YoY":
                # Same month prior year: replace year part
                year, month  = period.split("-")
                prior_period = f"{int(year) - 1}-{month}"
                prior_spend  = spend_by_period.get(prior_period)

                if prior_spend is None:
                    growth_pct   = "NULL_FLAGGED"
                    formula_used = f"NULL_FLAGGED — reference period {prior_period} has no actual_spend or is out of range"
                else:
                    pct = ((actual_spend - prior_spend) / prior_spend) * 100
                    growth_pct   = f"{pct:+.1f}%"
                    formula_used = f"(({actual_spend} - {prior_spend}) / {prior_spend}) * 100"

        output_rows.append({
            "ward":          ward,
            "category":      category,
            "period":        period,
            "actual_spend":  actual_spend if actual_spend is not None else "NULL",
            "growth_pct":    growth_pct,
            "formula_used":  formula_used,
            "null_flag":     null_flag,
            "null_reason":   null_reason,
        })

    # ── Write output CSV (enforcement rule 5) ─────────────────────────────────
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    fieldnames = ["ward", "category", "period", "actual_spend",
                  "growth_pct", "formula_used", "null_flag", "null_reason"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    # ── Print completion summary ───────────────────────────────────────────────
    null_count = sum(1 for r in output_rows if r["null_flag"] == "NULL")
    print(f"\n{'=' * 60}")
    print(f"UC-0C Growth Calculator — Complete")
    print(f"{'=' * 60}")
    print(f"  Ward          : {ward}")
    print(f"  Category      : {category}")
    print(f"  Growth Type   : {growth_type}")
    print(f"  Total periods : {len(output_rows)}")
    print(f"  Null rows     : {null_count}")
    print(f"  Output file   : {output_path}")
    print(f"{'=' * 60}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description=(
            "UC-0C Growth Calculator — computes per-ward per-category spend growth "
            "from ward_budget.csv. Flags nulls, shows formula, refuses to aggregate."
        )
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to ward_budget.csv (e.g. ../data/budget/ward_budget.csv)",
    )
    parser.add_argument(
        "--ward", required=True,
        help='Ward name (e.g. "Ward 1 – Kasba")',
    )
    parser.add_argument(
        "--category", required=True,
        help='Category name (e.g. "Roads & Pothole Repair")',
    )
    parser.add_argument(
        "--growth-type", required=False, default=None,
        help="Growth type: MoM or YoY. REQUIRED — will refuse if not provided.",
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to write growth_output.csv",
    )
    args = parser.parse_args()

    # ── Enforcement rule 4: refuse if --growth-type not provided ─────────────
    if not args.growth_type:
        print(
            "ERROR: Growth type not specified.\n"
            "Please provide --growth-type MoM or --growth-type YoY. Do not guess.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Step 1: load_dataset ──────────────────────────────────────────────────
    print(f"Loading dataset: {args.input}")
    data = load_dataset(args.input)
    print(f"  Total records : {len(data['records'])}")
    print(f"  Null rows     : {len(data['null_rows'])} (will be reported before computation)")

    # ── Step 2: compute_growth ────────────────────────────────────────────────
    compute_growth(
        records=data["records"],
        null_rows=data["null_rows"],
        ward=args.ward,
        category=args.category,
        growth_type=args.growth_type,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
