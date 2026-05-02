"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import sys
import os

CATEGORIES = [
    ("Heat Hazard", ["heat", "heatwave", "temperature", "temperatures", "sun", "44°c", "45°c", "52°c", "burn", "burns", "melting"]),
    ("Drain Blockage", ["drain", "drains", "block", "blocked"]),
    ("Heritage Damage", ["heritage", "ancient", "step well", "old city"]),
    ("Road Damage", ["road damage", "road collapse", "subsidence", "tarmac", "paving", "bubbling", "broken", "road surface", "divider", "dividers"]),
    ("Noise", ["noise", "music", "loud", "drilling", "idling"]),
    ("Waste", ["waste", "garbage", "trash", "bin", "bins"]),
    ("Streetlight", ["streetlight", "streetlights", "unlit", "dark", "lighting", "wiring"]),
    ("Flooding", ["flood", "floods", "flooded", "rain", "rains", "rainwater", "water"]),
    ("Pothole", ["pothole", "potholes", "crater", "craters"]),
]

SEVERITY_KEYWORDS = ["injury", "injured", "child", "children", "school", "hospital", "hospitalised", "ambulance", "fire", "hazard", "fell", "collapse", "collapsed"]

import re

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority_flag, reason
    """
    description = row.get("description", "").lower()
    
    category = "Other"
    priority = "Standard"
    reason = "No specific keywords found."
    matched_cat_kw = None
    
    for cat, keywords in CATEGORIES:
        for kw in keywords:
            pattern = r'(?<![a-z])' + re.escape(kw) + r'(?![a-z])'
            if re.search(pattern, description):
                category = cat
                matched_cat_kw = kw
                break
        if category != "Other":
            break
            
    if category == "Other":
        priority = "NEEDS_REVIEW"
        reason = "Category genuinely ambiguous as no keywords were matched in the description."
    else:
        matched_sev_kw = None
        for sev in SEVERITY_KEYWORDS:
            pattern = r'(?<![a-z])' + re.escape(sev) + r'(?![a-z])'
            if re.search(pattern, description):
                priority = "Urgent"
                matched_sev_kw = sev
                break
        
        if priority == "Urgent":
            reason = f"Assigned {category} due to '{matched_cat_kw}', and Urgent due to severity keyword '{matched_sev_kw}'."
        else:
            reason = f"Assigned {category} due to keyword '{matched_cat_kw}'."
            
    row["category"] = category
    row["priority_flag"] = priority
    row["reason"] = reason
    return row


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found.")

    with open(input_path, mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError("Input CSV is empty or has no header.")
            
        fieldnames = list(reader.fieldnames)
        
        for new_col in ["category", "priority_flag", "reason"]:
            if new_col not in fieldnames:
                fieldnames.append(new_col)
                
        rows = list(reader)

    with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            try:
                classified_row = classify_complaint(row)
                writer.writerow(classified_row)
            except Exception as e:
                # Do not crash on bad rows, produce output even if some rows fail.
                row["category"] = "Other"
                row["priority_flag"] = "NEEDS_REVIEW"
                row["reason"] = f"Error processing row: {str(e)}"
                writer.writerow(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
