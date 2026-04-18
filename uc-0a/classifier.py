"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import re

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = row.get("description", "").lower()
    
    # Check for priority keywords
    urgent_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    urgent_matches = []
    
    for kw in urgent_keywords:
        if kw in description:
            priority = "Urgent"
            urgent_matches.append(kw)
            
    # Check for exact category strings only - no variations
    allowed_categories = [
        "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
        "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
    ]
    
    found_categories = []
    
    for cat in allowed_categories:
        if cat.lower() in description:
            found_categories.append(cat)
                
    if len(found_categories) == 1:
        category = found_categories[0]
        flag = ""
        reason = f"Classified as {category} because description mentions it exactly."
    elif len(found_categories) > 1:
        category = ""
        flag = "NEEDS_REVIEW"
        reason = f"Ambiguous category. Description mentions exact keywords for {', '.join(found_categories)}."
    else:
        category = ""
        flag = "NEEDS_REVIEW"
        reason = "Could not definitively determine category from the text."
        
    if priority == "Urgent":
        reason += f" Priority is Urgent due to severity keyword(s): {', '.join(urgent_matches)}."
        
    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }

def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    results = []
    fieldnames = []
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    result = classify_complaint(row)
                    out_row = {**row, **result}
                    results.append(out_row)
                    if not fieldnames:
                        fieldnames = list(row.keys()) + ["category", "priority", "reason", "flag"]
                except Exception as e:
                    print(f"Error processing row {row.get('complaint_id', 'unknown')}: {e}")
                    results.append(row)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            if not fieldnames:
                fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
                
            final_fieldnames = []
            for f in fieldnames:
                if f not in final_fieldnames:
                    final_fieldnames.append(f)
                    
            writer = csv.DictWriter(outfile, fieldnames=final_fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
    except Exception as e:
        print(f"Error writing output file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
