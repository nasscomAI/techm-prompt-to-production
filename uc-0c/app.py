"""
UC-0C app.py — Financial Growth Calculator
"""
import argparse
import csv
import sys

def load_dataset(input_path: str, target_ward: str, target_category: str) -> list:
    """Read the CSV dataset, filter by ward and category, and report nulls."""
    
    if target_ward.lower() == "any" or target_category.lower() == "any":
        print("[ERROR] Refusing to aggregate across wards or categories. Please specify exact ward and category.")
        sys.exit(1)
        
    filtered_data = []
    null_count = 0
    null_details = []

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Count nulls across the whole dataset as required by the spec to "report null count"
                if not row['actual_spend'].strip():
                    null_count += 1
                    null_details.append(f"{row['period']} · {row['ward']} · {row['category']} (Reason: {row['notes']})")

                if row['ward'] == target_ward and row['category'] == target_category:
                    filtered_data.append(row)
                    
    except Exception as e:
        print(f"[ERROR] Could not read file {input_path}: {e}")
        sys.exit(1)

    print(f"Total nulls in dataset: {null_count}")
    for detail in null_details:
        print(f" - {detail}")
        
    return sorted(filtered_data, key=lambda x: x['period'])

def compute_growth(data: list, growth_type: str) -> list:
    """Calculate MoM growth for the filtered dataset."""
    
    if not growth_type:
        print("[ERROR] --growth-type not specified. Refusing to guess. Please specify MoM or YoY.")
        sys.exit(1)
        
    if growth_type.upper() != "MOM":
        print(f"[ERROR] Unsupported growth type: {growth_type}. Currently only MoM is fully implemented in this logic.")
        sys.exit(1)

    results = []
    
    for i in range(len(data)):
        current_row = data[i]
        period = current_row['period']
        ward = current_row['ward']
        category = current_row['category']
        notes = current_row['notes']
        
        current_spend_str = current_row['actual_spend'].strip()
        
        # Rule 2: Flag nulls before computing
        if not current_spend_str:
            results.append({
                "ward": ward,
                "category": category,
                "period": period,
                "actual_spend": "NULL",
                "growth": "NULL",
                "formula_used": f"Flagged NULL: {notes} - not computed"
            })
            continue
            
        current_spend = float(current_spend_str)
        
        if i == 0:
            results.append({
                "ward": ward,
                "category": category,
                "period": period,
                "actual_spend": current_spend,
                "growth": "n/a",
                "formula_used": "First period - no previous data"
            })
            continue
            
        prev_row = data[i-1]
        prev_spend_str = prev_row['actual_spend'].strip()
        
        if not prev_spend_str:
            results.append({
                "ward": ward,
                "category": category,
                "period": period,
                "actual_spend": current_spend,
                "growth": "n/a",
                "formula_used": "Previous period was NULL - cannot compute"
            })
            continue
            
        prev_spend = float(prev_spend_str)
        
        # Calculate MoM
        if prev_spend == 0:
            growth_pct = 0.0
        else:
            growth_pct = ((current_spend - prev_spend) / prev_spend) * 100
            
        # Format the growth to include + or - and %
        sign = "+" if growth_pct > 0 else ""
        growth_str = f"{sign}{growth_pct:.1f}%"
        
        results.append({
            "ward": ward,
            "category": category,
            "period": period,
            "actual_spend": current_spend,
            "growth": growth_str,
            "formula_used": f"(({current_spend} - {prev_spend}) / {prev_spend}) * 100"
        })

    return results

def main():
    parser = argparse.ArgumentParser(description="UC-0C Financial Growth Calculator")
    parser.add_argument("--input", required=True, help="Path to dataset CSV")
    parser.add_argument("--ward", required=True, help="Target ward name")
    parser.add_argument("--category", required=True, help="Target category name")
    parser.add_argument("--growth-type", required=False, help="Growth type (e.g. MoM, YoY)")
    parser.add_argument("--output", required=True, help="Path to write the results CSV")
    args = parser.parse_args()

    print(f"Loading data for {args.ward} -> {args.category}...")
    filtered_data = load_dataset(args.input, args.ward, args.category)
    
    if not filtered_data:
        print("[WARNING] No data found for the specified ward and category.")
        sys.exit(0)

    print(f"Computing {args.growth_type} growth...")
    results = compute_growth(filtered_data, args.growth_type)

    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ["ward", "category", "period", "actual_spend", "growth", "formula_used"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Done. Results written to {args.output}")

if __name__ == "__main__":
    main()
