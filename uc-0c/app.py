"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""

import argparse
import pandas as pd


def load_dataset(file_path):
    df = pd.read_csv(file_path)

    required = [
        "period",
        "ward",
        "category",
        "budgeted_amount",
        "actual_spend",
        "notes"
    ]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    return df


def compute_growth(df, ward, category, growth_type):
    if not growth_type:
        raise ValueError("growth_type required")

    filtered = df[
        (df["ward"] == ward) &
        (df["category"] == category)
    ].copy()

    filtered = filtered.sort_values("period")

    results = []

    prev = None

    for _, row in filtered.iterrows():
        if pd.isna(row["actual_spend"]):
            growth = "NULL"
            formula = row["notes"]
        elif prev is None:
            growth = "N/A"
            formula = "No previous month"
            prev = row["actual_spend"]
        else:
            growth_value = ((row["actual_spend"] - prev) / prev) * 100
            growth = f"{growth_value:.1f}%"
            formula = "(current-prev)/prev * 100"
            prev = row["actual_spend"]

        results.append({
            "period": row["period"],
            "ward": row["ward"],
            "category": row["category"],
            "actual_spend": row["actual_spend"],
            "growth": growth,
            "formula": formula
        })

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--ward", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--growth-type", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    df = load_dataset(args.input)

    result = compute_growth(
        df,
        args.ward,
        args.category,
        args.growth_type
    )

    result.to_csv(args.output, index=False)

    print("Done")


if __name__ == "__main__":
    main()
