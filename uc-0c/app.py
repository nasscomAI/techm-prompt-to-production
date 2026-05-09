"""UC-0C app.py — Growth calculator implementation."""

import argparse
import csv
from typing import List, Dict, Any

REQUIRED_COLUMNS = ["period", "ward", "category", "budgeted_amount", "actual_spend", "notes"]

def load_dataset(file_path: str) -> tuple[List[Dict[str, Any]], str]:
    """Reads CSV, validates columns, reports null count and which rows before returning."""
    try:
        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not all(col in reader.fieldnames for col in REQUIRED_COLUMNS):
                return [], f"Error: Missing required columns. Expected: {REQUIRED_COLUMNS}, Found: {list(reader.fieldnames)}"
            data = []
            null_report = []
            null_count = 0
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                data.append(row)
                if not row.get("actual_spend", "").strip():
                    null_count += 1
                    reason = row.get("notes", "No reason provided").strip()
                    null_report.append(f"Row {row_num}: {row['period']} - {row['ward']} - {row['category']} - Reason: {reason}")
            report = f"Dataset loaded successfully. Total rows: {len(data)}. Null actual_spend rows: {null_count}\n" + "\n".join(null_report) if null_report else f"Dataset loaded successfully. Total rows: {len(data)}. No nulls found."
            return data, report
    except FileNotFoundError:
        return [], "Error: File not found."
    except Exception as e:
        return [], f"Error reading CSV: {str(e)}"

def compute_growth(ward: str, category: str, growth_type: str, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Takes ward, category, growth_type, returns per-period table with formula shown."""
    if growth_type != "MoM":
        raise ValueError("Error: Only 'MoM' growth type is supported. Please specify --growth-type MoM.")

    # Filter dataset for ward and category
    filtered = [row for row in dataset if row["ward"] == ward and row["category"] == category]
    if not filtered:
        raise ValueError(f"Error: No data found for ward '{ward}' and category '{category}'.")

    # Sort by period
    filtered.sort(key=lambda x: x["period"])

    results = []
    prev_spend = None
    for row in filtered:
        period = row["period"]
        spend_str = row.get("actual_spend", "").strip()
        notes = row.get("notes", "").strip()

        if not spend_str:
            growth = f"NULL - {notes}"
            formula = "N/A - null value"
        else:
            try:
                current_spend = float(spend_str)
                if prev_spend is None:
                    growth = "N/A - first period"
                    formula = "N/A - first period"
                else:
                    growth_pct = ((current_spend - prev_spend) / prev_spend) * 100
                    growth = f"{growth_pct:.1f}%"
                    formula = "MoM Growth = ((current - previous) / previous) * 100"
                prev_spend = current_spend
            except ValueError:
                growth = "ERROR - invalid spend value"
                formula = "N/A - invalid data"

        results.append({
            "period": period,
            "actual_spend": spend_str if spend_str else "NULL",
            "growth_percentage": growth,
            "formula_used": formula
        })

    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Ward name")
    parser.add_argument("--category", required=True, help="Category name")
    parser.add_argument("--growth-type", required=True, help="Growth type (e.g., MoM)")
    parser.add_argument("--output", required=True, help="Path to write growth_output.csv")
    args = parser.parse_args()

    dataset, report = load_dataset(args.input)
    print(report)

    if not dataset:
        print("Exiting due to dataset loading error.")
        return

    try:
        results = compute_growth(args.ward, args.category, args.growth_type, dataset)
    except ValueError as e:
        print(str(e))
        return

    try:
        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["period", "actual_spend", "growth_percentage", "formula_used"])
            writer.writeheader()
            writer.writerows(results)
        print(f"Growth output written to {args.output}")
    except Exception as e:
        print(f"Error writing output: {str(e)}")

if __name__ == "__main__":
    main()
