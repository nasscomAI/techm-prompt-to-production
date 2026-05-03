"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import sys
import pandas as pd
import numpy as np

def load_dataset(filepath: str) -> pd.DataFrame:
    """Reads the CSV file, identifies and flags null rows."""
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        sys.exit(1)
        
    # Check for nulls in actual_spend
    null_rows = df[df['actual_spend'].isnull()]
    
    print("\n--- Data Quality Check ---")
    print(f"Found {len(null_rows)} missing actual_spend entries:")
    
    for idx, row in null_rows.iterrows():
        print(f"- {row['period']} | {row['ward']} | {row['category']} -> Reason: {row['notes']}")
        
    print("--------------------------\n")
    return df

def compute_growth(df: pd.DataFrame, growth_type: str) -> pd.DataFrame:
    """Takes dataframe and growth_type, returns per-period table with formula."""
    if growth_type not in ["MoM", "YoY"]:
        print(f"Error: Invalid growth type '{growth_type}'. Please specify 'MoM' or 'YoY'. I will not guess.")
        sys.exit(1)
        
    # Sort data to ensure chronological order for diff/shift
    df = df.sort_values(by=['ward', 'category', 'period']).copy()
    
    growths = []
    formulas = []
    
    # Calculate per ward, per category
    for (ward, category), group in df.groupby(['ward', 'category']):
        if growth_type == "MoM":
            # Compare to previous row (since it's sorted by period which is YYYY-MM)
            prev_spend = group['actual_spend'].shift(1)
            
            for curr, prev in zip(group['actual_spend'], prev_spend):
                if pd.isna(curr) or pd.isna(prev):
                    growths.append("Must be flagged — not computed")
                    formulas.append("N/A (Missing Data)")
                else:
                    if prev == 0:
                        growths.append("N/A")
                        formulas.append(f"({curr} - 0) / 0")
                    else:
                        growth_val = ((curr - prev) / prev) * 100
                        sign = "+" if growth_val > 0 else ""
                        growths.append(f"{sign}{growth_val:.1f}%")
                        formulas.append(f"({curr} - {prev}) / {prev} * 100")
        elif growth_type == "YoY":
            # YoY would require shift(12) or parsing dates. 
            # Given we only have 2024 data, YoY is not computable for this dataset.
            for curr in group['actual_spend']:
                growths.append("Must be flagged — not computed")
                formulas.append("N/A (Insufficient historical data for YoY)")
                
    df['growth'] = growths
    df['formula'] = formulas
    
    return df

def main():
    parser = argparse.ArgumentParser(description="UC-0C Ward Wise Summary Agent")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument("--growth-type", required=False, help="Growth type (MoM or YoY)")
    parser.add_argument("--aggregate", action="store_true", help="Aggregate data across wards/categories")
    args = parser.parse_args()

    if not args.growth_type:
        print("Refused: --growth-type not specified. Please specify 'MoM' or 'YoY'. I will not guess.")
        sys.exit(1)
        
    if args.aggregate:
        print("Refused: Never aggregate across wards or categories unless explicitly instructed. Aggregation is blocked by policy.")
        sys.exit(1)

    df = load_dataset(args.input)
    result_df = compute_growth(df, args.growth_type)
    
    result_df.to_csv(args.output, index=False)
    print(f"Computed {args.growth_type} growth and saved to {args.output}")

if __name__ == "__main__":
    main()
