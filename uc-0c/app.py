"""
UC-0C app.py — Financial Data Analyst implementation.
Based strictly on agents.md and skills.md.
"""
import argparse
import csv
import sys

def load_dataset(input_path: str):
    """
    Reads budget CSV, validates columns, and reports null count + reasons.
    """
    required_columns = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    data = []
    null_rows = []

    try:
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not all(col in reader.fieldnames for col in required_columns):
                raise ValueError("Missing essential columns in dataset.")

            for row in reader:
                data.append(row)
                if not row['actual_spend'].strip():
                    null_rows.append(row)
                    
        print(f"Dataset Loaded. Total Rows: {len(data)}")
        print(f"Validation: Found {len(null_rows)} rows with null 'actual_spend'.")
        for r in null_rows:
            print(f"  - NULL at {r['period']} / {r['ward']} / {r['category']} | Reason: {r['notes']}")
            
        return data

    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

def compute_growth(data: list, ward: str, category: str, growth_type: str, output_path: str):
    """
    Computes per-period growth for a target ward & category.
    Strictly forbids aggregation and explicitly flags nulls according to agents.md.
    """
    if not ward or not category:
        print("ERROR: Refusing to compute. Ward and Category must be explicitly specified to prevent incorrect aggregation.")
        sys.exit(1)
        
    if not growth_type:
        print("ERROR: --growth-type not specified. I will not guess. Please provide MoM or YoY.")
        sys.exit(1)

    # Filter data preventing cross-ward or cross-category aggregations
    filtered_data = [row for row in data if row['ward'] == ward and row['category'] == category]
    
    if not filtered_data:
        print(f"No data found for Ward: '{ward}', Category: '{category}'.")
        sys.exit(1)

    # Sort strictly by period to calculate growth
    filtered_data = sorted(filtered_data, key=lambda x: x['period'])

    results = []
    
    for i, row in enumerate(filtered_data):
        period = row['period']
        actual_spend = row['actual_spend'].strip()
        notes = row['notes'].strip()
        
        result_row = {
            'period': period,
            'ward': ward,
            'category': category,
            'actual_spend': actual_spend if actual_spend else 'NULL',
            'growth': 'NULL',
            'formula': 'N/A',
            'flags': ''
        }

        if not actual_spend:
            result_row['flags'] = f"FLAGGED NULL: {notes}"
            results.append(result_row)
            continue

        current_val = float(actual_spend)

        # Logic for MoM, looking at the strict previous index (assuming continuous months)
        if growth_type.lower() == 'mom':
            if i == 0:
                result_row['growth'] = 'N/A (First Month)'
                result_row['formula'] = 'No previous month data'
            else:
                prev_spend_str = filtered_data[i-1]['actual_spend'].strip()
                if not prev_spend_str:
                    result_row['growth'] = 'N/A'
                    result_row['formula'] = 'Previous month was NULL'
                else:
                    prev_val = float(prev_spend_str)
                    if prev_val == 0:
                        result_row['growth'] = 'Undefined (Prev is 0)'
                        result_row['formula'] = f"({current_val} - {prev_val}) / {prev_val}"
                    else:
                        g = ((current_val - prev_val) / prev_val) * 100
                        result_row['growth'] = f"{g:+.1f}%"
                        result_row['formula'] = f"(Current({current_val}) - Prev({prev_val})) / Prev({prev_val}) * 100"
                        
        # Optionally support YoY if dataset spanning multiple years is provided
        elif growth_type.lower() == 'yoy':
            result_row['growth'] = 'N/A'
            result_row['formula'] = 'YoY logic unimplemented in this snippet'
        else:
            print(f"ERROR: Unsupported growth type '{growth_type}'")
            sys.exit(1)

        results.append(result_row)

    # Write Results
    fieldnames = ['period', 'ward', 'category', 'actual_spend', 'growth', 'formula', 'flags']
    
    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Success. Growth output written to {output_path}")
    except Exception as e:
        print(f"Error writing output: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="UC-0C Financial Data Analyst")
    parser.add_argument("--input", required=True, help="Path to input budget CSV")
    parser.add_argument("--ward", required=False, help="Target ward for isolation")
    parser.add_argument("--category", required=False, help="Target category for isolation")
    parser.add_argument("--growth-type", required=False, dest="growth_type", help="Growth metric formula (e.g. MoM)")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()

    # The agent explicitly requires ward and category, refusing to guess missing parameters.
    if not args.ward or not args.category:
        print("ERROR: You must specify --ward and --category explicitly to avoid unintended aggregation.")
        sys.exit(1)

    if not args.growth_type:
        print("ERROR: --growth-type must be specified to confirm computation formula.")
        sys.exit(1)

    dataset = load_dataset(args.input)
    compute_growth(dataset, args.ward, args.category, args.growth_type, args.output)

if __name__ == "__main__":
    main()
