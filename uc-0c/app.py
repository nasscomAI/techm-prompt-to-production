import pandas as pd
import argparse

def load_dataset(input_file):
    df = pd.read_csv(input_file)

    required_columns = [
        "period",
        "ward",
        "category",
        "budgeted_amount",
        "actual_spend",
        "notes"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    null_rows = df[df["actual_spend"].isnull()]

    return df, null_rows


def compute_growth(df, ward, category, growth_type):
    if not growth_type:
        raise ValueError("Growth type must be specified.")

    filtered = df[
        (df["ward"] == ward) &
        (df["category"] == category)
    ].copy()

    filtered = filtered.sort_values("period")

    output_rows = []

    previous_value = None

    for _, row in filtered.iterrows():
        period = row["period"]
        actual = row["actual_spend"]
        notes = row["notes"]

        if pd.isnull(actual):
            output_rows.append({
                "period": period,
                "actual_spend": "NULL",
                "growth": "NOT COMPUTED",
                "formula": "NULL VALUE",
                "notes": notes
            })
            previous_value = None
            continue

        if previous_value is None:
            growth = "N/A"
            formula = "No previous month available"
        else:
            growth_value = ((actual - previous_value) / previous_value) * 100

            growth = f"{growth_value:.1f}%"

            formula = (
                f"(({actual} - {previous_value}) / "
                f"{previous_value}) * 100"
            )

        output_rows.append({
            "period": period,
            "actual_spend": actual,
            "growth": growth,
            "formula": formula,
            "notes": notes
        })

        previous_value = actual

    return pd.DataFrame(output_rows)


def main(input_file, ward, category, growth_type, output_file):
    df, null_rows = load_dataset(input_file)

    print("Null rows detected:")
    print(null_rows[["period", "ward", "category", "notes"]])

    result = compute_growth(df, ward, category, growth_type)

    result.to_csv(output_file, index=False)

    print(f"Growth output saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--ward", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--growth-type", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    main(
        args.input,
        args.ward,
        args.category,
        args.growth_type,
        args.output
    )