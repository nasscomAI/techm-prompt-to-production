"""
UC-0C app.py
Deterministically implements the strict RICE rules to calculate growth without aggregations or silent null handling.
"""
import argparse
import csv
import sys
from typing import List, Dict, Tuple

def load_dataset(filepath: str) -> Tuple[List[Dict], List[Dict]]:
    """
    skill: load_dataset
    Reads CSV, validates columns, reports null count and which rows before returning.
    Returns: (all_rows, null_rows_summary)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Ensure required columns are present
            required_cols = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}
            if not required_cols.issubset(set(reader.fieldnames or [])):
                print(f"[ERROR] Missing required columns. Found: {reader.fieldnames}", file=sys.stderr)
                sys.exit(1)
            
            rows = list(reader)
    except Exception as e:
        print(f"[ERROR] Could not read file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)

    null_rows = []
    
    # Validation step: identify exact null rows
    for row in rows:
        spend = row.get("actual_spend", "").strip()
        if not spend:
            null_rows.append(row)

    print(f"\n[DATA VALIDATION] Found {len(null_rows)} explicitly NULL actual_spend records:")
    for nr in null_rows:
        print(f"  -> {nr['period']} | {nr['ward']} | {nr['category']} | Reason Note: '{nr['notes']}'")
        
    return rows, null_rows

def compute_growth(rows: List[Dict], ward: str, category: str, growth_type: str) -> List[Dict]:
    """
    skill: compute_growth
    Takes ward + category + growth_type, returns per-period table with formula shown.
    Refuses cross ward/category aggregations perfectly by strictly filtering to the parameters.
    """
    # Enforce Rule 1 & Rule 4 explicitly
    if not ward or not category:
        print("\n[REFUSAL - RULE 1] I am instructed to NEVER aggregate across wards or categories unless explicitly instructed. You must provide specific --ward and --category targets.", file=sys.stderr)
        sys.exit(1)
        
    if not growth_type:
        print("\n[REFUSAL - RULE 4] I cannot assume the growth formula. Please explicitly specify --growth-type (e.g. MoM or YoY).", file=sys.stderr)
        sys.exit(1)

    # Filter to specific constraints
    filtered = [r for r in rows if r["ward"] == ward and r["category"] == category]
    
    # Sort strictly by period just in case
    filtered.sort(key=lambda x: x["period"])
    
    computed_output = []
    
    for i, row in enumerate(filtered):
        period = row["period"]
        spend_str = row.get("actual_spend", "").strip()
        
        # Enforce Rule 2: Note the null
        if not spend_str:
            computed_output.append({
                "Ward": ward,
                "Category": category,
                "Period": period,
                "Actual Spend (Lakh)": "NULL",
                "Growth": "FLAGGED_NULL",
                "Formula": f"NULL value detected due to: '{row['notes']}' — Computation Skipped"
            })
            continue
            
        current_val = float(spend_str)
        growth_str = "N/A"
        formula_str = "First period available; no prior data to compare."
        
        if growth_type.upper() == "MOM":
            if i > 0:
                prev_spend_str = filtered[i-1].get("actual_spend", "").strip()
                if not prev_spend_str:
                    growth_str = "N/A"
                    formula_str = "Previous month's value was NULL. Computation Skipped."
                else:
                    prev_val = float(prev_spend_str)
                    if prev_val == 0.0:
                        growth_str = "INF"
                        formula_str = f"({current_val} - 0) / 0"
                    else:
                        growth_pct = ((current_val - prev_val) / prev_val) * 100
                        sign = "+" if growth_pct > 0 else ""
                        growth_str = f"{sign}{growth_pct:.1f}%"
                        formula_str = f"({current_val} - {prev_val}) / {prev_val} * 100"
                        
        elif growth_type.upper() == "YOY":
            # Just simple matching for previous year same month if available.
            try:
                yyyy, mm = period.split('-')
                prev_period = f"{int(yyyy)-1}-{mm}"
                prev_row = next((r for r in filtered if r["period"] == prev_period), None)
                if prev_row:
                    prev_spend_str = prev_row.get("actual_spend", "").strip()
                    if not prev_spend_str:
                        growth_str = "N/A"
                        formula_str = f"Previous year month ({prev_period}) value was NULL. Computation Skipped."
                    else:
                        prev_val = float(prev_spend_str)
                        if prev_val == 0.0:
                            growth_str = "INF"
                            formula_str = f"({current_val} - 0) / 0"
                        else:
                            growth_pct = ((current_val - prev_val) / prev_val) * 100
                            sign = "+" if growth_pct > 0 else ""
                            growth_str = f"{sign}{growth_pct:.1f}%"
                            formula_str = f"({current_val} - {prev_val}) / {prev_val} * 100"
                else:
                    growth_str = "N/A"
                    formula_str = f"No data found for {prev_period}"
            except ValueError:
                growth_str = "ERROR"
                formula_str = "Invalid period format."
        else:
            print(f"\n[REFUSAL - RULE 4] Unsupported growth type '{growth_type}'. Use MoM or YoY.", file=sys.stderr)
            sys.exit(1)

        computed_output.append({
            "Ward": ward,
            "Category": category,
            "Period": period,
            "Actual Spend (Lakh)": str(current_val),
            "Growth": growth_str,
            "Formula": formula_str
        })
        
    return computed_output

def main():
    parser = argparse.ArgumentParser()
    # We do not use required=True for ward/category/growth_type to explicitly catch and REFUSE as defined by RICE rules.
    parser.add_argument("--input", required=True, help="Path to input dataset (CSV)")
    parser.add_argument("--output", required=True, help="Path to output computations (CSV)")
    parser.add_argument("--ward", help="Target Ward constraint")
    parser.add_argument("--category", help="Target Category constraint")
    parser.add_argument("--growth-type", dest="growth_type", help="Formula (MoM or YoY)")
    
    args = parser.parse_args()
    
    # 1. Dataset parsing & validation logic
    print("Executing strict skill: load_dataset...")
    data_rows, _ = load_dataset(args.input)
    
    # 2. Compute constrained growth
    print("\nExecuting strict skill: compute_growth...")
    results = compute_growth(
        rows=data_rows, 
        ward=args.ward, 
        category=args.category, 
        growth_type=args.growth_type
    )
    
    if not results:
        print("[WARN] No records found for the specific Ward and Category intersection. Check spelling.")
        
    # 3. Output results safely
    try:
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
                writer.writeheader()
                writer.writerows(results)
        print(f"\n[SUCCESS] Computation saved safely to {args.output}")
    except Exception as e:
        print(f"[ERROR] Could not write output: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
