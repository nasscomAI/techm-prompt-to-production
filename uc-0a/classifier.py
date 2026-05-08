"""
UC-0A — Complaint Classifier
Implements classify_complaint and batch_classify per agents.md and skills.md.
"""
import argparse
import csv
import os

ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

URGENT_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse"
]

# Keyword → category mapping (order matters: more specific first)
CATEGORY_KEYWORDS = [
    ("Heat Hazard",     ["heat", "temperature", "melting", "burns", "52°c", "45°c", "44°c", "sun exposure"]),
    ("Heritage Damage", ["heritage", "historic", "tram road", "cobblestone", "lamp post", "tagore", "marble palace", "step well", "ancient"]),
    ("Drain Blockage",  ["drain blocked", "drain blockage", "stormwater drain", "mosquito breeding"]),
    ("Flooding",        ["flood", "flooded", "flooding", "waterlogged", "standing water", "knee-deep", "submerged"]),
    ("Pothole",         ["pothole", "potholes"]),
    ("Streetlight",     ["streetlight", "street light", "lights out", "sparking", "flickering", "unlit", "darkness", "substation"]),
    ("Waste",           ["garbage", "waste", "overflowing bin", "bins overflowing", "dead animal", "dumped", "waste not cleared"]),
    ("Noise",           ["music", "noise", "drilling", "amplifier", "idling", "band playing", "audible"]),
    ("Road Damage",     ["road collapsed", "road subsided", "road subsidence", "cracked", "sinking", "buckled", "broken", "upturned", "manhole", "footpath", "crater", "surface"]),
]


def detect_category(description: str) -> tuple[str, str]:
    """Returns (category, flag)."""
    desc = description.lower()
    matches = []

    for category, keywords in CATEGORY_KEYWORDS:
        if any(kw in desc for kw in keywords):
            matches.append(category)

    if len(matches) == 1:
        return matches[0], ""
    elif len(matches) > 1:
        # Return the first (highest priority) match but flag as ambiguous
        return matches[0], "NEEDS_REVIEW"
    else:
        return "Other", "NEEDS_REVIEW"


def detect_priority(description: str, category: str) -> str:
    desc = description.lower()
    if any(kw in desc for kw in URGENT_KEYWORDS):
        return "Urgent"
    if category == "Noise":
        return "Low"
    return "Standard"


def build_reason(description: str, category: str, priority: str) -> str:
    desc_lower = description.lower()
    # Find the triggering keyword for the reason sentence
    if priority == "Urgent":
        for kw in URGENT_KEYWORDS:
            if kw in desc_lower:
                return f'Classified as {category} / Urgent because description contains "{kw}".'
    return f'Classified as {category} based on description: "{description[:80].rstrip()}".'


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    complaint_id = row.get("complaint_id", "UNKNOWN")
    description = row.get("description", "").strip()

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "Description field is empty — cannot classify.",
            "flag": "NEEDS_REVIEW",
        }

    category, flag = detect_category(description)
    priority = detect_priority(description, category)
    reason = build_reason(description, category, priority)

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Never drops rows — output row count equals input row count.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    input_rows = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            input_rows.append(row)

    output_rows = []
    for row in input_rows:
        try:
            result = classify_complaint(row)
        except Exception as e:
            result = {
                "complaint_id": row.get("complaint_id", "UNKNOWN"),
                "category": "Other",
                "priority": "Standard",
                "reason": f"Classification error: {e}",
                "flag": "NEEDS_REVIEW",
            }
        # Merge original row with classification output
        output_rows.append({**row, **result})

    if not output_rows:
        print("Warning: no rows found in input file.")
        return

    fieldnames = list(output_rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
