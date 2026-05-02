import pandas as pd
import argparse
import sys
import os

def load_dataset(file_path):
    """
    Loads the CSV dataset and validates columns.
    """
    required_columns = ['period', 'ward', 'category', 'budgeted_amount', 'actual_spend', 'notes']
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
        
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
        
    # Validate columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns in CSV: {', '.join(missing_cols)}")
        sys.exit(1)
        
    return df

def compute_growth(df, ward, category):
    """
    Filters data, sorts by period, and computes MoM growth.
    """
    # Filter strictly by ward AND category
    filtered_df = df[(df['ward'] == ward) & (df['category'] == category)].copy()
    
    if filtered_df.empty:
        print(f"Error: No data found for ward '{ward}' and category '{category}'.")
        sys.exit(1)
        
    # Detect NULL values in actual_spend before sorting/processing
    null_rows = filtered_df[filtered_df['actual_spend'].isna()]
    if not null_rows.empty:
        print("\nWARNING: Detected NULL values in actual_spend:")
        print(null_rows[['period', 'ward', 'category', 'notes']].to_string(index=False))
        print("-" * 50)

    # Sort by period ascending
    filtered_df = filtered_df.sort_values(by='period').reset_index(drop=True)
    
    results = []
    previous_value = None
    
    for i, row in filtered_df.iterrows():
        current_period = row['period']
        current_spend = row['actual_spend']
        
        growth = "N/A"
        formula = ""
        
        # Edge case: First row
        if i == 0:
            growth = "N/A"
            formula = "First row → N/A"
        # Edge case: If current is NULL
        elif pd.isna(current_spend):
            growth = "FLAGGED"
            formula = "NULL value → cannot compute"
            previous_value = None # Reset previous value as per requirements
        # Edge case: If previous is NULL
        elif previous_value is None or pd.isna(previous_value):
            growth = "N/A"
            formula = "Previous value is NULL or first valid row → N/A"
        else:
            # Standard MoM growth: ((current - previous) / previous) * 100
            try:
                growth_val = ((current_spend - previous_value) / previous_value) * 100
                growth = f"{growth_val:.2f}%"
                formula = f"(({current_spend} - {previous_value}) / {previous_value}) * 100"
            except ZeroDivisionError:
                growth = "INF"
                formula = "Division by zero"
        
        results.append({
            'period': current_period,
            'ward': row['ward'],
            'category': row['category'],
            'actual_spend': current_spend,
            'growth': growth,
            'formula': formula
        })
        
        # Update previous_value for next iteration
        previous_value = current_spend
        
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="UC-0C Budget MoM Growth Analysis Tool")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--ward", required=True, help="Ward name to filter")
    parser.add_argument("--category", required=True, help="Category to filter")
    parser.add_argument("--growth-type", required=True, help="Type of growth calculation (must be 'MoM')")
    parser.add_argument("--output", required=True, help="Path to output CSV file")
    
    args = parser.parse_args()
    
    # Validate growth-type
    if args.growth_type != "MoM":
        print(f"Error: Invalid growth-type '{args.growth_type}'. Only 'MoM' is supported.")
        sys.exit(1)
        
    # Load dataset
    df = load_dataset(args.input)
    
    # Compute growth
    result_df = compute_growth(df, args.ward, args.category)
    
    # Save result to output CSV
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        result_df.to_csv(args.output, index=False)
        print(f"\nSuccess: Analysis saved to '{args.output}'")
    except Exception as e:
        print(f"Error saving output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
