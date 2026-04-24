import argparse
import csv
import sys

def load_dataset(file_path):
    """
    Reads the CSV dataset, validates columns, and reports null count with row identification.
    """
    data = []
    null_rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_cols = {'period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes'}
        
        if not required_cols.issubset(set(reader.fieldnames)):
            raise ValueError(f"Missing columns in dataset. Required: {required_cols}")
        
        for row in reader:
            if not row['actual_spend'].strip():
                null_rows.append(row)
            data.append(row)
            
    # Rule 2: Flag every null row before computing
    if null_rows:
        print(f"FLAG: Found {len(null_rows)} explicitly null 'actual_spend' rows:")
        for r in null_rows:
            print(f"  - {r['period']} | {r['ward']} | {r['category']} | Reason: {r['notes']}")
            
    return data

def compute_growth(dataset, target_ward, target_category, growth_type):
    """
    Calculates growth (like MoM) strictly per-period using explicit ward and category mappings.
    Returns per-period table with formulas.
    """
    # Rule 1 & 4 Enforcement
    if not target_ward or str(target_ward).strip().lower() in ['any', 'all', '']:
        raise ValueError("REFUSAL: Cannot aggregate across wards unless explicitly instructed. Explicit ward must be provided.")
    if not target_category or str(target_category).strip().lower() in ['any', 'all', '']:
        raise ValueError("REFUSAL: Cannot aggregate across categories. Explicit category must be provided.")
    if not growth_type:
        raise ValueError("REFUSAL: --growth-type must be specified. I will not guess the formula.")
        
    if growth_type != 'MoM':
        raise ValueError(f"REFUSAL: Unsupported growth_type '{growth_type}'. Only 'MoM' is currenly instructed.")
        
    # Filter dataset for specific ward and category
    filtered = [row for row in dataset if row['ward'] == target_ward and row['category'] == target_category]
    # Ensure sequential chronological order
    filtered.sort(key=lambda x: x['period'])
    
    results = []
    for i, row in enumerate(filtered):
        period = row['period']
        actual_str = row['actual_spend'].strip()
        
        if not actual_str:
            # Handle null row securely without assuming zero
            results.append({
                'Ward': row['ward'],
                'Category': row['category'],
                'Period': period,
                'Actual Spend': 'NULL',
                'MoM Growth': 'NULL',
                'Formula': f"Flagged NULL: {row['notes']}"
            })
            continue
            
        actual_val = float(actual_str)
        if i == 0:
            growth = "n/a"
            # Rule 3: Show formula used in every output row
            formula = "n/a (first period)"
        else:
            prev_str = filtered[i-1]['actual_spend'].strip()
            if not prev_str:
                growth = "n/a"
                formula = "n/a (previous period was NULL)"
            else:
                prev_val = float(prev_str)
                if prev_val == 0:
                    growth = "n/a"
                    formula = "n/a (division by zero)"
                else:
                    g_val = (actual_val - prev_val) / prev_val * 100
                    sign = "+" if g_val >= 0 else ""
                    growth = f"{sign}{g_val:.1f}%"
                    # Rule 3: Show formula used in every output row alongside result
                    formula = f"({actual_val} - {prev_val}) / {prev_val} * 100"
                    
        results.append({
            'Ward': row['ward'],
            'Category': row['category'],
            'Period': period,
            'Actual Spend': actual_val,
            'MoM Growth': growth,
            'Formula': formula
        })
        
    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Growth Calculator")
    parser.add_argument('--input', required=True, help="Input CSV path")
    parser.add_argument('--ward', help="Target ward to calculate")
    parser.add_argument('--category', help="Target category to calculate")
    parser.add_argument('--growth-type', help="Type of growth (e.g. MoM)")
    parser.add_argument('--output', required=True, help="Output CSV path")
    
    args = parser.parse_args()
    
    try:
        data = load_dataset(args.input)
        results = compute_growth(data, args.ward, args.category, args.growth_type)
        
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            if not results:
                print("No data found for the specified ward and category.")
                return
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            
        print(f"Successfully processed {len(results)} rows and saved to {args.output}")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
