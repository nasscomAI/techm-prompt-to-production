"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row with strict enforcement.
    Applies hierarchical taxonomy rules to avoid false ambiguity and expanded severity checks.
    """
    desc = row.get("description", "").lower()
    
    # 1. Hierarchical Taxonomy Rules (Specific > Generic)
    # Order determines precedence. First match wins to avoid over-hedging.
    hierarchy = [
        ("Heritage Damage", ["heritage", "historic", "museum", "stone", "precinct"]),
        ("Pothole", ["pothole"]),
        ("Noise", ["noise", "band", "amplifier", "music"]),
        ("Waste", ["waste", "garbage", "overflow", "piles"]),
        ("Drain Blockage", ["drain"]),
        ("Flooding", ["flood", "rainwater"]),
        ("Streetlight", ["lamp", "light", "substation", "darkness", "streetlight"]),
        ("Road Damage", ["road", "footpath", "paving", "buckled", "subsided", "cobblestones"])
    ]

    category = "Other"
    reason = "No specific keywords matched in the description."
    flag = ""
    matched_categories = []

    for cat_name, keywords in hierarchy:
        for kw in keywords:
            if kw in desc:
                matched_categories.append((cat_name, kw))
                break # Only need one keyword per category

    if matched_categories:
        # Take the most specific (first matched based on hierarchy)
        best_match = matched_categories[0]
        category = best_match[0]
        reason = f"Classified as {category} because description mentions '{best_match[1]}'."
        
        # Check for genuine ambiguity among top specific categories (e.g. Noise and Pothole)
        # We ignore generic ones like Road Damage if a specific one matched.
        specific_matches = [m for m in matched_categories if m[0] not in ("Road Damage", "Other")]
        if len(specific_matches) > 1 and specific_matches[0][0] != specific_matches[1][0]:
            flag = "NEEDS_REVIEW"
            reason += f" Flagged for review due to multiple specific issues: '{specific_matches[0][1]}' and '{specific_matches[1][1]}'."
    else:
        if "gas leak" in desc or "pipeline" in desc or "accident" in desc:
            flag = "NEEDS_REVIEW"
            reason = "Complex case involving severe infrastructure risks not covered by primary taxonomy."

    # 2. Priority Rules (Expanded Severity Keywords)
    severity_keywords = [
        'injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 
        'fell', 'collapse', 'blowout', 'accident', 'leak', 'risk', 'fallen', 
        'defaced', 'blood'
    ]
    
    priority = "Standard"
    for word in severity_keywords:
        if word in desc:
            priority = "Urgent"
            reason += f" Priority set to Urgent due to severity keyword '{word}'."
            break

    return {
        "complaint_id": row.get("complaint_id", "UNKNOWN"),
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
    with open(input_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            classified = classify_complaint(row)
            # Add original data back for context
            classified["description"] = row.get("description", "")
            results.append(classified)
            
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        if not results:
            return
        fieldnames = ["complaint_id", "category", "priority", "reason", "flag", "description"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
