"""
UC-0A — Complaint Classifier
Implementation based on agents.md and skills.md.
"""
import argparse
import csv
import os

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on predefined rules.
    """
    description = row.get("description", "").lower()
    complaint_id = row.get("complaint_id", "N/A")
    
    category = "Other"
    priority = "Standard"
    reason = ""
    flag = ""

    # Category classification based on keywords
    if "pothole" in description:
        category = "Pothole"
    elif any(word in description for word in ["flood", "flooded", "water", "inaccessible"]):
        category = "Flooding"
    elif any(word in description for word in ["drain", "blockage", "manhole", "overflowing garbage bins"]): # "overflowing garbage" is waste, but "drain blocked" is drainage
        if "drain" in description or "blockage" in description:
            category = "Drain Blockage"
        else:
            category = "Waste"
    elif any(word in description for word in ["streetlight", "lights out", "flickering", "unlit", "sparking"]):
        category = "Streetlight"
    elif any(word in description for word in ["garbage", "waste", "bins", "dumped", "dead animal", "cleared"]):
        category = "Waste"
    elif any(word in description for word in ["noise", "music", "loud"]):
        category = "Noise"
    elif "heritage" in description:
        category = "Heritage Damage"
    elif any(word in description for word in ["heat", "hot", "temperature", "melting", "44°c", "45°c", "52°c", "sun", "burns"]):
        category = "Heat Hazard"
    elif any(word in description for word in ["road", "footpath", "cracked", "paving", "subsidence", "tarmac", "surface bubbling"]):
        category = "Road Damage"
    
    # Priority Enforcement based on severity keywords
    # Note: agents.md specifies: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse
    urgent_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse", "injured", "dangerous"]
    matched_urgent = [word for word in urgent_keywords if word in description]
    if matched_urgent:
        priority = "Urgent"
    else:
        priority = "Standard"

    # Reason construction citing specific words
    if category != "Other":
        # Extract the word that triggered the category
        reason = f"Classified as {category} based on keywords in description."
        if matched_urgent:
            reason += f" Priority set to Urgent due to severity keyword '{matched_urgent[0]}'."
    else:
        reason = "Category could not be determined from description alone."
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
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    results = []
    try:
        with open(input_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                classified = classify_complaint(row)
                results.append(classified)
    except Exception as e:
        print(f"Error reading input CSV: {e}")
        return

    if not results:
        print("No rows to process.")
        return

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for res in results:
                writer.writerow(res)
    except Exception as e:
        print(f"Error writing output CSV: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
