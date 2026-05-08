"""
UC-0C app.py — Budget Growth Analyst
Implements agents.md + skills.md: load_dataset and compute_growth.
"""
import argparse
import sys
import pandas as pd


# ── Skill: load_dataset ────────────────────────────────────────────────────────

def load_dataset(filepath: str):
    """
    Reads the ward budget CSV, validates required columns, and reports every
    null actual_spend row before returning the dataframe.
    Returns: (df, null_report)
      null_report — list of dicts {period, ward, category, reason}
    """
    required_columns = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}

    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        sys.exit(f"[ERROR] File not found: {filepath}")

    if df.empty:
        sys.exit("[ERROR] Dataset is empty — cannot proceed.")

    missing = required_columns - set(df.columns)
    if missing:
        sys.exit(f"[ERROR] Missing required columns: {', '.join(sorted(missing))}")

    # Build null report
    null_rows = df[df["actual_spend"].isna()]
    null_report = [
        {
            "period": row["period"],
            "ward": row["ward"],
            "category": row["category"],
            "reason": str(row["notes"]).strip() if pd.notna(row["notes"]) else "No reason provided",
        }
        for _, row in null_rows.iterrows()
    ]

    if null_report:
        print("\n[NULL REPORT] The following rows have no actual_spend and will be SKIPPED:")
        print(f"  {'Period':<12} {'Ward':<35} {'Category':<30} Reason")
        print("  " + "-" * 100)
        for r in null_report:
            print(f"  {r['period']:<12} {r['ward']:<35} {r['category']:<30} {r['reason']}")
        print()

    return df, null_report


# ── Skill: compute_growth ──────────────────────────────────────────────────────

def compute_growth(df: pd.DataFrame, ward: str, category: str, growth_type: str) -> pd.DataFrame:
    """
    Computes MoM or YoY growth for a single ward + category.
    Returns a per-period table: period, actual_spend, growth_pct, formula, status.
    """
    # Validate growth_type
    if growth_type not in ("MoM", "YoY"):
        sys.exit(
            f"[REFUSED] growth_type '{growth_type}' is not recognised.\n"
            "Please specify --growth-type MoM or --growth-type YoY."
        )

    # Validate ward
    available_wards = df["ward"].unique().tolist()
    if ward not in available_wards:
        sys.exit(
            f"[REFUSED] Ward '{ward}' not found in dataset.\n"
            f"Available wards: {', '.join(sorted(available_wards))}"
        )

    # Validate category
    available_categories = df["category"].unique().tolist()
    if category not in available_categories:
        sys.exit(
            f"[REFUSED] Category '{category}' not found in dataset.\n"
            f"Available categories: {', '.join(sorted(available_categories))}"
        )

    # Filter to single ward + category — never aggregate
    subset = df[(df["ward"] == ward) & (df["category"] == category)].copy()
    subset = subset.sort_values("period").reset_index(drop=True)

    if subset.empty:
        sys.exit(f"[REFUSED] No data found for ward='{ward}' and category='{category}'.")

    non_null_count = subset["actual_spend"].notna().sum()
    if non_null_count < 2:
        sys.exit(
            "[REFUSED] Fewer than 2 non-null periods available — "
            "cannot compute growth with insufficient data points."
        )

    if growth_type == "MoM":
        formula_template = "MoM = (current − previous) / previous × 100"
        shift = 1
    else:  # YoY
        formula_template = "YoY = (current − same_month_prior_year) / same_month_prior_year × 100"
        shift = 12

    results = []
    for i, row in subset.iterrows():
        period = row["period"]
        spend = row["actual_spend"]

        if pd.isna(spend):
            reason = str(row["notes"]).strip() if pd.notna(row["notes"]) else "No reason provided"
            results.append({
                "period": period,
                "actual_spend": "NULL",
                "growth_pct": "N/A",
                "formula": formula_template,
                "status": f"SKIPPED — null: {reason}",
            })
            continue

        # Find the comparison row
        prev_rows = subset.iloc[:i]
        prev_non_null = prev_rows[prev_rows["actual_spend"].notna()]

        if growth_type == "MoM":
            # Immediately preceding non-null period
            if prev_non_null.empty:
                results.append({
                    "period": period,
                    "actual_spend": round(spend, 2),
                    "growth_pct": "N/A",
                    "formula": formula_template,
                    "status": "OK — no prior period to compare",
                })
                continue
            prev_spend = prev_non_null.iloc[-1]["actual_spend"]
        else:
            # Same month, prior year
            prior_period = f"{int(period[:4]) - 1}{period[4:]}"
            prior_row = subset[subset["period"] == prior_period]
            if prior_row.empty or pd.isna(prior_row.iloc[0]["actual_spend"]):
                results.append({
                    "period": period,
                    "actual_spend": round(spend, 2),
                    "growth_pct": "N/A",
                    "formula": formula_template,
                    "status": "OK — no prior year period to compare",
                })
                continue
            prev_spend = prior_row.iloc[0]["actual_spend"]

        growth_pct = ((spend - prev_spend) / prev_spend) * 100
        sign = "+" if growth_pct >= 0 else ""
        results.append({
            "period": period,
            "actual_spend": round(spend, 2),
            "growth_pct": f"{sign}{round(growth_pct, 1)}%",
            "formula": formula_template,
            "status": "OK",
        })

    return pd.DataFrame(results)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Analyst")
    parser.add_argument("--input",       required=True,  help="Path to ward_budget.csv")
    parser.add_argument("--ward",        required=True,  help="Ward name (exact match)")
    parser.add_argument("--category",    required=True,  help="Category name (exact match)")
    parser.add_argument("--growth-type", required=False, default=None,
                        dest="growth_type", help="MoM or YoY")
    parser.add_argument("--output",      required=False, default="growth_output.csv",
                        help="Output CSV filename")
    args = parser.parse_args()

    # Enforcement: refuse if --growth-type not provided
    if args.growth_type is None:
        sys.exit(
            "[REFUSED] --growth-type was not specified.\n"
            "Please provide --growth-type MoM or --growth-type YoY.\n"
            "This system never guesses the growth formula."
        )

    # Skill: load_dataset
    df, null_report = load_dataset(args.input)

    print(f"[INFO] Dataset loaded: {len(df)} rows")
    print(f"[INFO] Computing {args.growth_type} growth for: {args.ward} / {args.category}\n")

    # Skill: compute_growth
    result_df = compute_growth(df, args.ward, args.category, args.growth_type)

    # Display results
    print(f"{'Period':<12} {'Actual Spend':>14} {'Growth':>10}  {'Status':<40} Formula")
    print("-" * 110)
    for _, row in result_df.iterrows():
        print(
            f"{row['period']:<12} {str(row['actual_spend']):>14} {str(row['growth_pct']):>10}"
            f"  {str(row['status']):<40} {row['formula']}"
        )

    # Save output
    result_df.to_csv(args.output, index=False)
    print(f"\n[INFO] Output saved to: {args.output}")


if __name__ == "__main__":
    main()
