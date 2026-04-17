"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import sys
import re

# Allowed categories (exact strings only)
ALLOWED_CATEGORIES = {
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
}

# Severity keywords that trigger Urgent priority
SEVERITY_KEYWORDS = {"injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"}

# Category detection keywords
CATEGORY_KEYWORDS = {
    "Pothole": {"pothole", "hole", "crater"},
    "Flooding": {"flood", "waterlog", "water", "submerge", "knee-deep", "stranded"},
    "Streetlight": {"streetlight", "light", "dark", "electricity", "sparking", "flickering"},
    "Waste": {"garbage", "waste", "trash", "dump", "rubbish", "bin", "dead animal"},
    "Noise": {"noise", "sound", "music", "loud", "midnight"},
    "Road Damage": {"crack", "sinking", "broken", "upturned", "tiles", "surface"},
    "Drain Blockage": {"drain", "clog", "blockage", "block", "blocked"},
    "Heritage Damage": {"heritage", "historic", "monument", "heritage street"},
}

def extract_category(description: str) -> tuple[str, bool]:
    """
    Determine category from description.
    Returns: (category, needs_review_flag)
    """
    if not description or not isinstance(description, str):
        return "Other", True
    
    desc_lower = description.lower()
    matched_categories = []
    
    # Check for category keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in desc_lower for keyword in keywords):
            matched_categories.append(category)
    
    # If multiple categories match, flag for review
    if len(matched_categories) > 1:
        # Try to pick the most specific one based on keyword order
        return matched_categories[0], True
    elif len(matched_categories) == 1:
        return matched_categories[0], False
    else:
        # No clear match
        return "Other", True

def extract_priority(description: str) -> str:
    """
    Determine priority based on severity keywords.
    Returns: "Urgent" or "Standard"
    """
    if not description or not isinstance(description, str):
        return "Standard"
    
    desc_lower = description.lower()
    
    # Check for severity keywords
    if any(keyword in desc_lower for keyword in SEVERITY_KEYWORDS):
        return "Urgent"
    
    return "Standard"

def extract_reason(description: str) -> str:
    """
    Generate reason field citing specific phrases from description.
    Returns: one sentence reason
    """
    if not description or not isinstance(description, str):
        return "No description provided."
    
    # Find relevant phrases (first 1-2 sentences or up to 80 chars)
    sentences = re.split(r'[.!?]', description)
    if sentences:
        reason = sentences[0].strip()
        if len(reason) > 100:
            reason = reason[:100] + "..."
        return reason + "."
    
    return description[:80] + "." if len(description) > 80 else description

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    complaint_id = row.get("complaint_id", "UNKNOWN")
    description = row.get("description", "")
    
    category, needs_review = extract_category(description)
    priority = extract_priority(description)
    reason = extract_reason(description)
    flag = "NEEDS_REVIEW" if needs_review else ""
    
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
    Handles errors gracefully and produces output even if some rows fail.
    """
    try:
        # Read input CSV
        input_rows = []
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or 'complaint_id' not in reader.fieldnames:
                raise ValueError("Input CSV must have 'complaint_id' column")
            
            for i, row in enumerate(reader):
                try:
                    input_rows.append(row)
                except Exception as e:
                    print(f"Warning: Error reading row {i}: {e}", file=sys.stderr)
        
        # Classify each row
        results = []
        for i, row in enumerate(input_rows):
            try:
                classification = classify_complaint(row)
                # Merge input row with classification
                result_row = dict(row)
                result_row.update(classification)
                results.append(result_row)
            except Exception as e:
                print(f"Warning: Error classifying row {i}: {e}", file=sys.stderr)
                # Still include the row, but mark as needing review
                result_row = dict(row)
                result_row.update({
                    "complaint_id": row.get("complaint_id", "UNKNOWN"),
                    "category": "Other",
                    "priority": "Standard",
                    "reason": "Classification error",
                    "flag": "NEEDS_REVIEW"
                })
                results.append(result_row)
        
        # Write output CSV
        if results:
            fieldnames = list(results[0].keys())
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
    
    except Exception as e:
        print(f"Error in batch_classify: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
