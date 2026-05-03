"""
UC-0A — Complaint Classifier
Generated based on agents.md RICE framework rules.
"""
import argparse
import csv
import sys

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on rules defined in agents.md.
    Returns: dict with original keys plus: category, priority, reason, flag
    """
    desc = row.get("description", "").lower()
    
    # Priority classification based on severity keywords
    severity_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    priority = "Standard"
    found_severity = [kw for kw in severity_keywords if kw in desc]
    if found_severity:
        priority = "Urgent"

    # Category classification mapping based on schema
    category_map = {
        "Pothole": ["pothole"],
        "Flooding": ["flood", "rain", "water"],
        "Streetlight": ["streetlight", "light", "dark"],
        "Waste": ["garbage", "waste", "bin", "smell", "animal"],
        "Noise": ["music", "noise", "loud"],
        "Road Damage": ["road", "crack", "sinking", "footpath", "tile", "surface"],
        "Heritage Damage": ["heritage"],
        "Heat Hazard": ["heat"],
        "Drain Blockage": ["drain", "manhole"]
    }
    
    matched_categories = []
    matched_keywords = []
    
    for cat, keywords in category_map.items():
        for kw in keywords:
            if kw in desc:
                if cat not in matched_categories:
                    matched_categories.append(cat)
                matched_keywords.append(kw)
                
    flag = ""
    
    # Evaluate matched categories
    if len(matched_categories) == 1:
        category = matched_categories[0]
    elif len(matched_categories) > 1:
        # Ambiguous due to multiple categories matching
        category = matched_categories[0]
        flag = "NEEDS_REVIEW"
    else:
        # Ambiguous due to no categories matching
        category = "Other"
        flag = "NEEDS_REVIEW"
        
    # Reason formulation based on description citations
    cited_words = list(set(found_severity + matched_keywords))
    if cited_words:
        reason = f"Classified based on specific words found in description: {', '.join(cited_words)}."
    else:
        reason = "No specific recognizable keywords found in description."

    # Construct the final result row
    result = row.copy()
    result["category"] = category
    result["priority"] = priority
    result["reason"] = reason
    result["flag"] = flag
    
    return result


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)

    if not rows:
        print("Warning: Input file is empty.")
        sys.exit(0)
        
    # Add our new columns to the fieldnames
    fieldnames = list(rows[0].keys()) + ["category", "priority", "reason", "flag"]
    
    try:
        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in rows:
                try:
                    classified = classify_complaint(row)
                    writer.writerow(classified)
                except Exception as e:
                    print(f"Error classifying row {row.get('complaint_id', 'UNKNOWN')}: {e}")
                    # Gracefully handle the error and write an 'Other' classification
                    out_row = row.copy()
                    out_row["category"] = "Other"
                    out_row["priority"] = "Standard"
                    out_row["reason"] = f"Error during processing: {str(e)}"
                    out_row["flag"] = "NEEDS_REVIEW"
                    writer.writerow(out_row)
    except IOError as e:
        print(f"Error writing to output file '{output_path}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
