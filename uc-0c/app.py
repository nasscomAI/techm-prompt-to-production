"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import csv
import sys

def load_dataset(filepath):
    """Reads CSV, validates columns, reports null count and which rows before returning."""
    expected_cols = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    data = []
    null_count = 0
    null_rows = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or reader.fieldnames != expected_cols:
                raise ValueError(f"Dataset structure invalid. Expected columns: {expected_cols}")
                
            for row in reader:
                data.append(row)
                actual = row.get('actual_spend', '').strip()
                if not actual:
                    null_count += 1
                    null_rows.append(f"Period: {row['period']}, Ward: {row['ward']}, Category: {row['category']}, Reason: {row['notes']}")
    except Exception as e:
        raise ValueError(f"Failed to load dataset: {e}")
        
    print(f"Dataset loaded. Found {null_count} deliberate null actual_spend values:")
    for nr in null_rows:
        print(f" - [NULL FLAGGED] {nr}")
        
    return data

def compute_growth(data, ward, category, growth_type):
    """Takes ward + category + growth_type, returns per-period table with formula shown."""
    if not growth_type:
        raise ValueError("REFUSAL: --growth-type not specified. Will not guess the formula.")
        
    if not ward or not category:
        raise ValueError("REFUSAL: Never aggregate across wards or categories unless explicitly instructed. Missing ward or category.")
        
    # Filter data based on explicit instruction (ward and category)
    filtered = [row for row in data if row['ward'] == ward and row['category'] == category]
            
    # Sort chronologically
    filtered.sort(key=lambda x: x['period'])
    
    results = []
    for i, row in enumerate(filtered):
        period = row['period']
        budget = row['budgeted_amount']
        actual = row['actual_spend']
        notes = row['notes']
        
        # Null handling
        if not actual.strip():
            results.append({
                'period': period,
                'ward': ward,
                'category': category,
                'budgeted_amount': budget,
                'actual_spend': 'NULL',
                'growth': 'NULL (Flagged)',
                'formula': 'Not computed',
                'notes': notes
            })
            continue
            
        actual_val = float(actual)
        
        # Growth calculation
        if growth_type.upper() == 'MOM':
            if i == 0:
                growth_str = "n/a (first period)"
                formula_str = "n/a"
            else:
                prev_actual_str = filtered[i-1]['actual_spend']
                if not prev_actual_str.strip():
                    growth_str = "n/a (previous month null)"
                    formula_str = "n/a"
                else:
                    prev_val = float(prev_actual_str)
                    if prev_val == 0:
                        growth_str = "n/a (division by zero)"
                        formula_str = f"({actual_val} - 0) / 0"
                    else:
                        growth = ((actual_val - prev_val) / prev_val) * 100
                        growth_str = f"{growth:+.1f}%"
                        formula_str = f"(({actual_val} - {prev_val}) / {prev_val}) * 100"
        else:
             growth_str = f"Unsupported type: {growth_type}"
             formula_str = "Unknown"
             
        results.append({
            'period': period,
            'ward': ward,
            'category': category,
            'budgeted_amount': budget,
            'actual_spend': actual_val,
            'growth': growth_str,
            'formula': formula_str,
            'notes': notes
        })
        
    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to input dataset CSV")
    parser.add_argument("--ward", required=False, help="Specific ward to filter by")
    parser.add_argument("--category", required=False, help="Specific category to filter by")
    parser.add_argument("--growth-type", dest="growth_type", required=False, help="Type of growth to compute (e.g., MoM)")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    
    args = parser.parse_args()
    
    try:
        data = load_dataset(args.input)
        results = compute_growth(data, args.ward, args.category, args.growth_type)
        
        if not results:
            print("No data matched the given ward and category.")
            return
            
        with open(args.output, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'growth', 'formula', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"Success. Per-period growth output written to {args.output}")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
