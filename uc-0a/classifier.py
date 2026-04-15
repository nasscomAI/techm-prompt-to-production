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
    complaint_id = row.get("complaint_id", "N/A")
    
    # Categories and keywords mapping
    # Note: In a real scenario, this would be an LLM call. 
    # Here we implement it using rule-based logic for the workshop simulation.
    category_map = {
        "pothole": "Pothole",
        "flood": "Flooding",
        "water": "Flooding",
        "light": "Streetlight",
        "garbage": "Waste",
        "trash": "Waste",
        "noise": "Noise",
        "loud": "Noise",
        "road": "Road Damage",
        "heritage": "Heritage Damage",
        "monument": "Heritage Damage",
        "heat": "Heat Hazard",
        "sun": "Heat Hazard",
        "drain": "Drain Blockage",
        "sewage": "Drain Blockage"
    }
    
    category = "Other"
    for kw, cat in category_map.items():
        if kw in description:
            category = cat
            break
            
    # Priority keywords
    urgent_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    for kw in urgent_keywords:
        if kw in description:
            priority = "Urgent"
            break
    
    # Reason
    if category != "Other":
        reason = f"Classified as {category} because of keywords related to '{category.lower()}'. "
    else:
        reason = "Could not identify a specific category from the description."
        
    # Flag
    flag = ""
    if category == "Other" or not description:
        flag = "NEEDS_REVIEW"
        
    return {
        "complaint_id": complaint_id,
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
        with open(input_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(classify_complaint(row))
    except Exception as e:
        print(f"Error reading input: {e}")
        return

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    try:
        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    except Exception as e:
        print(f"Error writing output: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
