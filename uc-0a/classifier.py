"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import os
import sys


ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard",
    "Drain Blockage", "Other"
]

ALLOWED_PRIORITIES = ["Urgent", "Standard", "Low"]

SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital",
    "ambulance", "fire", "hazard", "fell", "collapse"
]

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole"],
    "Flooding": ["flood", "waterlogging"],
    "Streetlight": ["streetlight", "light not working", "dark"],
    "Waste": ["garbage", "waste", "trash", "dump"],
    "Noise": ["noise", "loud"],
    "Road Damage": ["road damage", "crack", "broken road"],
    "Heritage Damage": ["heritage", "monument"],
    "Heat Hazard": ["heat"],
    "Drain Blockage": ["drain", "sewer", "blockage"],
}


def contains_severity(text):
    text_lower = text.lower()
    return any(word in text_lower for word in SEVERITY_KEYWORDS)


def detect_category(description):
    matched = []
    desc_lower = description.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                matched.append(category)
                break

    if len(matched) == 1:
        return matched[0], False
    elif len(matched) > 1:
        return matched[0], True
    else:
        return "Other", True


def generate_reason(description, category):
    words = description.strip().split()
    excerpt = " ".join(words[:6]) if words else "no valid description"
    return f'Based on words "{excerpt}", classified as {category}.'


def enforce_one_sentence(text):
    if "." in text:
        return text.split(".")[0].strip() + "."
    return text.strip() + "."

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    
    TODO: Build this using your AI tool guided by your agents.md and skills.md.
    Your RICE enforcement rules must be reflected in this function's behaviour.
    """
    
    description = row.get("description")

    if not description or not description.strip():
        return {
            "category": "Other",
            "priority": "Low",
            "reason": "No valid description provided.",
            "flag": "NEEDS_REVIEW"
        }

    category, ambiguous = detect_category(description)

    if category not in ALLOWED_CATEGORIES:
        category = "Other"
        ambiguous = True

    if contains_severity(description):
        priority = "Urgent"
    else:
        priority = "Standard"

    if priority not in ALLOWED_PRIORITIES:
        priority = "Low"

    reason = generate_reason(description, category)
    reason = enforce_one_sentence(reason)

    if not reason.strip():
        reason = "Insufficient description to justify classification."
        ambiguous = True

    flag = "NEEDS_REVIEW" if ambiguous else ""

    return {
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    
    TODO: Build this using your AI tool.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)

    results = []

    try:
        with open(input_path, newline='', encoding="utf-8") as infile:
            reader = csv.DictReader(infile)

            if "description" not in reader.fieldnames:
                print("Error: Missing 'description' column in input CSV")
                sys.exit(1)

            for row in reader:
                try:
                    result = classify_complaint(row)
                except Exception:
                    result = {
                        "category": "Other",
                        "priority": "Low",
                        "reason": "Error processing row based on given input.",
                        "flag": "NEEDS_REVIEW"
                    }

                if result["category"] not in ALLOWED_CATEGORIES:
                    result["category"] = "Other"
                    result["flag"] = "NEEDS_REVIEW"

                if result["priority"] not in ALLOWED_PRIORITIES:
                    result["priority"] = "Low"
                    result["flag"] = "NEEDS_REVIEW"

                if not result.get("reason"):
                    result["reason"] = "No justification provided from description."
                    result["flag"] = "NEEDS_REVIEW"

                result["reason"] = enforce_one_sentence(result["reason"])

                results.append(result)

    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        with open(output_path, "w", newline='', encoding="utf-8") as outfile:
            fieldnames = ["category", "priority", "reason", "flag"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in results:
                writer.writerow(row)

    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")