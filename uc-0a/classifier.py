"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import re

# Define categories and their keywords
CATEGORY_KEYWORDS = {
    'Pothole': ['pothole', 'tyre', 'damage', 'vehicles'],
    'Flooding': ['flooded', 'rain', 'water', 'knee-deep', 'stranded'],
    'Streetlight': ['streetlight', 'lights out', 'dark', 'flickering', 'sparking', 'electrical hazard'],
    'Waste': ['garbage', 'overflowing', 'smell', 'dead animal', 'bulk waste', 'dumped'],
    'Noise': ['music', 'midnight', 'playing', 'loud'],
    'Road Damage': ['cracked', 'sinking', 'manhole', 'missing', 'tiles broken', 'fell', 'injury'],
    'Heritage Damage': ['heritage', 'old city'],
    'Heat Hazard': ['heat', 'hot'],
    'Drain Blockage': ['drain blocked'],
    'Other': []
}

SEVERITY_KEYWORDS = ['injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse']

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    complaint_id = row.get('complaint_id', '')
    description = row.get('description', '').lower()
    
    if not description:
        return {
            'complaint_id': complaint_id,
            'category': 'Other',
            'priority': 'Low',
            'reason': 'Invalid or empty description.',
            'flag': 'NEEDS_REVIEW'
        }
    
    # Determine category
    category = 'Other'
    matched_categories = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if cat == 'Other':
            continue
        if any(keyword in description for keyword in keywords):
            matched_categories.append(cat)
    
    if len(matched_categories) == 1:
        category = matched_categories[0]
    elif len(matched_categories) > 1:
        # Ambiguous, choose the first or flag
        category = matched_categories[0]
        flag = 'NEEDS_REVIEW'
    else:
        category = 'Other'
    
    # Determine priority
    priority = 'Standard'
    if any(keyword in description for keyword in SEVERITY_KEYWORDS):
        priority = 'Urgent'
    # For Low, perhaps if no impact mentioned, but for now, Standard if not Urgent
    
    # Reason
    reason_words = []
    if category != 'Other':
        for keyword in CATEGORY_KEYWORDS[category]:
            if keyword in description:
                reason_words.append(keyword)
    if priority == 'Urgent':
        urgent_words = [kw for kw in SEVERITY_KEYWORDS if kw in description]
        reason_words.extend(urgent_words)
    
    reason = f"The description mentions '{', '.join(reason_words)}' indicating {category.lower()} and {priority.lower()} priority."
    
    flag = 'NEEDS_REVIEW' if len(matched_categories) > 1 else ''
    
    return {
        'complaint_id': complaint_id,
        'category': category,
        'priority': priority,
        'reason': reason,
        'flag': flag
    }

def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    results = []
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    classified = classify_complaint(row)
                    results.append(classified)
                except Exception as e:
                    print(f"Error classifying row {row.get('complaint_id')}: {e}")
                    results.append({
                        'complaint_id': row.get('complaint_id', ''),
                        'category': 'Other',
                        'priority': 'Low',
                        'reason': 'Classification error.',
                        'flag': 'NEEDS_REVIEW'
                    })
    except FileNotFoundError:
        print(f"Input file {input_path} not found.")
        return
    
    # Write output
    fieldnames = ['complaint_id', 'category', 'priority', 'reason', 'flag']
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Classification complete. Results written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
