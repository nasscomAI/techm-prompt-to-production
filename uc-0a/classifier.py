"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""

import argparse
import csv


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys:
    complaint_id, category, priority, reason, flag
    """

    complaint_id = row.get("complaint_id", "").strip()
    text = row.get("complaint_text", "")

    # Flag missing or empty complaints
    if not text:
        return {
            "complaint_id": complaint_id,
            "category": "Unclassified",
            "priority": "Low",
            "reason": "Complaint text is missing",
            "flag": "NULL_TEXT",
        }

    text_lower = text.lower()

    if any(word in text_lower for word in ["road", "pothole", "bridge", "metro"]):
        category = "Infrastructure"
        reason = "Complaint relates to roads or transport infrastructure"
    elif any(word in text_lower for word in ["water", "electricity", "power", "gas"]):
        category = "Utilities"
        reason = "Complaint relates to utility services"
    elif any(word in text_lower for word in ["garbage", "waste", "cleaning", "drain"]):
        category = "Sanitation"
        reason = "Complaint relates to sanitation or cleanliness"
    elif any(word in text_lower for word in ["municipal", "officer", "government", "authority"]):
        category = "Governance"
        reason = "Complaint relates to governance or administration"
    else:
        category = "Unclassified"
        reason = "No matching category found"

    priority = "High" if category in ["Infrastructure", "Utilities"] else "Medium"

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": "",
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """

    results = []

    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            try:
                result = classify_complaint(row)
            except Exception as e:
                result = {
                    "complaint_id": row.get("complaint_id", ""),
                    "category": "Error",
                    "priority": "Low",
                    "reason": str(e),
                    "flag": "PROCESSING_ERROR",
                }
            results.append(result)

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()

    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
