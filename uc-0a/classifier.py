"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    
    TODO: Build this using your AI tool guided by your agents.md and skills.md.
    Your RICE enforcement rules must be reflected in this function's behaviour.
    """
    # Enforcement values from README / agents.md
    ALLOWED_CATEGORIES = [
        "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
        "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
    ]
    SEVERITY_KEYWORDS = [
        "injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"
    ]

    description = (row.get("description") or "").strip()
    if not description:
        return {
            "category": "Other",
            "priority": "Low",
            "reason": "Missing description in input; cannot classify confidently.",
            "flag": "NEEDS_REVIEW",
        }

    desc_lower = description.lower()

    # simple keyword -> category mapping (rule-based, conservative)
    mapping = {
        "pothole": "Pothole",
        "sinkhole": "Pothole",
        "flood": "Flooding",
        "water logging": "Flooding",
        "streetlight": "Streetlight",
        "light not working": "Streetlight",
        "garbage": "Waste",
        "trash": "Waste",
        "dump": "Waste",
        "noise": "Noise",
        "loud": "Noise",
        "road": "Road Damage",
        "crack": "Road Damage",
        "sink": "Road Damage",
        "heritage": "Heritage Damage",
        "monument": "Heritage Damage",
        "heat": "Heat Hazard",
        "hot": "Heat Hazard",
        "drain": "Drain Blockage",
        "sewer": "Drain Blockage",
        "blocked": "Drain Blockage",
    }

    matched_cats = set()
    matched_tokens = set()
    for token, cat in mapping.items():
        if token in desc_lower:
            matched_cats.add(cat)
            matched_tokens.add(token)

    # Decide priority
    priority = "Standard"
    for sk in SEVERITY_KEYWORDS:
        if sk in desc_lower:
            priority = "Urgent"
            break

    # Resolve category or set NEEDS_REVIEW when ambiguous / unknown
    if len(matched_cats) == 1:
        category = next(iter(matched_cats))
        flag = ""
        reason = f"Contains words {sorted(list(matched_tokens))} in description supporting {category}."
    elif len(matched_cats) > 1:
        category = "Other"
        flag = "NEEDS_REVIEW"
        reason = f"Multiple category indicators {sorted(list(matched_tokens))} found, ambiguous classification."
    else:
        category = "Other"
        flag = "NEEDS_REVIEW"
        reason = "No clear category keywords found in description; manual review needed."

    return {
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    
    TODO: Build this using your AI tool.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    with open(input_path, newline='', encoding='utf-8') as infp:
        reader = csv.DictReader(infp)
        rows = list(reader)

    if not rows:
        # write header with expected output fields
        fieldnames = (reader.fieldnames or []) + ["category", "priority", "reason", "flag"]
        with open(output_path, 'w', newline='', encoding='utf-8') as outfp:
            writer = csv.DictWriter(outfp, fieldnames=fieldnames)
            writer.writeheader()
        return

    # prepare output fieldnames (preserve original columns)
    fieldnames = reader.fieldnames + ["category", "priority", "reason", "flag"]
    errors = []

    with open(output_path, 'w', newline='', encoding='utf-8') as outfp:
        writer = csv.DictWriter(outfp, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            try:
                result = classify_complaint(row)
                out_row = dict(row) if row is not None else {}
                out_row.update({
                    "category": result.get("category", "Other"),
                    "priority": result.get("priority", "Standard"),
                    "reason": result.get("reason", ""),
                    "flag": result.get("flag", ""),
                })
                writer.writerow(out_row)
            except Exception as e:
                errors.append((idx, str(e)))
                # write a fallback row marking review needed
                out_row = dict(row) if row is not None else {}
                out_row.update({
                    "category": "Other",
                    "priority": "Low",
                    "reason": f"Error during classification: {e}",
                    "flag": "NEEDS_REVIEW",
                })
                writer.writerow(out_row)

    if errors:
        print(f"Completed with {len(errors)} row errors; see output for flagged rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
