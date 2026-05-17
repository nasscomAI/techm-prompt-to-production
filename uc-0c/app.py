import argparse
import pandas as pd
import sys

def load_dataset(filepath):
    """
    Reads a CSV file, validates its columns, and reports the count 
    and specific rows of any null values before returning the dataset.
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        sys.exit(1)
        
    required_columns = {'period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes'}
    if not required_columns.issubset(df.columns):
        print(f"Error: Missing columns. Expected {required_columns}")
        sys.exit(1)
        
    # Flag every null row before computing — report null reason from the notes column
    null_mask = df['actual_spend'].isnull()
    null_rows = df[null_mask]
    
    if not null_rows.empty:
        print(f"Found {len(null_rows)} rows with null 'actual_spend'.")
        for idx, row in null_rows.iterrows():
            period = row.get('period', 'Unknown')
            ward = row.get('ward', 'Unknown')
            cat = row.get('category', 'Unknown')
            note = row.get('notes', 'No reason provided')
            print(f"Flagged Null Row: Period: {period}, Ward: {ward}, Category: {cat} - Reason: {note}")
            
    return df, null_rows

def compute_growth(df, ward, category, growth_type):
    """
    Computes growth metrics for a specific ward and category, returning a per-period table 
    that includes the exact formula used.
    """
    if not growth_type:
        print("Error: --growth-type not specified. Refusing to guess the formula. Please explicitly provide --growth-type.")
        sys.exit(1)
        
    if not ward or ward.lower() == 'any' or not category or category.lower() == 'any':
        print("Error: Refusing to aggregate across wards or categories. Please provide specific --ward and --category.")
        sys.exit(1)
        
    # Filter dataset strictly to per-ward and per-category level
    filtered_df = df[(df['ward'] == ward) & (df['category'] == category)].copy()
    
    if filtered_df.empty:
        print(f"No data found for Ward: {ward} and Category: {category}")
        sys.exit(1)
        
    # Sort by period to ensure sequential calculation
    filtered_df = filtered_df.sort_values('period')
    
    if growth_type == 'MoM':
        shift_amount = 1
    elif growth_type == 'YoY':
        shift_amount = 12
    else:
        print(f"Error: Unsupported growth type '{growth_type}'")
        sys.exit(1)
        
    results = []
    
    actuals = filtered_df['actual_spend'].values
    periods = filtered_df['period'].values
    notes = filtered_df['notes'].values
    
    for i in range(len(filtered_df)):
        current_period = periods[i]
        current_val = actuals[i]
        current_note = notes[i]
        
        if pd.isnull(current_val):
            growth_val = "NULL"
            formula_used = "Not computed (Null actual_spend)"
        else:
            if i >= shift_amount:
                prev_val = actuals[i - shift_amount]
                if pd.isnull(prev_val):
                    growth_val = "NULL"
                    formula_used = "Not computed (Previous period actual_spend is null)"
                elif prev_val == 0:
                    growth_val = "N/A"
                    formula_used = "Not computed (Previous period actual_spend is zero)"
                else:
                    growth_metric = (current_val - prev_val) / prev_val
                    sign = "+" if growth_metric > 0 else ""
                    growth_val = f"{sign}{growth_metric * 100:.1f}%"
                    formula_used = f"({current_val} - {prev_val}) / {prev_val} * 100 ({growth_type})"
            else:
                growth_val = "N/A"
                formula_used = "Not computed (No previous period available)"
                
        results.append({
            'period': current_period,
            'ward': ward,
            'category': category,
            'actual_spend': current_val if not pd.isnull(current_val) else "NULL",
            'notes': current_note if not pd.isnull(current_note) else "",
            f'{growth_type}_growth': growth_val,
            'formula_used': formula_used
        })
        
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Calculate budget growth metrics.')
    parser.add_argument('--input', required=True, help='Path to the input CSV file')
    parser.add_argument('--ward', help='Specific ward to filter on (do not use "any")')
    parser.add_argument('--category', help='Specific category to filter on (do not use "any")')
    parser.add_argument('--growth-type', help='Growth type (e.g., MoM, YoY)')
    parser.add_argument('--output', required=True, help='Path to the output CSV file')
    
    args = parser.parse_args()
    
    # Enforce rules from agents.md
    if not args.growth_type:
        print("Error: --growth-type not specified. Refusing to guess formula. Please explicitly provide --growth-type.")
        sys.exit(1)
        
    if not args.ward or args.ward.lower() == 'any' or not args.category or args.category.lower() == 'any':
        print("Error: --ward and --category must be explicitly provided. Refusing to aggregate across wards or categories.")
        sys.exit(1)

    # Execute skills
    df, null_rows = load_dataset(args.input)
    output_df = compute_growth(df, args.ward, args.category, args.growth_type)
    
    # Save output
    output_df.to_csv(args.output, index=False)
    print(f"Output successfully written to {args.output}")

if __name__ == '__main__':
    main()
