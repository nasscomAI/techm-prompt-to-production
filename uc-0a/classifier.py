"""
UC-0A — Complaint Classifier
Built using agents.md + skills.md classification schema.
"""
import argparse
import csv
import re

# Allowed categories (exact strings — no variations)
CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other",
]

# Severity keywords that must trigger Urgent priority
SEVERITY_KEYWORDS = {
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
}

# Keyword rules: ordered list of (category, keywords).
# First match wins. Keywords are checked against the lowercased description.
CATEGORY_RULES = [
    ("Heritage Damage",  ["heritage"]),
    ("Heat Hazard",      ["heat hazard", "heat wave", "heat stress"]),
    ("Drain Blockage",   ["drain block", "blocked drain", "blockage", "drain chok"]),
    ("Flooding",         ["flood", "waterlog", "water logging", "inundat", "knee-deep", "standing in water"]),
    ("Pothole",          ["pothole", "pot hole"]),
    ("Streetlight",      ["streetlight", "street light", "street lamp", "lamp post", "lighting"]),
    ("Noise",            ["noise", "music", "loud", "sound", "decibel"]),
    ("Waste",            ["garbage", "waste", "rubbish", "litter", "dump", "bin", "dead animal", "animal not removed"]),
    ("Road Damage",      ["road surface", "road crack", "sinking", "manhole", "footpath", "pavement", "tarmac", "road damage", "cracked road"]),
]


def _detect_category(description: str):
    """Return (category, ambiguous) for the given description."""
    text = description.lower()
    matched = []
    for category, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            matched.append(category)

    if len(matched) == 1:
        return matched[0], False
    if len(matched) > 1:
        # Return the first matched category but flag as ambiguous
        return matched[0], True
    return "Other", True


def _detect_priority(description: str) -> str:
    """Return Urgent / Standard / Low based on severity keywords."""
    words = set(re.findall(r"[a-z]+", description.lower()))
    if words & SEVERITY_KEYWORDS:
        return "Urgent"
    return "Standard"


def _build_reason(description: str, category: str) -> str:
    """One sentence citing specific words from the description."""
    # Truncate to a reasonable length while keeping the sentence readable
    excerpt = description if len(description) <= 120 else description[:117] + "..."
    return f"Classified as {category} based on description: \"{excerpt}\""


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = (row.get("description") or "").strip()

    if not description:
        return {
            "complaint_id": row.get("complaint_id", ""),
            "category": "Other",
            "priority": "Low",
            "reason": "Description could not be parsed.",
            "flag": "NEEDS_REVIEW",
        }

    category, ambiguous = _detect_category(description)
    priority = _detect_priority(description)
    reason = _build_reason(description, category)
    flag = "NEEDS_REVIEW" if ambiguous else ""

    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Preserves original columns and appends: category, priority, reason, flag.
    """
    results = []

    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames is None:
            raise ValueError(f"Input file '{input_path}' is empty or has no header row.")
        original_fields = list(reader.fieldnames)

        for row in reader:
            try:
                classification = classify_complaint(row)
            except Exception as exc:
                classification = {
                    "complaint_id": row.get("complaint_id", ""),
                    "category": "Other",
                    "priority": "Low",
                    "reason": f"Row processing error: {exc}",
                    "flag": "NEEDS_REVIEW",
                }
            merged = dict(row)
            merged["category"] = classification["category"]
            merged["priority"] = classification["priority"]
            merged["reason"]   = classification["reason"]
            merged["flag"]     = classification["flag"]
            results.append(merged)

    output_fields = original_fields + [
        f for f in ["category", "priority", "reason", "flag"]
        if f not in original_fields
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
