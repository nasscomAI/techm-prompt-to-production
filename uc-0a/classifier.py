"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on RICE enforcement rules.
    """
    description = row.get("description", "").lower()
    
    # 1. Determine Priority
    urgent_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    for word in urgent_keywords:
        if word in description:
            priority = "Urgent"
            break
            
    # 2. Determine Category
    categories = {
        "Pothole": ["pothole"],
        "Flooding": ["flood", "water", "inundation"],
        "Streetlight": ["streetlight", "light", "dark", "lamp"],
        "Waste": ["garbage", "waste", "trash", "bin", "smell", "dumped", "animal"],
        "Noise": ["noise", "music", "speaker", "loud"],
        "Road Damage": ["road surface", "crack", "sinking", "pavement", "footpath", "tiles", "manhole"],
        "Heritage Damage": ["heritage"],
        "Heat Hazard": ["heat", "hot", "sun"],
        "Drain Blockage": ["drain", "sewage", "gutter", "blockage"]
    }
    
    found_categories = []
    reason_words = []
    
    for cat, keywords in categories.items():
        for word in keywords:
            if word in description:
                found_categories.append(cat)
                reason_words.append(word)
                break # Move to next category
                
    # Enforcement Rules
    category = "Other"
    flag = ""
    
    if len(found_categories) == 1:
        category = found_categories[0]
    elif len(found_categories) > 1:
        # Ambiguous if multiple categories match
        category = found_categories[0] # Pick first but flag
        flag = "NEEDS_REVIEW"
    else:
        # No category found
        category = "Other"
        flag = "NEEDS_REVIEW"
        
    # 3. Generate Reason
    if reason_words:
        reason = f"Classified as {category} because description mentions '{reason_words[0]}'."
    else:
        reason = "Classified as Other due to lack of specific category keywords."
        
    if priority == "Urgent":
        # Find which urgent word triggered it
        urgent_word = next((w for w in urgent_keywords if w in description), "critical keywords")
        reason += f" Priority set to Urgent due to '{urgent_word}'."

    return {
        "complaint_id": row.get("complaint_id"),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ["category", "priority", "reason", "flag"]
            
            results = []
            for row in reader:
                classification = classify_complaint(row)
                row.update(classification)
                results.append(row)
                
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
    except Exception as e:
        print(f"Error processing {input_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
