"""
UC-0A — Complaint Classifier
"""
import argparse
import csv

ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

URGENT_KEYWORDS = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = row.get("description", "").lower()
    complaint_id = row.get("complaint_id", "")

    for keyword in URGENT_KEYWORDS:
        if keyword in description:
            priority = "Urgent"
            break
    else:
        priority = "Standard"

    category = None
    flag = ""

    if "pothole" in description or "hole" in description:
        category = "Pothole"
    elif "flood" in description or "water" in description:
        category = "Flooding"
    elif "street" in description and "light" in description:
        category = "Streetlight"
    elif "waste" in description or "garbage" in description or "trash" in description:
        category = "Waste"
    elif "noise" in description or "sound" in description:
        category = "Noise"
    elif "road" in description or "road" in description:
        category = "Road Damage"
    elif "heritage" in description or "historical" in description:
        category = "Heritage Damage"
    elif "heat" in description or "temperature" in description:
        category = "Heat Hazard"
    elif "drain" in description or "clog" in description:
        category = "Drain Blockage"
    else:
        category = "Other"
        flag = "NEEDS_REVIEW"

    if category == "Other":
        flag = "NEEDS_REVIEW"

    words = row.get("description", "").split()[:5]
    reason = f"Keywords found: {', '.join(words)}"

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    results = []

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if not row.get("description"):
                    continue
                result = classify_complaint(row)
                results.append(result)
            except Exception as e:
                print(f"Warning: Failed to process row: {e}")
                continue

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Classified {len(results)} complaints")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")