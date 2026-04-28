"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import pandas as pd
import sys

def load_dataset(file_path):
    """Load and validate the dataset."""
    try:
        df = pd.read_csv(file_path)
        required_cols = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
        
        null_count = df['actual_spend'].isnull().sum()
        null_rows = df[df['actual_spend'].isnull()]
        print(f"Loaded dataset with {len(df)} rows. Null actual_spend: {null_count}")
        if null_count > 0:
            print("Null rows:")
            for _, row in null_rows.iterrows():
                print(f"  {row['period']} · {row['ward']} · {row['category']} · {row['notes']}")
        
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} not found")
    except Exception as e:
        raise ValueError(f"Error loading dataset: {e}")

def compute_growth(df, ward, category, growth_type):
    """Compute growth for specific ward and category."""
    if growth_type not in ['MoM', 'YoY']:
        raise ValueError("Invalid growth_type. Must be 'MoM' or 'YoY'")
    
    # Filter data
    filtered = df[(df['ward'] == ward) & (df['category'] == category)].copy()
    if filtered.empty:
        raise ValueError(f"No data found for ward '{ward}' and category '{category}'")
    
    # Sort by period
    filtered['period'] = pd.to_datetime(filtered['period'])
    filtered = filtered.sort_values('period')
    
    results = []
    prev_spend = None
    for _, row in filtered.iterrows():
        period = row['period'].strftime('%Y-%m')
        actual_spend = row['actual_spend']
        flag = ''
        growth = None
        formula = ''
        
        if pd.isnull(actual_spend):
            flag = row['notes']
        else:
            if prev_spend is not None and prev_spend != 0:
                if growth_type == 'MoM':
                    growth = ((actual_spend - prev_spend) / prev_spend) * 100
                    formula = f"(({actual_spend} - {prev_spend}) / {prev_spend}) * 100"
                # YoY not implemented since no previous year data
            prev_spend = actual_spend
        
        results.append({
            'period': period,
            'actual_spend': actual_spend if not pd.isnull(actual_spend) else 'NULL',
            'growth_percentage': f"{growth:.1f}%" if growth is not None else 'NULL',
            'formula_used': formula,
            'flag': flag
        })
    
    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to budget CSV")
    parser.add_argument("--ward", required=True, help="Ward name")
    parser.add_argument("--category", required=True, help="Category name")
    parser.add_argument("--growth-type", required=True, choices=['MoM', 'YoY'], help="Growth type")
    parser.add_argument("--output", required=True, help="Output CSV path")
    
    args = parser.parse_args()
    
    if args.growth_type == 'YoY':
        print("YoY growth not supported (no previous year data)")
        sys.exit(1)
    
    try:
        df = load_dataset(args.input)
        results = compute_growth(df, args.ward, args.category, args.growth_type)
        
        output_df = pd.DataFrame(results)
        output_df.to_csv(args.output, index=False)
        print(f"Results written to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
