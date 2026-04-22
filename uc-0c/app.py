"""
UC-0C app.py — Growth Analysis with Strict Enforcement (Standard Lib only).
"""
import argparse
import csv
import sys
import os
from datetime import datetime

# Configure standard output to use UTF-8 if possible, or handle encoding errors
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

def load_dataset(file_path):
    """
    Reads CSV using standard lib, validates columns, reports null count.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    
    data = []
    required_columns = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    
    # Try reading with utf-8-sig to handle BOM if present
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print("Error: CSV file is empty or invalid.")
                sys.exit(1)
                
            for col in required_columns:
                if col not in reader.fieldnames:
                    print(f"Error: Missing required column '{col}'")
                    sys.exit(1)
            
            for row in reader:
                data.append(row)
    except UnicodeDecodeError:
        # Fallback to cp1252 if utf-8 fails
        with open(file_path, mode='r', encoding='cp1252') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    
    null_rows = [row for row in data if not row['actual_spend'] or row['actual_spend'].strip() == '']
    if null_rows:
        print(f"--- Dataset Validation: Found {len(null_rows)} rows with NULL actual_spend ---")
        for row in null_rows:
            # Print safely
            print(f"Flagged NULL: {row['period']} | {row['ward']} | {row['category']} | Reason: {row['notes']}")
        print("-----------------------------------------------------------------------\n")
    
    return data

def compute_growth(data, ward, category, growth_type):
    """
    Calculates growth (MoM or YoY) for a specific ward and category.
    """
    # Enforcement Rule 1: Never aggregate across wards or categories
    if ward == "Any" or category == "Any" or not ward or not category:
        print("Error: All-ward or all-category aggregation is prohibited. Please specify a single ward and category.")
        sys.exit(1)

    # Filter data - handle potential encoding variations in ward name
    subset = [row for row in data if row['ward'].strip() == ward.strip() and row['category'].strip() == category.strip()]
    
    if not subset:
        print(f"Error: No data found for Ward: '{ward}' and Category: '{category}'")
        # List available wards to help debugging
        wards = sorted(list(set(row['ward'] for row in data)))
        print(f"Available Wards: {', '.join(wards)}")
        sys.exit(1)

    # Sort by period
    try:
        subset.sort(key=lambda x: datetime.strptime(x['period'], '%Y-%m'))
    except Exception as e:
        print(f"Error parsing period format: {e}")
        sys.exit(1)
    
    results = []
    
    for i in range(len(subset)):
        current_row = subset[i]
        period_str = current_row['period']
        actual_spend_str = current_row['actual_spend'].strip()
        
        is_null = not actual_spend_str or actual_spend_str == ''
        actual_spend = float(actual_spend_str) if not is_null else None
        
        res = {
            "Ward": ward,
            "Category": category,
            "Period": period_str,
            "Actual Spend (INR lakh)": actual_spend if not is_null else "NULL",
            "MoM Growth": "n/a",
            "Formula": "n/a"
        }

        if is_null:
            res["MoM Growth"] = "NULL (Flagged)"
            res["Formula"] = f"N/A - {current_row['notes']}"
        elif i > 0:
            prev_row = subset[i-1]
            prev_spend_str = prev_row['actual_spend'].strip()
            prev_is_null = not prev_spend_str or prev_spend_str == ''
            
            if prev_is_null:
                res["MoM Growth"] = "Cannot compute"
                res["Formula"] = f"({actual_spend} - NULL) / NULL"
            else:
                prev_spend = float(prev_spend_str)
                growth = ((actual_spend - prev_spend) / prev_spend) * 100
                res["MoM Growth"] = f"{growth:+.1f}%"
                res["Formula"] = f"(({actual_spend} - {prev_spend}) / {prev_spend}) * 100"
        
        results.append(res)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Calculate growth from budget data.")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--ward", help="Specific ward name")
    parser.add_argument("--category", help="Specific category name")
    parser.add_argument("--growth-type", choices=["MoM", "YoY"], help="Type of growth calculation")
    parser.add_argument("--output", help="Path to output CSV")
    
    args = parser.parse_args()

    # Enforcement Rule 4: If growth-type not specified — refuse and ask
    if not args.growth_type:
        print("Refusal: --growth-type is not specified. Please specify 'MoM' or 'YoY'. I will not guess.")
        sys.exit(1)

    # Load data
    data = load_dataset(args.input)

    # Compute growth
    results = compute_growth(data, args.ward, args.category, args.growth_type)

    # Show output
    header = ["Ward", "Category", "Period", "Actual Spend (INR lakh)", "MoM Growth", "Formula"]
    print(f"{' | '.join(header)}")
    print("-" * 120)
    for res in results:
        print(f"{res['Ward']} | {res['Category']} | {res['Period']} | {res['Actual Spend (INR lakh)']} | {res['MoM Growth']} | {res['Formula']}")

    # Save to file if specified
    if args.output:
        with open(args.output, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
