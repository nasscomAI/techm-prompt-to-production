"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import pandas as pd
import os
import sys

# Allowed schema values
ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard",
    "Drain Blockage", "Other"
]

ALLOWED_PRIORITY = ["Urgent", "Standard", "Low"]

SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse"
]


def extract_description(row):
    """Extract description field safely"""
    for col in row.index:
        if col.lower() in ["description", "complaint", "text"]:
            return str(row[col])
    return ""


def contains_severity(text):
    text_lower = text.lower()
    return any(word in text_lower for word in SEVERITY_KEYWORDS)


def classify_complaint(row):
    """
    Classifies a single complaint into category, priority, reason, flag
    """
    description = extract_description(row)

    # Handle missing description
    if not description or description.strip() == "":
        return {
            "category": "Other",
            "priority": "Low",
            "reason": "No valid description provided",
            "flag": "NEEDS_REVIEW"
        }

    text = description.lower()

    # Simple keyword-based classification (strict, no hallucination)
    category_matches = []

    if "pothole" in text:
        category_matches.append("Pothole")
    if "flood" in text or "waterlogging" in text:
        category_matches.append("Flooding")
    if "light" in text:
        category_matches.append("Streetlight")
    if "garbage" in text or "waste" in text:
        category_matches.append("Waste")
    if "noise" in text or "loud" in text:
        category_matches.append("Noise")
    if "road" in text and "damage" in text:
        category_matches.append("Road Damage")
    if "heritage" in text:
        category_matches.append("Heritage Damage")
    if "heat" in text:
        category_matches.append("Heat Hazard")
    if "drain" in text or "sewage" in text:
        category_matches.append("Drain Blockage")

    # Resolve category
    if len(category_matches) == 1:
        category = category_matches[0]
        flag = ""
    elif len(category_matches) > 1:
        category = category_matches[0]
        flag = "NEEDS_REVIEW"
    else:
        category = "Other"
        flag = ""

    # Priority assignment
    if contains_severity(text):
        priority = "Urgent"
    else:
        priority = "Standard"

    # Ensure valid priority
    if priority not in ALLOWED_PRIORITY:
        priority = "Low"

    # Reason must cite exact words
    cited_word = None
    for word in description.split():
        if word.lower() in text:
            cited_word = word
            break

    if cited_word:
        reason = f"The complaint mentions '{cited_word}'."
    else:
        reason = "The complaint text provides insufficient clear keywords."
        flag = "NEEDS_REVIEW"

    # Ensure one sentence
    reason = reason.strip().replace("\n", " ")

    # Final enforcement checks
    if category not in ALLOWED_CATEGORIES:
        category = "Other"
        flag = "NEEDS_REVIEW"

    if contains_severity(text) and priority != "Urgent":
        priority = "Urgent"

    return {
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path, output_path):
    """Processes CSV and writes classified output"""

    # Input validation
    if not os.path.exists(input_path):
        print("Error: Input file not found or invalid")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
    except Exception:
        print("Error: Unable to read input CSV")
        sys.exit(1)

    results = []

    for _, row in df.iterrows():
        try:
            result = classify_complaint(row)
        except Exception:
            result = {
                "category": "Other",
                "priority": "Low",
                "reason": "Processing error occurred",
                "flag": "NEEDS_REVIEW"
            }

        # Ensure all fields exist
        for field in ["category", "priority", "reason", "flag"]:
            if field not in result:
                result[field] = "NEEDS_REVIEW" if field == "flag" else ""

        # Enforce schema
        if result["category"] not in ALLOWED_CATEGORIES:
            result["category"] = "Other"
            result["flag"] = "NEEDS_REVIEW"

        if contains_severity(extract_description(row)):
            result["priority"] = "Urgent"

        results.append(result)

    output_df = pd.DataFrame(results, columns=["category", "priority", "reason", "flag"])

    # Write output
    try:
        output_df.to_csv(output_path, index=False)
    except Exception:
        print("Error: Unable to write output file")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")

    args = parser.parse_args()

    batch_classify(args.input, args.output)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
