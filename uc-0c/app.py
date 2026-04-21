"""
UC-0C app.py — Growth Rate Calculator
Calculates month-over-month growth rates for municipal budget data per ward and category.
"""
import argparse
import pandas as pd
import sys

def load_dataset(file_path):
    """
    Reads the CSV budget data file, validates the required columns,
    and reports the total null count and details of which rows have null actual_spend values.
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file '{file_path}' not found")
    
    required_cols = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns. Required: {required_cols}, Found: {list(df.columns)}")
    
    null_rows = df[df['actual_spend'].isnull()]
    if not null_rows.empty:
        print(f"Found {len(null_rows)} null rows in actual_spend:")
        for idx, row in null_rows.iterrows():
            print(f"- {row['period']} · {row['ward']} · {row['category']}: {row['notes']}")
    
    return df

def compute_growth(df, ward, category, growth_type):
    """
    Takes a specific ward, category, and growth type, filters the data accordingly,
    and computes growth rates for each period, showing the formula used.
    """
    if growth_type not in ['MoM', 'YoY']:
        raise ValueError("Invalid growth_type. Must be 'MoM' or 'YoY'")
    
    if growth_type == 'YoY':
        raise ValueError("YoY growth not supported with current data (only 2024 available)")
    
    filtered = df[(df['ward'] == ward) & (df['category'] == category)].copy()
    if filtered.empty:
        raise ValueError(f"No data found for ward '{ward}' and category '{category}'")
    
    # Convert period to datetime for sorting
    filtered['period_dt'] = pd.to_datetime(filtered['period'])
    filtered = filtered.sort_values('period_dt')
    
    results = []
    prev_spend = None
    
    for idx, row in filtered.iterrows():
        period = row['period']
        actual = row['actual_spend']
        
        if pd.isna(actual):
            growth = f"NULL - {row['notes']}"
            formula = "N/A (null value)"
        else:
            if prev_spend is not None and prev_spend != 0:
                growth_pct = ((actual - prev_spend) / prev_spend) * 100
                growth = f"{growth_pct:.1f}%"
                formula = f"(({actual} - {prev_spend}) / {prev_spend}) * 100 = {growth}"
            else:
                growth = "N/A (no previous data)"
                formula = "N/A"
            prev_spend = actual
        
        results.append({
            'period': period,
            'actual_spend': actual if not pd.isna(actual) else 'NULL',
            'growth_rate': growth,
            'formula': formula
        })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Calculate growth rates for municipal budget data")
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--ward', required=True, help='Ward name to filter by')
    parser.add_argument('--category', required=True, help='Category name to filter by')
    parser.add_argument('--growth-type', required=True, choices=['MoM', 'YoY'], help='Type of growth calculation')
    parser.add_argument('--output', required=True, help='Path to output CSV file')
    
    args = parser.parse_args()
    
    try:
        df = load_dataset(args.input)
        result = compute_growth(df, args.ward, args.category, args.growth_type)
        result.to_csv(args.output, index=False)
        print(f"Output written to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
