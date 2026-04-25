"""
UC-0A — Complaint Classifier
Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import os
import re

# Configuration based on agents.md enforcement rules
CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "pit", "hole"],
    "Flooding": ["flood", "flooding", "waterlogging", "inundation", "overflow"],
    "Streetlight": ["light", "streetlight", "street light", "lamp", "darkness"],
    "Waste": ["garbage", "trash", "waste", "litter", "dump"],
    "Noise": ["noise", "loud", "sound", "music"],
    "Road Damage": ["crack", "road broken", "asphalt", "rugged"],
    "Heritage Damage": ["heritage", "monument", "statue", "ancient"],
    "Heat Hazard": ["heat", "hot", "sunstroke", "exhaustion"],
    "Drain Blockage": ["drain", "sewage", "gutter", "clog"],
}

URGENT_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance", 
    "fire", "hazard", "fell", "collapse"
]

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: category, priority, reason, flag
    """
    description = row.get("description", "").lower()
    
    # 1. Determine Category
    assigned_category = "Other"
    found_keyword = None
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            # Match whole words only
            if re.search(r'\b' + re.escape(kw) + r'\b', description):
                assigned_category = category
                found_keyword = kw
                break
        if assigned_category != "Other":
            break
            
    # 2. Determine Priority
    priority = "Standard"
    urgent_keyword = None
    for kw in URGENT_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', description):
            priority = "Urgent"
            urgent_keyword = kw
            break
            
    # 3. Generate Reason
    reason_parts = []
    if assigned_category != "Other":
        reason_parts.append(f"categorized as {assigned_category} due to the word '{found_keyword}'")
    else:
        reason_parts.append("category could not be determined from the description")
        
    if priority == "Urgent":
        reason_parts.append(f"flagged as Urgent because it mentions '{urgent_keyword}'")
    
    reason = ". ".join(reason_parts).capitalize() + "."
    # Ensure it's one sentence as per enforcement rule
    reason = reason.replace(". ", " and ").replace("..", ".")
    
    # 4. Set Flag
    flag = "NEEDS_REVIEW" if assigned_category == "Other" else ""
    
    return {
        "category": assigned_category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    results = []
    fieldnames = []
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            if not fieldnames:
                print("Error: Input CSV is empty or invalid.")
                return
            
            # Prepare output fieldnames
            output_fieldnames = fieldnames + ["category", "priority", "reason", "flag"]
            
            for row in reader:
                classification = classify_complaint(row)
                row.update(classification)
                results.append(row)
                
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
    except Exception as e:
        print(f"An error occurred during batch processing: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
