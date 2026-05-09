"""
UC-0A — Complaint Classifier
Enforces RICE rules: exact taxonomy, severity keywords trigger Urgent,
reason must cite description text, ambiguous cases flagged NEEDS_REVIEW.
"""
import argparse
import csv
import re

# Allowed categories per README enforcement rule 1
ALLOWED_CATEGORIES = {
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
}

# Severity keywords that must trigger Urgent priority per README
SEVERITY_KEYWORDS = {"injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"}

# Category detection patterns (description substring → category)
CATEGORY_PATTERNS = {
    "pothole": "Pothole",
    "hole": "Pothole",
    "flood": "Flooding",
    "water": "Flooding",
    "streetlight": "Streetlight",
    "light": "Streetlight",
    "lamp": "Streetlight",
    "waste": "Waste",
    "garbage": "Waste",
    "litter": "Waste",
    "noise": "Noise",
    "sound": "Noise",
    "loud": "Noise",
    "road damage": "Road Damage",
    "crack": "Road Damage",
    "damaged": "Road Damage",
    "heritage": "Heritage Damage",
    "monument": "Heritage Damage",
    "historic": "Heritage Damage",
    "heat": "Heat Hazard",
    "hot": "Heat Hazard",
    "summer": "Heat Hazard",
    "drain": "Drain Blockage",
    "blockage": "Drain Blockage",
    "clogged": "Drain Blockage",
}


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Inputs: dict with keys complaint_id, description
    Returns: dict with complaint_id, category, priority, reason, flag
    
    Enforces: exact taxonomy, severity→Urgent, reason cites text, ambiguous→flag
    """
    complaint_id = row.get("complaint_id", "UNKNOWN")
    description = row.get("description", "").strip()
    
    # Handle missing/empty description
    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW"
        }
    
    description_lower = description.lower()
    
    # Detect category from description patterns
    detected_categories = set()
    detected_keywords = set()
    
    for keyword, category in CATEGORY_PATTERNS.items():
        if keyword in description_lower:
            detected_categories.add(category)
            detected_keywords.add(keyword)
    
    # Determine priority from severity keywords
    has_severity = any(kw in description_lower for kw in SEVERITY_KEYWORDS)
    priority = "Urgent" if has_severity else "Standard"
    
    # Resolve category ambiguity
    if len(detected_categories) == 0:
        category = "Other"
        reason = "No recognizable complaint type in description."
        flag = "NEEDS_REVIEW"
    elif len(detected_categories) == 1:
        category = list(detected_categories)[0]
        matched_keyword = list(detected_keywords)[0]
        reason = f"Description contains '{matched_keyword}', classified as {category}."
        flag = ""
    else:
        # Multiple categories detected — ambiguous
        category = "Other"
        reason = f"Description matches multiple categories: {', '.join(sorted(detected_categories))}."
        flag = "NEEDS_REVIEW"
    
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
    Enforces: process all rows, skip invalid but log, produce output even if some fail.
    """
    results = []
    skipped_count = 0
    flagged_count = 0
    
    # Read input CSV
    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            if not reader.fieldnames or "complaint_id" not in reader.fieldnames:
                raise ValueError("Input CSV must have 'complaint_id' column")
            
            for row_idx, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                try:
                    # Validate required fields
                    if not row.get("complaint_id") or not row.get("description"):
                        print(f"[WARN] Row {row_idx}: Missing complaint_id or description. Skipping.")
                        skipped_count += 1
                        continue
                    
                    # Classify the complaint
                    classified = classify_complaint(row)
                    results.append(classified)
                    
                    if classified["flag"] == "NEEDS_REVIEW":
                        flagged_count += 1
                        print(f"[FLAG] Row {row_idx}: complaint_id={classified['complaint_id']} flagged for review.")
                
                except Exception as e:
                    print(f"[ERROR] Row {row_idx}: {str(e)}. Skipping row.")
                    skipped_count += 1
                    continue
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading input CSV: {str(e)}")
    
    # Write output CSV
    try:
        if results:
            with open(output_path, "w", newline="", encoding="utf-8") as outfile:
                fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        else:
            raise ValueError("No rows were classified. Check input file.")
    
    except Exception as e:
        raise RuntimeError(f"Error writing output CSV: {str(e)}")
    
    # Summary
    print(f"\n--- BATCH CLASSIFICATION SUMMARY ---")
    print(f"Total rows processed: {len(results)}")
    print(f"Rows skipped/invalid: {skipped_count}")
    print(f"Rows flagged NEEDS_REVIEW: {flagged_count}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    try:
        batch_classify(args.input, args.output)
    except Exception as e:
        print(f"[FATAL] {str(e)}", file=__import__("sys").stderr)
        exit(1)
