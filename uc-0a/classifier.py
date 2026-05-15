"""
UC-0A — Complaint Classifier
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on keywords in its description.
    
    Args:
        row (dict): A dictionary representing a single complaint record.
        
    Returns:
        dict: A dictionary containing the original complaint_id and newly determined 
              category, priority, reason, and flag.
    """
    description = row.get("description", "")
    if not description:
        return {
            "complaint_id": row.get("complaint_id", ""),
            "category": "Other",
            "priority": "Standard",
            "reason": "Missing description.",
            "flag": "NEEDS_REVIEW"
        }
        
    desc_lower = description.lower()
    
    # Determine Priority as per severity
    severity_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    found_severity_kw = None
    for kw in severity_keywords:
        if kw in desc_lower:
            priority = "Urgent"
            found_severity_kw = kw
            break
            
    # Determine Category of mapping
    cat_mapping = {
        "Pothole": ["pothole", "crater"],
        "Flooding": ["flood", "rainwater"],
        "Streetlight": ["streetlight", "light", "dark"],
        "Waste": ["waste", "garbage", "trash", "debris"],
        "Noise": ["noise", "drilling", "engines on", "loud", "idling"],
        "Road Damage": ["road collapsed", "road damage"],
        "Heritage Damage": ["heritage"],
        "Heat Hazard": ["heat", "sun"],
        "Drain Blockage": ["drain blocked", "drain completely blocked", "mosquito", "drain block", "drain 100% blocked"]
    }
    
    detected_cats = []
    reason_words = []
    
    for cat, keywords in cat_mapping.items():
        for kw in keywords:
            if kw in desc_lower:
                if cat not in detected_cats:
                    detected_cats.append(cat)
                reason_words.append(kw)
                
    flag = ""
    # Ambiguity check
    if len(detected_cats) > 1:
        flag = "NEEDS_REVIEW"
        category = "Other"
        reason = f"Ambiguous. Found keywords for multiple categories: {', '.join(reason_words)}."
    elif len(detected_cats) == 1:
        category = detected_cats[0]
        reason = f"Matched keyword '{reason_words[0]}'."
    else:
        category = "Other"
        flag = "NEEDS_REVIEW"
        reason = "No definitive category keywords found."
        
    if found_severity_kw:
        reason += f" Marked Urgent due to keyword '{found_severity_kw}'."

    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, and write results to a new CSV file.
    
    Args:
        input_path (str): The file path to the input CSV containing complaints.
        output_path (str): The file path where the classified results CSV should be saved.
    """
    results = []
    fieldnames = []
    try:
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            # Ensure new columns are added
            for col in ["category", "priority", "reason", "flag"]:
                if col not in fieldnames:
                    fieldnames.append(col)
                    
            for row in reader:
                try:
                    classification = classify_complaint(row)
                    row.update(classification)
                    results.append(row)
                except Exception as e:
                    print(f"Error processing row {row.get('complaint_id', '')}: {e}")
                    row["flag"] = "ERROR"
                    results.append(row)
    except Exception as e:
        print(f"Failed to read input file: {e}")
        return

    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
    except Exception as e:
        print(f"Failed to write output file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
