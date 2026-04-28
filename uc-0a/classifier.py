"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import re

# Define category keywords
CATEGORY_KEYWORDS = {
    'Pothole': ['pothole', 'hole', 'sinkhole', 'crater'],
    'Flooding': ['flood', 'water', 'inundated', 'submerged', 'rain', 'storm'],
    'Streetlight': ['streetlight', 'street light', 'bulb', 'light', 'lamp'],
    'Waste': ['waste', 'garbage', 'trash', 'litter', 'dump', 'rubbish'],
    'Noise': ['noise', 'loud', 'sound', 'music', 'party', 'horn'],
    'Road Damage': ['road', 'damage', 'crack', 'broken', 'pavement', 'asphalt'],
    'Heritage Damage': ['heritage', 'monument', 'historical', 'statue', 'temple', 'building'],
    'Heat Hazard': ['heat', 'hot', 'temperature', 'sun', 'scorching'],
    'Drain Blockage': ['drain', 'blocked', 'clogged', 'sewage', 'pipe'],
}

URGENT_KEYWORDS = ['injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse']

LOW_KEYWORDS = ['dim', 'flickering', 'occasional', 'minor', 'small']

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
            'reason': 'No description provided',
            'flag': 'NEEDS_REVIEW'
        }
    
    # Determine category
    category = 'Other'
    reason_parts = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description:
                category = cat
                reason_parts.append(f"contains '{keyword}'")
                break
        if category != 'Other':
            break
    
    if category == 'Other':
        flag = 'NEEDS_REVIEW'
    else:
        flag = ''
    
    # Determine priority
    if any(keyword in description for keyword in URGENT_KEYWORDS):
        priority = 'Urgent'
        if not reason_parts:
            reason_parts.append("contains urgent keywords")
    elif any(keyword in description for keyword in LOW_KEYWORDS):
        priority = 'Low'
        if not reason_parts:
            reason_parts.append("appears minor")
    else:
        priority = 'Standard'
    
    reason = f"Description {', '.join(reason_parts)} indicating {category.lower()} issue."
    
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
    
    TODO: Build this using your AI tool.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    results = []
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    classified = classify_complaint(row)
                    results.append(classified)
                except Exception as e:
                    # On failure, add a row with error
                    complaint_id = row.get('complaint_id', 'unknown')
                    results.append({
                        'complaint_id': complaint_id,
                        'category': 'Other',
                        'priority': 'Low',
                        'reason': f'Classification failed: {str(e)}',
                        'flag': 'NEEDS_REVIEW'
                    })
    except FileNotFoundError:
        print(f"Input file {input_path} not found.")
        return
    
    # Write output
    if results:
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['complaint_id', 'category', 'priority', 'reason', 'flag']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
