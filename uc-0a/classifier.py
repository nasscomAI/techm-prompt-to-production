"""
UC-0A — Complaint Classifier
Implementation based on agents.md and skills.md.
"""
import argparse
import csv
import os

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on the rules in agents.md.
    """
    description = row.get("description", "").lower()
    complaint_id = row.get("complaint_id", "UNKNOWN")
    
    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "Missing description.",
            "flag": "NEEDS_REVIEW"
        }

    # 1. Priority Enforcement
    # Priority must be 'Urgent' if description contains specific severity keywords.
    severity_keywords = ['injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse']
    priority = "Standard"
    found_severity = []
    
    for kw in severity_keywords:
        if kw in description:
            priority = "Urgent"
            found_severity.append(kw)
            
    # 2. Category Enforcement
    # Defined Categories: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other
    category_mappings = {
        "Pothole": ["pothole"],
        "Flooding": ["flooded", "flooding", "water", "rain", "straded"],
        "Streetlight": ["streetlight", "light", "dark", "flickering", "sparking"],
        "Waste": ["garbage", "waste", "bins", "dumped", "refuse"],
        "Noise": ["noise", "music", "loud"],
        "Road Damage": ["road surface", "cracked", "sinking", "pavement", "footpath", "tiles"],
        "Heritage Damage": ["heritage"],
        "Heat Hazard": ["heat", "hot", "temperature"],
        "Drain Blockage": ["drain", "sewer", "blocked"]
    }
    
    matched_categories = []
    reason_words = []

    for cat, keywords in category_mappings.items():
        for kw in keywords:
            if kw in description:
                if cat not in matched_categories:
                    matched_categories.append(cat)
                reason_words.append(kw)
                break # Move to next category if one keyword matches

    # 3. Ambiguity & Assignment
    category = "Other"
    flag = ""
    
    if len(matched_categories) == 1:
        category = matched_categories[0]
    elif len(matched_categories) > 1:
        # Multiple matches = Ambiguous
        category = "Other"
        flag = "NEEDS_REVIEW"
    else:
        # No matches = Other
        category = "Other"
        flag = "NEEDS_REVIEW"

    # 4. Reason Construction
    # Must cite specific words from description
    if matched_categories:
        cat_evidence = f"Cited: {', '.join(reason_words)}."
    else:
        cat_evidence = "No specific category keywords found."
        
    if found_severity:
        sev_evidence = f" Urgent due to: {', '.join(found_severity)}."
    else:
        sev_evidence = ""

    reason = f"{cat_evidence}{sev_evidence}".strip()

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, apply classify_complaint per row, write output CSV.
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
            
            # Ensure we have the target columns in the output
            new_fields = ["category", "priority", "reason", "flag"]
            output_fieldnames = fieldnames + [f for f in new_fields if f not in fieldnames]

            for row in reader:
                try:
                    classification = classify_complaint(row)
                    # Merge classification results into the row
                    row.update(classification)
                    results.append(row)
                except Exception as e:
                    print(f"Skipping malformed row {row.get('complaint_id')}: {e}")

        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(results)

    except Exception as e:
        print(f"Critical error during batch processing: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to input test CSV")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
