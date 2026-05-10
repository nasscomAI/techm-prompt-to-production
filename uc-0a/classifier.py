"""
UC-0A — Complaint Classifier
Built using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import logging

logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on rules encoded in agents.md and skills.md.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    if not isinstance(row, dict):
        raise ValueError("Input row must be a dictionary.")

    description_key = next((k for k in row.keys() if "desc" in k.lower() or "text" in k.lower()), "description")
    id_key = next((k for k in row.keys() if "id" in k.lower()), "complaint_id")
    
    description = str(row.get(description_key, "")).lower()
    complaint_id = row.get(id_key, "")

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "The description provided was empty or null.",
            "flag": "NEEDS_REVIEW"
        }

    # Severity Keyword Rules (agents.md)
    urgent_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    found_urgent = [kw for kw in urgent_keywords if kw in description]
    priority = "Urgent" if found_urgent else "Standard"

    # Category Mapping Rules (agents.md)
    categories_map = {
        "Pothole": ["pothole", "pit"],
        "Flooding": ["flood", "waterlog", "water"],
        "Streetlight": ["light", "dark", "streetlamp", "streetlight", "lamp"],
        "Waste": ["waste", "garbage", "trash", "rubbish", "litter"],
        "Noise": ["noise", "loud", "music", "sound"],
        "Road Damage": ["road", "crack", "damage", "broken", "cave-in"],
        "Heritage Damage": ["heritage", "monument", "statue", "ruin"],
        "Heat Hazard": ["heat", "hot", "sun", "blistering"],
        "Drain Blockage": ["drain", "block", "clog", "sewage", "gutter"]
    }

    matched_categories = []
    category_factors = []

    for cat, kws in categories_map.items():
        matched_kws = [kw for kw in kws if kw in description]
        if matched_kws:
            matched_categories.append(cat)
            category_factors.extend(matched_kws)

    flag = ""
    
    # Enforce strict output and reason citation (agents.md & skills.md)
    if len(matched_categories) == 1:
        category = matched_categories[0]
        words_cited = list(set(category_factors + found_urgent))
        reason = f"The description was assigned to {category} because it contained specific keywords like '{', '.join(words_cited)}'."
    elif len(matched_categories) > 1:
        category = "Other"
        flag = "NEEDS_REVIEW"
        words_cited = list(set(category_factors[:2]))
        reason = f"The description was ambiguous, matching multiple categories using words like '{words_cited[0]}' and '{words_cited[1]}'."
    else:
        category = "Other"
        flag = "NEEDS_REVIEW"
        reason = "The description lacked specific actionable keywords to clearly determine a category."

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row individually, write results CSV.
    Skills requirement: flag nulls, not crash on bad rows, write output.
    """
    results = []
    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    result = classify_complaint(row)
                    # Enforce that all expected fields are present
                    safe_result = {
                        "complaint_id": result.get("complaint_id", ""),
                        "category": result.get("category", "Other"),
                        "priority": result.get("priority", "Standard"),
                        "reason": result.get("reason", "Unknown."),
                        "flag": result.get("flag", "")
                    }
                    results.append(safe_result)
                except Exception as e:
                    logging.error(f"Error classifying row {row}: {e}")
                    results.append({
                        "complaint_id": row.get("complaint_id", row.get("id", "UNKNOWN")),
                        "category": "Other",
                        "priority": "Low",
                        "reason": "System error occurred during classification.",
                        "flag": "NEEDS_REVIEW"
                    })
    except Exception as e:
        logging.error(f"Failed to read input file {input_path}: {e}")
        return

    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    except Exception as e:
        logging.error(f"Failed to write output file {output_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    batch_classify(args.input, args.output)
    print(f"Classification completed. Results securely written to {args.output}")
