"""
UC-0A — Complaint Classifier
"""
import argparse
import csv

CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

URGENT_KEYWORDS = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]

def classify_complaint(row: dict) -> dict:
    description = row.get("description", "").lower()
    
    # Check for urgency
    priority = "Standard"
    urgent_words_found = []
    for word in URGENT_KEYWORDS:
        if word in description:
            urgent_words_found.append(word)
    
    if urgent_words_found:
        priority = "Urgent"

    # Match categories based on keywords
    matched_categories = []
    reason_words = []
    
    if "pothole" in description:
        matched_categories.append("Pothole")
        reason_words.append("pothole")
    
    if "flood" in description or "rainwater" in description or "waterlogged" in description:
        matched_categories.append("Flooding")
        reason_words.append("water/flood")
        
    if "lamp post" in description or "streetlight" in description or "substation" in description or "darkness" in description:
        matched_categories.append("Streetlight")
        reason_words.append("light/power")
        
    if "waste" in description or "garbage" in description or "trash" in description:
        matched_categories.append("Waste")
        reason_words.append("waste")
        
    if "band playing" in description or "amplifiers" in description or "noise" in description:
        matched_categories.append("Noise")
        reason_words.append("noise/sound")
        
    if "road surface buckled" in description or "road subsided" in description or "footpath broken" in description or "cobblestones broken" in description or "paving removed" in description:
        matched_categories.append("Road Damage")
        reason_words.append("road damage")
        
    if "heritage" in description or "historic" in description:
        matched_categories.append("Heritage Damage")
        reason_words.append("heritage/historic")
        
    import re
    if re.search(r'\b(heat|hot)\b', description):
        matched_categories.append("Heat Hazard")
        reason_words.append("heat")
        
    if "drain" in description:
        matched_categories.append("Drain Blockage")
        reason_words.append("drain")
        
    # Determine category, flag and reason
    flag = ""
    category = "Other"
    reason = "Could not determine category from description."
    
    if len(matched_categories) == 1:
        category = matched_categories[0]
        reason = f"Classified as {category} because description mentions '{reason_words[0]}'."
    elif len(matched_categories) > 1:
        category = matched_categories[0] # Pick the first one, but flag it
        flag = "NEEDS_REVIEW"
        reason = f"Ambiguous complaint mentioning multiple issues: {', '.join(reason_words)}."
    
    if priority == "Urgent":
        reason += f" Priority is Urgent due to '{urgent_words_found[0]}'."

    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            # The expected output should just contain the fields we care about, or maybe all input + classified fields?
            # Let's just output complaint_id, category, priority, reason, flag
            output_fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
            
            with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
                writer.writeheader()
                
                for row in reader:
                    try:
                        result = classify_complaint(row)
                        writer.writerow(result)
                    except Exception as e:
                        print(f"Error processing row {row.get('complaint_id', 'UNKNOWN')}: {e}")
                        writer.writerow({
                            "complaint_id": row.get("complaint_id", ""),
                            "category": "Other",
                            "priority": "Low",
                            "reason": f"Parsing error: {e}",
                            "flag": "NEEDS_REVIEW"
                        })
    except Exception as e:
        print(f"Failed to process file {input_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
