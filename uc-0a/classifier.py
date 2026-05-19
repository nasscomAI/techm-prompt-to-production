import argparse
import csv
import sys
from typing import List


# Classification schema constants
CATEGORIES = [
    "Pothole",
    "Flooding",
    "Streetlight",
    "Waste",
    "Noise",
    "Road Damage",
    "Heritage Damage",
    "Heat Hazard",
    "Drain Blockage",
    "Other",
]

SEVERITY_KEYWORDS = [
    "injury",
    "child",
    "school",
    "hospital",
    "ambulance",
    "fire",
    "hazard",
    "fell",
    "collapse",
]


def _match_category(description: str) -> List[str]:
    """
    Return a list of matching categories based on keyword presence.
    Simple heuristic: look for lowercase keywords within the description.
    """
    desc = description.lower()
    matches = []

    keyword_map = {
        "pothole": "Pothole",
        "flood": "Flooding",
        "flooding": "Flooding",
        "streetlight": "Streetlight",
        "waste": "Waste",
        "noise": "Noise",
        "road damage": "Road Damage",
        "roaddamage": "Road Damage",
        "heritage damage": "Heritage Damage",
        "heritage": "Heritage Damage",
        "heat hazard": "Heat Hazard",
        "heat": "Heat Hazard",
        "drain blockage": "Drain Blockage",
        "drain": "Drain Blockage",
    }

    for kw, cat in keyword_map.items():
        if kw in desc:
            matches.append(cat)

    return matches


def _determine_priority(description: str) -> str:
    """Return 'Urgent' if any severity keyword is present, else 'Standard'."""
    desc = description.lower()

    for kw in SEVERITY_KEYWORDS:
        if kw in desc:
            return "Urgent"

    return "Standard"


def _compose_reason(description: str, category: str) -> str:
    """
    Create a one-sentence reason citing keywords from the description.
    If a keyword that triggered the category is found, mention it.
    Otherwise provide a generic statement.
    """
    desc = description.lower()

    # Find a keyword that maps to the chosen category
    cat_to_kw = {
        "Pothole": "pothole",
        "Flooding": "flood",
        "Streetlight": "streetlight",
        "Waste": "waste",
        "Noise": "noise",
        "Road Damage": "road damage",
        "Heritage Damage": "heritage",
        "Heat Hazard": "heat hazard",
        "Drain Blockage": "drain blockage",
    }

    kw = cat_to_kw.get(category)

    if kw and kw in desc:
        return f"The description mentions '{kw}' indicating a {category.lower()} issue."

    # fallback – include first few words of description
    snippet = description.strip().split(" ")[:6]
    snippet_text = " ".join(snippet)

    return (
        f"Based on the description ('{snippet_text}...'), "
        f"the issue is classified as {category.lower()}."
    )


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.

    Expected input keys: 'description' (required), optionally 'complaint_id'.

    Returns a dict with keys:
    complaint_id, category, priority, reason, flag.
    """
    description = row.get("description", "").strip()
    complaint_id = row.get("complaint_id") or row.get("id") or ""

    if not description:
        # Empty description – treat as ambiguous
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW",
        }

    matched = _match_category(description)

    if len(matched) == 1:
        category = matched[0]
        flag = ""
    else:
        # No clear match or multiple matches -> ambiguous
        category = "Other"
        flag = "NEEDS_REVIEW"

    priority = _determine_priority(description)
    reason = _compose_reason(description, category)

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, and write results to output CSV.

    The output includes original columns plus the classification fields.
    Errors are logged to stderr but processing continues.
    """
    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        # Add classification columns if not already present
        extra_fields = ["category", "priority", "reason", "flag"]
        out_fields = fieldnames + [
            f for f in extra_fields if f not in fieldnames
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=out_fields)
            writer.writeheader()

            for idx, row in enumerate(reader, start=1):
                try:
                    result = classify_complaint(row)
                except Exception as e:
                    print(
                        f"Error classifying row {idx}: {e}",
                        file=sys.stderr,
                    )

                    # Fallback to ambiguous result
                    result = {
                        "category": "Other",
                        "priority": "Standard",
                        "reason": "Classification failed.",
                        "flag": "NEEDS_REVIEW",
                    }

                # Merge result into row
                output_row = {**row, **result}
                writer.writerow(output_row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="UC-0A Complaint Classifier"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV file",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to write results CSV",
    )

    args = parser.parse_args()

    batch_classify(args.input, args.output)

    print(f"Done. Results written to {args.output}")
