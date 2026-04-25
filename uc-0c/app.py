"""
UC-0C app.py — Budget Growth Analyst.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
"""
import argparse
import csv
import sys
import os

def load_dataset(file_path):
    """
    Reads the budget CSV file, validates the required columns,
    and identifies/reports all null rows with their reasons.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
        
    data = []
    null_rows = []
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_columns = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
        missing = [col for col in required_columns if col not in reader.fieldnames]
        if missing:
            print(f"Error: Missing columns {missing}")
            sys.exit(1)
            
        for row in reader:
            if not row['actual_spend'] or row['actual_spend'].strip().lower() == 'null':
                row['actual_spend'] = None
                null_rows.append(row)
            else:
                try:
                    row['actual_spend'] = float(row['actual_spend'])
                except ValueError:
                    row['actual_spend'] = None
                    null_rows.append(row)
            data.append(row)
            
    print(f"Found {len(null_rows)} null rows in 'actual_spend':")
    for row in null_rows:
        print(f"- {row['period']} | {row['ward']} | {row['category']} | Reason: {row['notes']}")
        
    return data

def compute_growth(data, ward, category, growth_type):
    """
    Computes growth (MoM) for a specific ward and category.
    """
    # Filter strictly by ward and category
    subset = [row for row in data if row['ward'] == ward and row['category'] == category]
    
    if not subset:
        print(f"Error: No data found for Ward: '{ward}' and Category: '{category}'")
        sys.exit(1)
        
    # Sort by period to ensure chronological order
    subset.sort(key=lambda x: x['period'])
    
    results = []
    
    for i in range(len(subset)):
        row = subset[i]
        period = row['period']
        actual_spend = row['actual_spend']
        
        growth_value = "n/a"
        formula = "n/a"
        
        if actual_spend is None:
            growth_value = "NULL"
            formula = f"Flagged: {row['notes']}"
        elif growth_type == "MoM":
            if i > 0:
                prev_spend = subset[i-1]['actual_spend']
                if prev_spend is None:
                    growth_value = "n/a"
                    formula = "Previous month spend is NULL"
                else:
                    # Formula: ((Current - Previous) / Previous) * 100
                    diff = actual_spend - prev_spend
                    growth = (diff / prev_spend) * 100
                    growth_value = f"{growth:+.1f}%"
                    formula = f"(({actual_spend} - {prev_spend}) / {prev_spend}) * 100"
            else:
                growth_value = "n/a"
                formula = "First period in dataset"
        
        results.append({
            "Ward": ward,
            "Category": category,
            "Period": period,
            "Actual Spend (₹ lakh)": actual_spend if actual_spend is not None else "NULL",
            "Growth": growth_value,
            "Formula": formula
        })
        
    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Analyst")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Ward name")
    parser.add_argument("--category", required=True, help="Category name")
    parser.add_argument("--growth-type", help="Growth type (e.g., MoM)")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    
    args = parser.parse_args()
    
    # Enforcement: If --growth-type not specified — refuse and ask, never guess
    if not args.growth_type:
        print("Error: --growth-type not specified. Please specify MoM or YoY. Refusing to guess.")
        sys.exit(1)
        
    if args.growth_type != "MoM":
        print(f"Error: Growth type '{args.growth_type}' is not supported yet. Only MoM is supported.")
        sys.exit(1)

    # Skills: load_dataset
    data = load_dataset(args.input)
    
    # Skills: compute_growth
    results = compute_growth(data, args.ward, args.category, args.growth_type)
    
    # Output
    if results:
        fieldnames = results[0].keys()
        with open(args.output, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nResults successfully written to {args.output}")
        # Print a small table to console
        print(f"{'Period':<10} | {'Spend':<8} | {'Growth':<8} | {'Formula'}")
        print("-" * 60)
        for r in results:
            print(f"{r['Period']:<10} | {str(r['Actual Spend (₹ lakh)']):<8} | {r['Growth']:<8} | {r['Formula']}")

if __name__ == "__main__":
    main()
