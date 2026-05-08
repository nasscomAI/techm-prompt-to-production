"""
UC-0A — Complaint Classifier
Implements classify_complaint and batch_classify per agents.md and skills.md.
"""
import argparse
import csv
import sys

# Enforcement rule 1: exact allowed category strings
ALLOWED_CATEGORIES = {
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
}

# Enforcement rule 2: severity keywords that must trigger Urgent priority
URGENT_KEYWORDS = {
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse"
}

# Keyword-to-category mapping (checked in order; first match wins)
CATEGORY_RULES = [
    ({"pothole", "potholes"},                          "Pothole"),
    ({"flood", "flooded", "flooding"},                 "Flooding"),
    ({"streetlight", "street light", "light out"},     "Streetlight"),
    ({"waste", "garbage", "trash", "litter"},          "Waste"),
    ({"noise", "drilling", "idling", "loud"},          "Noise"),
    ({"collapse", "collapsed", "crater", "road damage"}, "Road Damage"),
    ({"heritage", "monument", "historical"},           "Heritage Damage"),
    ({"heat", "temperature", "heatwave"},              "Heat Hazard"),
    ({"drain", "drainage", "stormwater", "blockage",
      "blocked", "sewage"},                            "Drain Blockage"),
]


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns dict with keys: complaint_id, category, priority, reason, flag.

    Enforcement (agents.md):
    - category must be one of ALLOWED_CATEGORIES
    - priority is Urgent if any URGENT_KEYWORDS appear in description
    - reason must quote specific words from the description
    - flag is NEEDS_REVIEW when category is ambiguous
    """
    complaint_id = row.get("complaint_id", "UNKNOWN")
    description = row.get("description", "").strip()

    # skills.md error_handling: missing description
    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW",
        }

    desc_lower = description.lower()

    # Determine category
    category = None
    for keywords, cat in CATEGORY_RULES:
        if any(kw in desc_lower for kw in keywords):
            category = cat
            break

    # Enforcement rule 4: ambiguous → Other + NEEDS_REVIEW
    flag = ""
    if category is None:
        category = "Other"
        flag = "NEEDS_REVIEW"

    # Enforcement rule 2: severity keywords override priority to Urgent
    matched_urgent = [kw for kw in URGENT_KEYWORDS if kw in desc_lower]
    if matched_urgent:
        priority = "Urgent"
    elif any(word in desc_lower for word in ("slow", "struggling", "suffering", "mosquito", "dengue")):
        priority = "Standard"
    else:
        priority = "Low"

    # Enforcement rule 3: reason must cite specific words from description
    if matched_urgent:
        trigger = matched_urgent[0]
        reason = f"Description contains '{trigger}', triggering Urgent priority."
    else:
        # Quote a short excerpt from the description as the reason
        excerpt = description[:80].rstrip()
        reason = f"Classified based on description: '{excerpt}'."

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, apply classify_complaint per row, write results CSV.
    Skills.md: one output row per input row, no rows dropped; failed rows get
    category: Other, flag: NEEDS_REVIEW, complaint_id logged to stderr.
    """
    output_fields = [
        "complaint_id", "date_raised", "city", "ward", "location",
        "description", "reported_by", "days_open",
        "category", "priority", "reason", "flag"
    ]

    with open(input_path, newline="", encoding="utf-8") as infile, \
         open(output_path, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=output_fields)
        writer.writeheader()

        for row in reader:
            try:
                result = classify_complaint(row)
            except Exception as exc:
                print(f"ERROR: {row.get('complaint_id', '?')} — {exc}", file=sys.stderr)
                result = {
                    "complaint_id": row.get("complaint_id", "UNKNOWN"),
                    "category": "Other",
                    "priority": "Low",
                    "reason": "Classification failed due to unexpected error.",
                    "flag": "NEEDS_REVIEW",
                }

            row.update({
                "category": result["category"],
                "priority": result["priority"],
                "reason":   result["reason"],
                "flag":     result["flag"],
            })
            writer.writerow(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
