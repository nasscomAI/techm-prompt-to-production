"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import re

CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

SEVERITY_KEYWORDS = {
    "injury", "child", "school", "hospital", "ambulance", 
    "fire", "hazard", "fell", "collapse", "children"
}

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "potholes"],
    "Flooding": ["flood", "flooded", "flooding", "waterlog", "waterlogged"],
    "Streetlight": ["streetlight", "streetlights", "light", "lights", "dark"],
    "Waste": ["waste", "garbage", "trash", "dump"],
    "Noise": ["noise", "loud", "sound"],
    "Road Damage": ["road damage", "crack", "broken road", "road"],
    "Heritage Damage": ["heritage damage", "monument", "heritage"],
    "Heat Hazard": ["heat hazard", "heat"],
    "Drain Blockage": ["drain block", "drain blocked", "drain", "blocked drain"]
}

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    desc = str(row.get("description", "")).lower()
    
    # Determine category
    matched_categories = []
    reason_words = []
    
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', desc):
                if cat not in matched_categories:
                    matched_categories.append(cat)
                reason_words.append(kw)

    # Determine priority
    priority = "Standard"
    sev_matches = []
    for skw in SEVERITY_KEYWORDS:
        if re.search(r'\b' + re.escape(skw) + r'\b', desc) or skw in desc:
            priority = "Urgent"
            sev_matches.append(skw)
    
    reason_words.extend(sev_matches)
    
    category = "Other"
    flag = ""
    if len(matched_categories) == 1:
        category = matched_categories[0]
    elif len(matched_categories) > 1:
        if "Pothole" in matched_categories:
            category = "Pothole"
        elif "Flooding" in matched_categories and "Drain Blockage" in matched_categories:
            category = "Flooding"
        else:
            category = "Other"
            flag = "NEEDS_REVIEW"
    else:
        category = "Other"
        flag = "NEEDS_REVIEW"
        
    reason_str = "No specific keywords identified."
    if reason_words:
        unique_reasons = list(set(reason_words))
        reason_str = f"The description mentions the following terms: {', '.join(unique_reasons)}."
        
    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": category,
        "priority": priority,
        "reason": reason_str,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, \
             open(output_path, 'w', encoding='utf-8', newline='') as f_out:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            out_fields = list(fieldnames)
            for f in ['category', 'priority', 'reason', 'flag']:
                if f not in out_fields:
                    out_fields.append(f)
                    
            writer = csv.DictWriter(f_out, fieldnames=out_fields)
            writer.writeheader()
            
            for row in reader:
                try:
                    result = classify_complaint(row)
                    row['category'] = result['category']
                    row['priority'] = result['priority']
                    row['reason'] = result['reason']
                    row['flag'] = result['flag']
                    writer.writerow(row)
                except Exception as e:
                    row['flag'] = "ERROR_PROCESSING"
                    row['reason'] = str(e)
                    writer.writerow(row)
    except Exception as e:
        print(f"Error processing batch: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
