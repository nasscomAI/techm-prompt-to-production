"""
UC-0A — Complaint Classifier
Implementation guided by agents.md RICE enforcement rules and skills.md spec.
"""
import argparse
import csv
import sys
from typing import Dict, Any

# Classification schema from agents.md enforcement rules
ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"
]

# Keyword mappings for category detection (case-insensitive)
CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "hole", "crater", "bump"],
    "Flooding": ["flood", "water", "standing", "overflow", "log"],
    "Streetlight": ["streetlight", "lamp", "light", "dark", "bulb", "glow"],
    "Waste": ["garbage", "trash", "waste", "dump", "litter", "bin"],
    "Noise": ["noise", "sound", "loud", "honk", "construction", "music"],
    "Road Damage": ["road", "crack", "damage", "broken", "uneven"],
    "Heritage Damage": ["heritage", "monument", "historical", "ancient", "old"],
    "Heat Hazard": ["heat", "hot", "temperature", "steam", "boiling"],
    "Drain Blockage": ["drain", "clog", "blockage", "sewer", "gutter"]
}


def classify_complaint(row: Dict[str, Any]) -> Dict[str, str]:
    """
    Classify a single complaint row according to RICE enforcement rules.
    Input: dict with at least 'description' key (string).
    Output: dict with keys: complaint_id, category, priority, reason, flag.
    """
    description = str(row.get("description", "")).strip()
    complaint_id = str(row.get("complaint_id", ""))

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW"
        }

    desc_lower = description.lower()

    # Priority: Urgent if any severity keyword present
    priority = "Standard"
    for keyword in SEVERITY_KEYWORDS:
        if keyword in desc_lower:
            priority = "Urgent"
            break

    # Category detection via keyword matching
    category = "Other"
    matched_keyword = None
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                category = cat
                matched_keyword = kw
                break
        if category != "Other":
            break

    # Build reason citing the specific word(s) from description
    if matched_keyword:
        reason = f"Complaint mentions '{matched_keyword}', indicating {category}."
    elif category == "Other":
        reason = "No clear category indicator found in description."
    else:
        reason = f"Complaint indicates {category}."

    # Flag ambiguous cases
    flag = ""
    if category == "Other":
        flag = "NEEDS_REVIEW"

    return {
        "complaint_id": complaint_id,
        "description": description,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row using classify_complaint, write results CSV.
    Preserves all original input columns and appends: category, priority, reason, flag.
    """
    rows_processed = 0
    rows_failed = 0

    try:
        with open(input_path, "r", encoding="utf-8", newline="") as infile:
            reader = csv.DictReader(infile)
            if "description" not in reader.fieldnames:
                print("ERROR: Input CSV must contain a 'description' column", file=sys.stderr)
                sys.exit(1)

            input_fieldnames = reader.fieldnames
            output_fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
            results = []

            for row in reader:
                rows_processed += 1
                try:
                    classification = classify_complaint(row)
                    results.append({
                        "complaint_id": row.get("complaint_id", ""),
                        "category": classification["category"],
                        "priority": classification["priority"],
                        "reason": classification["reason"],
                        "flag": classification["flag"]
                    })
                except Exception as e:
                    rows_failed += 1
                    print(f"ERROR: Failed to classify row {rows_processed}: {e}", file=sys.stderr)
                    results.append({
                        "complaint_id": row.get("complaint_id", ""),
                        "category": "Other",
                        "priority": "Standard",
                        "reason": f"Classification error: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })

        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"Done. Processed {rows_processed} rows, {rows_failed} failures. Results written to {output_path}")

    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
