"""
UC-0A — Complaint Classifier
Fixed file for Nasscom Prompt to Production.
"""
import argparse
import csv
from typing import Dict, List, Optional

# Constants
ALLOWED_CATEGORIES: List[str] = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

SEVERITY_KEYWORDS: List[str] = [
    "injury", "child", "school", "hospital", "ambulance", 
    "fire", "hazard", "fell", "collapse"
]

CATEGORY_KEYWORDS = [
    ("Pothole", ["pothole", "potholes"]),
    ("Flooding", ["flood", "flooded", "waterlogged", "water logged", "water-logged"]),
    ("Drain Blockage", ["drain", "blocked drain", "blocked drains", "drainage", "sewer", "gutter"]),
    ("Streetlight", ["streetlight", "street lights", "lighting", "lights out", "dark"]),
    ("Waste", ["garbage", "trash", "dumped", "waste", "overflowing bins", "bins"]),
    ("Noise", ["noise", "loud music", "music past", "speaker", "sound"]),
    ("Heritage Damage", ["heritage", "heritage street", "heritage site", "historical", "monument"]),
    ("Road Damage", ["road surface", "cracked", "sinking", "broken road", "manhole", "footpath"]),
    ("Heat Hazard", ["heat", "heat hazard", "hot", "sunny", "temperature"]),
]

CATEGORY_PRIORITY_ORDER: List[str] = [
    "Pothole", "Drain Blockage", "Flooding", "Streetlight", 
    "Noise", "Waste", "Heritage Damage", "Road Damage", "Heat Hazard"
]

# Helper Functions
def _normalize(text: str) -> str:
    return text.strip().lower() if text else ""

def _find_matching_categories(description: str) -> List[str]:
    matches: List[str] = []
    normalized = _normalize(description)
    for category, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword in normalized:
                matches.append(category)
                break
    return matches

def _choose_category(matches: List[str], description: str) -> str:
    if not matches:
        return "Other"
    for category in CATEGORY_PRIORITY_ORDER:
        if category in matches:
            return category
    return matches[0]

def _contains_severity(description: str) -> bool:
    normalized = _normalize(description)
    return any(kw in normalized for kw in SEVERITY_KEYWORDS)

def _determine_priority(category: str, description: str) -> str:
    if _contains_severity(description):
        return "Urgent"
    return "Low" if category == "Noise" else "Standard"

def _build_reason(category: str, priority: str, description: str) -> str:
    normalized = _normalize(description)
    reason_parts = []
    if category != "Other":
        reason_parts.append(f"Category set to {category} based on description")
    else:
        reason_parts.append("Category set to Other because description is not clear")

    if priority == "Urgent":
        for kw in SEVERITY_KEYWORDS:
            if kw in normalized:
                reason_parts.append(f"priority set to Urgent because it mentions '{kw}'")
                break
    else:
        reason_parts.append(f"priority set to {priority} because no urgent keywords were found")

    return ". ".join(reason_parts) + "."

# Main Logic
def classify_complaint(row: Dict[str, str]) -> Dict[str, str]:
    description = row.get("description", "") or ""
    if not description.strip():
        return {
            "category": "Other",
            "priority": "Standard",
            "reason": "Missing description text.",
            "flag": "NEEDS_REVIEW",
        }

    matches = _find_matching_categories(description)
    category = _choose_category(matches, description)
    priority = _determine_priority(category, description)
    reason = _build_reason(category, priority, description)
    
    flag = "NEEDS_REVIEW" if category == "Other" else ""

    return {
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }

def batch_classify(input_path: str, output_path: str):
    output_fields = ["category", "priority", "reason", "flag"]
    try:
        with open(input_path, newline="", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            with open(output_path, "w", newline="", encoding="utf-8") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=output_fields)
                writer.writeheader()

                for row in reader:
                    try:
                        result = classify_complaint(row)
                    except Exception:
                        result = {
                            "category": "Other",
                            "priority": "Standard",
                            "reason": "Classification failed.",
                            "flag": "NEEDS_REVIEW",
                        }
                    writer.writerow(result)
    except FileNotFoundError:
        print(f"Error: The file {input_path} was not found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
