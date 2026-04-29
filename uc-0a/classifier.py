"""
UC-0A — Complaint Classifier
Implementation based on agents.md and skills.md.
"""
import argparse
import csv
import os

# Configuration from agents.md
ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance", 
    "fire", "hazard", "fell", "collapse"
]

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "hole", "pavement hole"],
    "Flooding": ["flood", "waterlogging", "water logged", "rain water", "underpass flooded"],
    "Streetlight": ["streetlight", "street light", "lamp", "dark at night", "flickering"],
    "Waste": ["waste", "garbage", "trash", "bins", "overflowing", "smell"],
    "Noise": ["noise", "loud", "music", "sound"],
    "Road Damage": ["road surface", "cracked", "sinking", "broken road"],
    "Heritage Damage": ["heritage", "historical", "monument"],
    "Heat Hazard": ["heat", "temperature", "sun"],
    "Drain Blockage": ["drain", "drainage", "sewage", "clogged", "blocked"]
}

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on the description.
    Returns: dict with keys: category, priority, reason, flag
    """
    description = row.get("description", "").lower()
    
    # 1. Category Classification
    detected_category = "Other"
    found_keyword = ""
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description:
                detected_category = category
                found_keyword = keyword
                break
        if detected_category != "Other":
            break
            
    # 2. Priority Assignment
    priority = "Standard"
    severity_trigger = ""
    for kw in SEVERITY_KEYWORDS:
        if kw in description:
            priority = "Urgent"
            severity_trigger = kw
            break
    
    # 3. Flagging Ambiguity
    flag = ""
    if detected_category == "Other":
        flag = "NEEDS_REVIEW"
        
    # 4. Reason Generation
    if detected_category != "Other":
        if priority == "Urgent":
            reason = f"Classified as {detected_category} due to '{found_keyword}' and prioritized as Urgent because of '{severity_trigger}'."
        else:
            reason = f"Classified as {detected_category} because the description mentions '{found_keyword}'."
    else:
        reason = "Category could not be determined from the description text."
        
    return {
        "category": detected_category,
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
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['category', 'priority', 'reason', 'flag']
            
            for row in reader:
                try:
                    classification = classify_complaint(row)
                    row.update(classification)
                    results.append(row)
                except Exception as e:
                    print(f"Error processing row {row.get('complaint_id', 'unknown')}: {e}")
                    row.update({
                        "category": "Other",
                        "priority": "Low",
                        "reason": f"Error: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })
                    results.append(row)
    except Exception as e:
        print(f"Failed to read input file: {e}")
        return

    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    except Exception as e:
        print(f"Failed to write output file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
