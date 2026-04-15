"""
UC-0C app.py — Starter file.
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""
import argparse
import csv

def load_dataset(input_path: str):
    """
    Read the ward budget CSV and track nulls.
    """
    data = []
    null_report = []
    try:
        with open(input_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row["actual_spend"] or row["actual_spend"].strip() == "":
                    null_report.append({
                        "period": row["period"],
                        "ward": row["ward"],
                        "category": row["category"],
                        "notes": row["notes"]
                    })
                    # Use None for internal representation
                    row["actual_spend"] = None
                else:
                    try:
                        row["actual_spend"] = float(row["actual_spend"])
                    except ValueError:
                        row["actual_spend"] = None
                data.append(row)
    except Exception as e:
        print(f"Error loading dataset: {e}")
    return data, null_report


def compute_growth(data, target_ward, target_cat, growth_type):
    """
    Compute growth (MoM) for specific ward/category.
    """
    # Filter data
    filtered = [r for r in data if r["ward"] == target_ward and r["category"] == target_cat]
    
    # Sort by period
    filtered.sort(key=lambda x: x["period"])
    
    results = []
    for i in range(len(filtered)):
        curr = filtered[i]
        prev = filtered[i-1] if i > 0 else None
        
        row_res = {
            "ward": curr["ward"],
            "category": curr["category"],
            "period": curr["period"],
            "actual_spend": curr["actual_spend"],
            "growth": "N/A",
            "formula": "N/A",
            "flag": ""
        }
        
        if curr["actual_spend"] is None:
            row_res["flag"] = "NULL_VALUE_MISSING"
            # Try to find the reason from global notes if needed or just mark it
            # In this simple implementation, we assume the load_dataset already reported it
        elif prev and prev["actual_spend"] is not None:
            if growth_type.upper() == "MOM":
                c = curr["actual_spend"]
                p = prev["actual_spend"]
                try:
                    growth = (c - p) / p
                    row_res["growth"] = f"{growth:+.1%}"
                    row_res["formula"] = f"(Current[{c}] - Previous[{p}]) / Previous[{p}]"
                except ZeroDivisionError:
                    row_res["growth"] = "N/A"
            else:
                row_res["growth"] = "ERROR_UNSUPPORTED_TYPE"
        
        results.append(row_res)
        
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0C Budget Analyst")
    parser.add_argument("--input", required=True)
    parser.add_argument("--ward", required=False)
    parser.add_argument("--category", required=False)
    parser.add_argument("--growth-type", required=False)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    # RICE Enforcement: Refusal conditions
    if not args.ward or not args.category:
        print("ERROR: Ward and Category must be specified. Aggregation is not permitted.")
        exit(1)
    if not args.growth_type:
        print("ERROR: Growth-type (MoM or YoY) must be specified.")
        exit(1)
        
    data, null_report = load_dataset(args.input)
    
    # Report nulls before computing
    if null_report:
        print("\n[DATA QUALITY REPORT] Null values found:")
        for n in null_report:
            if n["ward"] == args.ward and n["category"] == args.category:
                print(f"- {n['period']}: {n['notes']}")
    
    results = compute_growth(data, args.ward, args.category, args.growth_type)
    
    fieldnames = ["ward", "category", "period", "actual_spend", "growth", "formula", "flag"]
    with open(args.output, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nDone. Results written to {args.output}")
