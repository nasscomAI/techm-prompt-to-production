"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import sys
import pandas as pd


REQUIRED_COLUMNS = [
    "period",
    "ward",
    "category",
    "budgeted_amount",
    "actual_spend",
    "notes",
]


def load_dataset(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise Exception(f"File access error: {str(e)}")

    # Validate columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise Exception(f"Schema validation error: Missing columns {missing_cols}")

    if df.empty:
        raise Exception("Data validation error: Dataset is empty")

    # Detect nulls
    null_rows = df[df["actual_spend"].isna()]
    null_summary = {
        "count": len(null_rows),
        "rows": null_rows[["period", "ward", "category", "notes"]].to_dict(
            orient="records"
        ),
    }

    return {"dataframe": df, "null_summary": null_summary}


def compute_growth(df, ward, category, growth_type):
    if not ward or not category:
        raise Exception("Validation error: Ward and category must be provided")

    if not growth_type:
        raise Exception(
            "Missing parameter: --growth-type must be specified (MoM or YoY)"
        )

    if growth_type not in ["MoM", "YoY"]:
        raise Exception(f"Unsupported growth_type: {growth_type}")

    # Filter strictly (no aggregation)
    filtered = df[(df["ward"] == ward) & (df["category"] == category)]

    if filtered.empty:
        raise Exception("Validation error: No data found for given ward and category")

    # Sort by period
    filtered = filtered.sort_values("period").reset_index(drop=True)

    output_rows = []

    for i in range(len(filtered)):
        row = filtered.iloc[i]
        current_val = row["actual_spend"]

        null_flag = pd.isna(current_val)
        null_reason = row["notes"] if null_flag else ""

        growth_value = None
        formula = ""

        if null_flag:
            formula = "NULL - actual_spend missing"
        else:
            if i == 0:
                formula = "N/A (no previous period)"
            else:
                prev_val = filtered.iloc[i - 1]["actual_spend"]

                if pd.isna(prev_val):
                    formula = "Skipped - previous period actual_spend is NULL"
                    null_flag = True
                    null_reason = "Previous period value missing"
                else:
                    if growth_type == "MoM":
                        growth_value = ((current_val - prev_val) / prev_val) * 100
                        formula = f"(({current_val} - {prev_val}) / {prev_val}) * 100"
                    elif growth_type == "YoY":
                        # Find same month previous year
                        prev_year_period = str(int(row["period"][:4]) - 1) + row["period"][4:]
                        prev_year_row = filtered[
                            filtered["period"] == prev_year_period
                        ]

                        if prev_year_row.empty or pd.isna(
                            prev_year_row.iloc[0]["actual_spend"]
                        ):
                            formula = "Skipped - previous year value missing or NULL"
                            null_flag = True
                            null_reason = "Previous year value missing"
                        else:
                            prev_val = prev_year_row.iloc[0]["actual_spend"]
                            growth_value = ((current_val - prev_val) / prev_val) * 100
                            formula = f"(({current_val} - {prev_val}) / {prev_val}) * 100"

        output_rows.append(
            {
                "period": row["period"],
                "ward": ward,
                "category": category,
                "actual_spend": current_val,
                "growth_value": growth_value,
                "formula": formula,
                "null_flag": null_flag,
                "null_reason": null_reason,
            }
        )

    result_df = pd.DataFrame(output_rows)

    # Reference validation (only for known cases)
    def approx_equal(a, b, tol=0.5):
        return abs(a - b) <= tol

    for _, r in result_df.iterrows():
        if (
            ward == "Ward 1 – Kasba"
            and category == "Roads & Pothole Repair"
            and r["period"] == "2024-07"
            and r["growth_value"] is not None
        ):
            if not approx_equal(r["growth_value"], 33.1):
                raise Exception("Reference validation failed for 2024-07")

        if (
            ward == "Ward 1 – Kasba"
            and category == "Roads & Pothole Repair"
            and r["period"] == "2024-10"
            and r["growth_value"] is not None
        ):
            if not approx_equal(r["growth_value"], -34.8):
                raise Exception("Reference validation failed for 2024-10")

    return result_df


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--ward", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--growth-type", required=False)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    # Enforce growth-type presence
    if not args.growth_type:
        print(
            "Error: --growth-type must be specified (MoM or YoY). Refusing to proceed."
        )
        sys.exit(1)

    try:
        # Load dataset
        dataset = load_dataset(args.input)
        df = dataset["dataframe"]

        # Print null summary (explicit handling)
        null_summary = dataset["null_summary"]
        print(f"Null rows detected: {null_summary['count']}")
        for row in null_summary["rows"]:
            print(f"NULL -> {row}")

        # Compute growth
        result_df = compute_growth(
            df, args.ward, args.category, args.growth_type
        )

        # Ensure per-period output (not aggregated)
        if result_df.shape[0] <= 1:
            raise Exception("Output validation error: Not a per-period table")

        # Save output
        result_df.to_csv(args.output, index=False)
        print(f"Output written to {args.output}")

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        sys.exit(1)




if __name__ == "__main__":
    main()
