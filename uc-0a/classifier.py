"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv


# Allowed categories and severity keywords from the README
ALLOWED_CATEGORIES = [
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


def detect_category(description: str) -> (str, bool):
    """
    Very simple heuristic mapping from description text to category.
    Returns (category, is_ambiguous).
    You can refine this logic if needed, but it must only use allowed categories.
    """
    if not description or not description.strip():
        return "Other", True

    text = description.lower()

    # Simple keyword-based rules
    if "pothole" in text or "hole in road" in text:
        return "Pothole", False
    if "flood" in text or "water logging" in text or "waterlogging" in text:
        return "Flooding", False
    if "streetlight" in text or "street light" in text or "lamp post" in text:
        return "Streetlight", False
    if "garbage" in text or "trash" in text or "waste" in text or "dump" in text:
        return "Waste", False
    if "noise" in text or "loud" in text or "sound" in text:
        return "Noise", False
    if "road" in text or "tarmac" in text or "asphalt" in text or "crack" in text:
        return "Road Damage", False
    if "heritage" in text or "monument" in text or "temple" in text or "statue" in text:
        return "Heritage Damage", False
    if "heat" in text or "hot" in text or "heatwave" in text:
        return "Heat Hazard", False
    if "drain" in text or "sewer" in text or "blocked drain" in text or "clogged" in text:
        return "Drain Blockage", False

    # No strong signal: treat as Other and ambiguous
    return "Other", True


def detect_priority(description: str) -> str:
    """
    Determine priority based on severity keywords.
    Urgent if any severity keyword appears; otherwise Standard for now.
    (You can extend to Low based on other heuristics if needed.)
    """
    if not description:
        return "Standard"

    text = description.lower()
    for kw in SEVERITY_KEYWORDS:
        if kw in text:
            return "Urgent"
    # You could optionally add 'Low' based on very mild complaints
    return "Standard"


def build_reason(description: str, category: str, priority: str, ambiguous: bool) -> str:
    """
    Build a one-sentence reason citing words from the description.
    """
    snippet = (description or "").strip()
    # Clip long descriptions for the reason
    if len(snippet) > 80:
        snippet = snippet[:77] + "..."
    base = f"Classified as {category} with {priority} priority based on the words: \"{snippet}\"."
    if ambiguous:
        return base + " Category is ambiguous so flagged for review."
    return base


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag

    Implements the enforcement rules from agents.md:
    - category is one of the allowed list
    - priority is Urgent if severity keywords appear
    - reason cites specific words from description
    - flag is NEEDS_REVIEW for ambiguous cases
    """
    complaint_id = row.get("complaint_id") or row.get("id") or ""
    description = row.get("description") or row.get("complaint") or ""

    # Handle missing description
    if not description.strip():
        category = "Other"
        priority = "Standard"
        reason = "Description is missing or empty, so classified as Other and flagged for review."
        flag = "NEEDS_REVIEW"
        return {
            "complaint_id": complaint_id,
            "category": category,
            "priority": priority,
            "reason": reason,
            "flag": flag,
        }

    category, ambiguous = detect_category(description)

    # Enforce allowed categories
    if category not in ALLOWED_CATEGORIES:
        category = "Other"
        ambiguous = True

    priority = detect_priority(description)
    reason = build_reason(description, category, priority, ambiguous)

    flag = "NEEDS_REVIEW" if ambiguous else ""

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

    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    results = []

    with open(input_path, newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            try:
                classified = classify_complaint(row)
                results.append(classified)
            except Exception as e:
                # Fallback for bad rows: mark as Other and NEEDS_REVIEW
                fallback_id = row.get("complaint_id") or row.get("id") or ""
                results.append(
                    {
                        "complaint_id": fallback_id,
                        "category": "Other",
                        "priority": "Standard",
                        "reason": f"Row could not be processed due to error: {e}",
                        "flag": "NEEDS_REVIEW",
                    }
                )

    # Write output CSV with the required columns
    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    with open(output_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
