"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = row.get("description", "").lower()
    
    # 1. Define keyword mappings for categories
    category_mapping = {
        "Pothole": ["pothole"],
        "Flooding": ["flood", "waterlogging"],
        "Streetlight": ["streetlight", "lights out", "dark", "sparking"],
        "Waste": ["waste", "garbage", "dump", "dead animal"],
        "Noise": ["noise", "music", "loud"],
        "Road Damage": ["cracked", "sinking", "manhole", "footpath", "tiles broken"],
        "Heritage Damage": ["heritage"],
        "Heat Hazard": ["heat"],
        "Drain Blockage": ["drain block"]
    }
    
    found_categories = []
    matched_cat_keywords = []
    for cat, keywords in category_mapping.items():
        for kw in keywords:
            if kw in description:
                if cat not in found_categories:
                    found_categories.append(cat)
                matched_cat_keywords.append(kw)
    
    # Determine Category and Flag
    category = "Other"
    flag = ""
    
    if len(found_categories) == 1:
        category = found_categories[0]
    else:
        # Ambiguous (0 or >1 matches)
        category = "Other"
        flag = "NEEDS_REVIEW"

    # 2. Determine Priority
    severity_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    matched_sev_kw = None
    for kw in severity_keywords:
        if kw in description:
            priority = "Urgent"
            matched_sev_kw = kw
            break

    # 3. Determine Reason
    if priority == "Urgent":
        reason = f"The complaint is marked Urgent because it contains the severity keyword '{matched_sev_kw}'."
    elif flag == "NEEDS_REVIEW":
        if len(found_categories) > 1:
            reason = f"The description is ambiguous as it contains keywords for multiple categories: {', '.join(found_categories)}."
        else:
            reason = "The complaint could not be clearly classified into a specific category."
    else:
        kw = matched_cat_keywords[0] if matched_cat_keywords else "specific keywords"
        reason = f"The complaint is classified as {category} because it mentions '{kw}'."

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
    """
    results = []
    
    try:
        with open(input_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    classification = classify_complaint(row)
                    results.append(classification)
                except Exception as e:
                    # Error handling specified in skills.md
                    results.append({
                        "complaint_id": row.get("complaint_id", "UNKNOWN"),
                        "category": "Other",
                        "priority": "Standard",
                        "reason": f"Error processing row: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })
    except Exception as e:
        print(f"Failed to read input file: {e}")
        return

    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
    except Exception as e:
        print(f"Failed to write output file: {e}")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_*.csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
