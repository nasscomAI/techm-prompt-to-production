"""
UC-0C — Budget Growth Calculator
Enforces per-ward per-category scope, null handling, formula transparency.
"""
import argparse
import csv
from pathlib import Path
from datetime import datetime

def load_dataset(input_path: str, ward_filter=None, category_filter=None) -> dict:
    """
    Load and validate budget CSV.
    Returns dict with data, null rows info, counts.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    null_rows = []
    
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Validate columns
        required_cols = {"period", "ward", "category", "actual_spend", "notes"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must have columns: {required_cols}")
        
        for row in reader:
            # Apply filters
            if ward_filter and row["ward"].strip() != ward_filter.strip():
                continue
            if category_filter and row["category"].strip() != category_filter.strip():
                continue
            
            # Track nulls
            if not row["actual_spend"].strip():
                null_rows.append({
                    "period": row["period"],
                    "ward": row["ward"],
                    "category": row["category"],
                    "reason": row.get("notes", "No notes")
                })
            
            data.append(row)
    
    # Sort by period
    data.sort(key=lambda x: x["period"])
    
    return {
        "data": data,
        "null_rows": null_rows,
        "row_count": len(data),
        "null_count": len(null_rows)
    }


def compute_growth(dataset: dict, growth_type: str) -> list:
    """
    Compute MoM or YoY growth with formula transparency.
    """
    if growth_type not in ["MoM", "YoY"]:
        raise ValueError("growth_type must be 'MoM' or 'YoY'")
    
    data = dataset["data"]
    results = []
    
    # Filter out rows with null actual_spend for calculation
    valid_rows = []
    for row in data:
        if row["actual_spend"].strip():
            try:
                row_copy = row.copy()
                row_copy["actual_spend_float"] = float(row["actual_spend"])
                valid_rows.append(row_copy)
            except ValueError:
                continue
    
    # Sort by period
    valid_rows.sort(key=lambda x: x["period"])
    
    # Compute growth
    for i in range(len(valid_rows)):
        current_row = valid_rows[i]
        current_period = current_row["period"]  # YYYY-MM
        current_spend = current_row["actual_spend_float"]
        
        # Find previous period based on growth_type
        if growth_type == "MoM":
            # Previous month
            if i == 0:
                continue  # No previous month
            previous_row = valid_rows[i - 1]
            previous_period = previous_row["period"]
            previous_spend = previous_row["actual_spend_float"]
        
        elif growth_type == "YoY":
            # Previous year (not applicable for 1-year data)
            current_month = current_period.split("-")[1]
            previous_period_expected = f"2023-{current_month}"
            # Check if previous year exists
            found = False
            for row in valid_rows:
                if row["period"] == previous_period_expected:
                    previous_spend = row["actual_spend_float"]
                    previous_period = row["period"]
                    found = True
                    break
            
            if not found:
                # No previous year data
                continue
        
        # Compute growth percentage
        if previous_spend == 0:
            growth_percent = None  # Undefined
            formula = f"Cannot compute growth: previous spend is 0"
        else:
            growth_percent = ((current_spend - previous_spend) / previous_spend) * 100
            formula = f"({current_spend:.1f} - {previous_spend:.1f}) / {previous_spend:.1f} * 100 = {growth_percent:+.1f}%"
        
        results.append({
            "period": current_period,
            "previous_period": previous_period,
            "previous_spend_lakh": f"{previous_spend:.1f}",
            "current_spend_lakh": f"{current_spend:.1f}",
            "growth_percent": f"{growth_percent:+.1f}%" if growth_percent is not None else "N/A",
            "formula": formula
        })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Ward name (exact match required)")
    parser.add_argument("--category", required=True, help="Category name (exact match required)")
    parser.add_argument("--growth-type", required=True, choices=["MoM", "YoY"], help="Growth type: MoM or YoY")
    parser.add_argument("--output", required=True, help="Path to write growth_output.csv")
    args = parser.parse_args()
    
    try:
        # Load dataset
        print(f"Loading data for Ward: {args.ward} | Category: {args.category}")
        dataset = load_dataset(args.input, args.ward, args.category)
        
        print(f"\nRows found: {dataset['row_count']}")
        print(f"Null actual_spend rows: {dataset['null_count']}")
        
        # Report nulls
        if dataset["null_rows"]:
            print("\n[FLAGGED NULL ROWS]")
            for null_row in dataset["null_rows"]:
                print(f"  Period {null_row['period']}: {null_row['reason']}")
        
        # Compute growth
        print(f"\nComputing {args.growth_type} growth...")
        growth_data = compute_growth(dataset, args.growth_type)
        
        if not growth_data:
            print(f"[WARN] No growth data computed (insufficient data points or all nulls).")
            growth_data = []
        
        # Write output
        output_file = Path(args.output)
        if growth_data:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["period", "previous_period", "previous_spend_lakh", "current_spend_lakh", "growth_percent", "formula"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(growth_data)
            
            print(f"\n[OUTPUT]")
            print(f"Growth results written to: {args.output}")
            for row in growth_data:
                print(f"  {row['period']}: {row['growth_percent']} | {row['formula']}")
        else:
            print(f"\n[OUTPUT] No results to write.")
    
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=__import__("sys").stderr)
        exit(1)


if __name__ == "__main__":
    main()
