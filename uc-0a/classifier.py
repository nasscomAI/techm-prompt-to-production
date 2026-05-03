"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row using rule-based logic following RICE/agents.md.
    """
    desc = row.get("description", "").lower()
    
    # 1. Severity Keywords for Priority
    severity_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    for kw in severity_keywords:
        if kw in desc:
            priority = "Urgent"
            break
    
    # 2. Category Keywords
    category_map = {
        "Pothole": ["pothole"],
        "Flooding": ["flooded", "flood", "water", "rain"],
        "Streetlight": ["streetlight", "lights out", "flickering"],
        "Waste": ["garbage", "waste", "trash", "dump", "animal"],
        "Noise": ["noise", "music", "loud"],
        "Road Damage": ["road surface", "cracked", "sinking"],
        "Heritage Damage": ["heritage"],
        "Heat Hazard": ["heat", "hot"],
        "Drain Blockage": ["drain", "blocked"]
    }
    
    category = "Other"
    found_keyword = None
    for cat, kws in category_map.items():
        for kw in kws:
            if kw in desc:
                category = cat
                found_keyword = kw
                break
        if found_keyword:
            break
            
    # 3. Reason (One sentence, citing words)
    if found_keyword:
        reason = f"Classified as {category} because the description mentions '{found_keyword}'."
    else:
        reason = "Classified as Other because no specific category keywords were identified in the description."
        
    # 4. Flag (NEEDS_REVIEW if ambiguous)
    flag = "NEEDS_REVIEW" if category == "Other" else ""
    
    return {
        "complaint_id": row.get("complaint_id"),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, apply classify_complaint, and write results to output CSV.
    """
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ["category", "priority", "reason", "flag"]
            
            results = []
            for row in reader:
                try:
                    # Basic validation for nulls/empty rows
                    if not any(row.values()):
                        continue
                        
                    classified = classify_complaint(row)
                    # Merge classification results into the row
                    row.update(classified)
                    results.append(row)
                except Exception as e:
                    print(f"Error processing row {row.get('complaint_id')}: {e}")
                    continue

        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
    except FileNotFoundError:
        print(f"Error: Input file {input_path} not found.")
    except Exception as e:
        print(f"An unexpected error occurred during batch processing: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
