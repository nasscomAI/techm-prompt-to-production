"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import pandas as pd
import sys

def load_dataset(filepath):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
    
    # Flag every null row before computing
    null_rows = df[df['actual_spend'].isnull()]
    if not null_rows.empty:
        print(f"Found {len(null_rows)} null records. Flagging them before computation:")
        for idx, row in null_rows.iterrows():
            print(f" - Period: {row['period']} | Ward: {row['ward']} | Category: {row['category']} -> Reason: {row['notes']}")
            
    return df

def compute_growth(df, ward, category, growth_type):
    # Filter data to exact ward and category
    filtered_df = df[(df['ward'] == ward) & (df['category'] == category)].copy()
    
    if filtered_df.empty:
        print("No data found for the specified ward and category.")
        sys.exit(1)
        
    filtered_df = filtered_df.sort_values(by='period').reset_index(drop=True)
    
    # Calculate growth
    results = []
    prev_spend = None
    
    for idx, row in filtered_df.iterrows():
        period = row['period']
        spend = row['actual_spend']
        notes = row['notes'] if pd.notnull(row['notes']) else ""
        
        # If current is null, explicitly flag it instead of ignoring
        if pd.isnull(spend):
            results.append({
                "Period": period,
                "Ward": ward,
                "Category": category,
                "Actual Spend (₹ lakh)": "NULL",
                f"{growth_type} Growth": f"Must be flagged — not computed (Reason: {notes})",
                "Formula": "N/A"
            })
            prev_spend = None
            continue
            
        # Calculate MoM
        if prev_spend is None:
            growth_str = "n/a"
            formula = "n/a"
        else:
            if growth_type.upper() == "MOM":
                growth = ((spend - prev_spend) / prev_spend) * 100
                sign = "+" if growth > 0 else ""
                growth_str = f"{sign}{growth:.1f}%"
                formula = f"({spend} - {prev_spend}) / {prev_spend}"
            else:
                growth_str = "n/a"
                formula = "n/a (unsupported growth type)"
            
        results.append({
            "Period": period,
            "Ward": ward,
            "Category": category,
            "Actual Spend (₹ lakh)": spend,
            f"{growth_type} Growth": growth_str,
            "Formula": formula
        })
        
        prev_spend = spend
        
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Calculate budget growth metrics")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file")
    parser.add_argument("--ward", type=str, help="Ward name")
    parser.add_argument("--category", type=str, help="Category name")
    parser.add_argument("--growth-type", dest="growth_type", type=str, help="Growth type (e.g. MoM)")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file")
    
    args = parser.parse_args()
    
    # 4. If --growth-type not specified — refuse and ask, never guess
    if not args.growth_type:
        print("REFUSAL: --growth-type not specified. Refusing to guess (e.g., MoM or YoY). Please specify.")
        sys.exit(1)
        
    # 1. Never aggregate across wards or categories unless explicitly instructed — refuse if asked
    if not args.ward or not args.category:
        print("REFUSAL: Missing --ward or --category. Never aggregate across wards or categories unless explicitly instructed. Refuse to proceed.")
        sys.exit(1)
        
    if args.growth_type.upper() != "MOM":
        print(f"ERROR: Only MoM growth is currently supported. Requested: {args.growth_type}")
        sys.exit(1)
        
    df = load_dataset(args.input)
        
    result_df = compute_growth(df, args.ward, args.category, args.growth_type)
    
    result_df.to_csv(args.output, index=False)
    print(f"Success. Wrote output to {args.output}")

if __name__ == "__main__":
    main()
