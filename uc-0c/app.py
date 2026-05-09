"""
UC-0C app.py — Implementation for growth calculation.
"""
import argparse
import pandas as pd
import csv

def load_dataset(file_path):
    """
    Reads CSV, validates columns, reports null count and which rows before returning.
    Input: File path (string) to the CSV file
    Output: Pandas DataFrame with loaded data
    Error handling: Raises ValueError if required columns missing or file cannot be read; reports nulls.
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Cannot read file: {e}")
    
    required_cols = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns: {[col for col in required_cols if col not in df.columns]}")
    
    null_count = df['actual_spend'].isnull().sum()
    null_rows = df[df['actual_spend'].isnull()][['period', 'ward', 'category', 'notes']]
    report = f"Null count in actual_spend: {null_count}\n"
    if null_count > 0:
        report += "Null rows:\n" + null_rows.to_string(index=False)
    print(report)
    return df

def compute_growth(ward, category, growth_type, df):
    """
    Takes ward + category + growth_type, returns per-period table with formula shown.
    Input: Ward (string), category (string), growth_type (string), dataset (Pandas DataFrame)
    Output: List of dictionaries with period, actual_spend, growth, formula
    Error handling: Raises ValueError if ward/category not found or growth_type invalid; flags nulls.
    """
    if growth_type != 'MoM':
        raise ValueError("Invalid growth_type. Only 'MoM' is supported. Refusing to assume.")
    
    filtered = df[(df['ward'] == ward) & (df['category'] == category)]
    if filtered.empty:
        raise ValueError(f"Ward '{ward}' and category '{category}' not found in dataset.")
    
    # Sort by period (assuming YYYY-MM format)
    filtered = filtered.sort_values('period')
    
    results = []
    prev_spend = None
    for _, row in filtered.iterrows():
        period = row['period']
        spend = row['actual_spend']
        if pd.isnull(spend):
            growth = 'NULL'
            formula = f"Flagged null: {row['notes']}"
        else:
            if prev_spend is not None and prev_spend != 0:
                growth_val = ((spend - prev_spend) / prev_spend) * 100
                growth = f"{growth_val:+.1f}%"  # + for positive
                formula = f"(({spend} - {prev_spend}) / {prev_spend}) * 100 = {growth}"
            else:
                growth = 'N/A'
                formula = "First period or previous spend is zero/None"
            prev_spend = spend
        results.append({
            'period': period,
            'actual_spend': spend if not pd.isnull(spend) else 'NULL',
            'MoM_growth': growth,
            'formula': formula
        })
    return results

def main():
    parser = argparse.ArgumentParser(description="Calculate MoM growth for ward and category.")
    parser.add_argument('--input', required=True, help="Path to input CSV file")
    parser.add_argument('--ward', required=True, help="Ward name")
    parser.add_argument('--category', required=True, help="Category name")
    parser.add_argument('--growth-type', required=True, help="Growth type (only MoM supported)")
    parser.add_argument('--output', required=True, help="Path to output CSV file")
    
    args = parser.parse_args()
    
    # Enforcement: If growth-type not specified, refuse and ask (but since required, it's provided)
    # Assuming it's provided via args.
    
    df = load_dataset(args.input)
    results = compute_growth(args.ward, args.category, args.growth_type, df)
    
    # Write to CSV
    with open(args.output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['period', 'actual_spend', 'MoM_growth', 'formula'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Output written to {args.output}")

if __name__ == "__main__":
    main()
