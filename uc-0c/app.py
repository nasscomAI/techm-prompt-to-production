"""
UC-0C Budget Analyzer — MoM/YoY Growth Calculator
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
"""
import argparse
import csv
import sys
import os

def load_dataset(file_path: str):
    """
    Reads the budget CSV and returns the data.
    """
    if not os.path.exists(file_path):
        print(f"Error: Dataset file not found at {file_path}")
        sys.exit(1)
        
    data = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def compute_growth(data, ward, category, growth_type):
    """
    Calculates period-over-period growth for a specific ward and category.
    """
    # Filter data for the specific ward and category
    filtered = [row for row in data if row['ward'] == ward and row['category'] == category]
    
    if not filtered:
        print(f"Error: No data found for Ward: '{ward}' and Category: '{category}'")
        return []

    # Sort by period to ensure MoM works correctly
    filtered.sort(key=lambda x: x['period'])
    
    results = []
    formula = "(Current - Previous) / Previous" if growth_type == "MoM" else "YoY Formula"
    
    for i, row in enumerate(filtered):
        period = row['period']
        actual_spend_str = row['actual_spend'].strip()
        notes = row['notes']
        
        current_val = None
        if actual_spend_str:
            try:
                current_val = float(actual_spend_str)
            except ValueError:
                current_val = None
        
        growth = "N/A"
        if i > 0 and growth_type == "MoM":
            prev_row = filtered[i-1]
            prev_spend_str = prev_row['actual_spend'].strip()
            
            if not actual_spend_str:
                growth = f"NOT_COMPUTED (Reason: {notes})"
            elif not prev_spend_str:
                growth = f"NOT_COMPUTED (Reason: Previous month {prev_row['period']} was null)"
            else:
                try:
                    prev_val = float(prev_spend_str)
                    if prev_val != 0:
                        growth_val = ((current_val - prev_val) / prev_val) * 100
                        growth = f"{growth_val:+.1f}%"
                    else:
                        growth = "INF (Prev is 0)"
                except ValueError:
                    growth = "ERROR"
        
        results.append({
            "period": period,
            "ward": ward,
            "category": category,
            "actual_spend": actual_spend_str if actual_spend_str else "NULL",
            "growth": growth,
            "formula": formula if i > 0 else "N/A (First Period)"
        })
        
    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Analyzer")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Specific ward name")
    parser.add_argument("--category", required=True, help="Specific category name")
    parser.add_argument("--growth-type", help="MoM or YoY (Required)")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    
    args = parser.parse_args()
    
    # Enforcement: If growth-type not specified, refuse
    if not args.growth_type:
        print("Refusal: --growth-type (MoM or YoY) must be specified. I cannot guess the growth calculation formula.")
        sys.exit(1)

    # Enforcement: Aggregation level check
    # (Since we are using specific --ward and --category, we are already granular)
    
    data = load_dataset(args.input)
    results = compute_growth(data, args.ward, args.category, args.growth_type)
    
    if results:
        with open(args.output, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["period", "ward", "category", "actual_spend", "growth", "formula"])
            writer.writeheader()
            writer.writerows(results)
        print(f"Done. Growth analysis written to {args.output}")

if __name__ == "__main__":
    main()
