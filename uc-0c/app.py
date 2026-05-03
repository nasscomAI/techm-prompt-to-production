import argparse
import csv
import sys
import os
from datetime import datetime

def load_dataset(file_path):
    """
    Skill: load_dataset
    Reads the budget CSV, validates columns, and reports null values.
    Uses standard csv library to avoid external dependencies.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    
    data = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Validate mandatory columns
            required_columns = ['period', 'ward', 'category', 'actual_spend', 'notes']
            missing = [col for col in required_columns if col not in reader.fieldnames]
            if missing:
                print(f"Error: Missing mandatory columns: {', '.join(missing)}")
                sys.exit(1)
                
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
        
    # Enforcement Rule 2: Flag every null row before computing
    null_count = 0
    for idx, row in enumerate(data):
        actual_spend_val = row['actual_spend'].strip()
        if not actual_spend_val:
            null_count += 1
            print(f"  - [NULL FLAG] Ward: {row['ward']}, Category: {row['category']}, Period: {row['period']}. Reason: {row['notes']}")
            
    if null_count > 0:
        print(f"Dataset loaded. Found {null_count} null values in 'actual_spend'.")
    else:
        print("Dataset loaded successfully with no null values in 'actual_spend'.")
        
    return data

def compute_growth(data, ward, category, growth_type):
    """
    Skill: compute_growth
    Calculates growth for specific ward/category and includes the formula.
    """
    # Filter by ward and category
    filtered_data = [
        row for row in data 
        if row['ward'] == ward and row['category'] == category
    ]
    
    if not filtered_data:
        print(f"Error: No data found for Ward '{ward}' and Category '{category}'.")
        sys.exit(1)
        
    # Sort by period to ensure growth calculation is chronological
    # Assumes period is YYYY-MM
    try:
        filtered_data.sort(key=lambda x: datetime.strptime(x['period'], '%Y-%m'))
    except ValueError as e:
        print(f"Error parsing period dates: {e}")
        sys.exit(1)
    
    results = []
    
    for i in range(len(filtered_data)):
        row = filtered_data[i]
        actual_spend_str = row['actual_spend'].strip()
        actual_spend = float(actual_spend_str) if actual_spend_str else None
        
        res_row = {
            'Ward': row['ward'],
            'Category': row['category'],
            'Period': row['period'],
            'Actual Spend': actual_spend if actual_spend is not None else 'NULL',
            f'{growth_type} Growth': 'n/a',
            'Formula': 'n/a'
        }
        
        # Enforcement Rule 2 (Output side): Report nulls in the output table
        if actual_spend is None:
            res_row[f'{growth_type} Growth'] = f"NULL ({row['notes']})"
            res_row['Formula'] = "N/A - Data missing"
        else:
            if i > 0:
                prev_row = filtered_data[i-1]
                prev_spend_str = prev_row['actual_spend'].strip()
                prev_spend = float(prev_spend_str) if prev_spend_str else None
                
                if growth_type == 'MoM':
                    if prev_spend is not None and prev_spend != 0:
                        growth = (actual_spend - prev_spend) / prev_spend
                        res_row['MoM Growth'] = f"{growth:+.1%}"
                        # Enforcement Rule 3: Show formula used in every output row
                        res_row['Formula'] = f"({actual_spend} - {prev_spend}) / {prev_spend}"
                    else:
                        res_row['MoM Growth'] = "n/a"
                        res_row['Formula'] = "Cannot compute: Previous value null/zero"
                elif growth_type == 'YoY':
                    res_row['YoY Growth'] = "n/a"
                    res_row['Formula'] = "Cannot compute YoY: Previous year data missing"
            else:
                res_row[f'{growth_type} Growth'] = "n/a"
                res_row['Formula'] = "Base period (No previous data)"
                
        results.append(res_row)
        
    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--ward", help="Ward name (e.g., 'Ward 1 – Kasba')")
    parser.add_argument("--category", help="Expenditure category")
    parser.add_argument("--growth-type", help="Type of growth calculation (MoM or YoY)")
    parser.add_argument("--output", default="growth_output.csv", help="Output file path")
    
    args = parser.parse_args()
    
    # Enforcement Rule 4: Refuse if --growth-type not specified
    if not args.growth_type:
        print("Refusal: --growth-type must be specified (MoM or YoY). I am not allowed to guess the growth type.")
        sys.exit(1)
        
    # Enforcement Rule 1: Never aggregate across wards or categories unless explicitly instructed
    if not args.ward or args.ward.lower() in ['all', 'any', 'total']:
        print("Refusal: A specific --ward must be provided. I am not allowed to aggregate across multiple wards.")
        sys.exit(1)
        
    if not args.category or args.category.lower() in ['all', 'any', 'total']:
        print("Refusal: A specific --category must be provided. I am not allowed to aggregate across multiple categories.")
        sys.exit(1)
        
    # Execute Skills
    data = load_dataset(args.input)
    results = compute_growth(data, args.ward, args.category, args.growth_type)
    
    # Save output using csv library
    if results:
        fieldnames = results[0].keys()
        try:
            with open(args.output, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"\nGrowth calculation complete for '{args.ward}' - '{args.category}'.")
            print(f"Results saved to {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
