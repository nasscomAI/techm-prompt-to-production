"""
UC-0A — Complaint Classifier
Built using agents.md and skills.md.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row according to UC-0A schema.
    Returns: dict with keys: category, priority, reason, flag
    """
    desc = row.get('description', '').strip()
    if not desc:
        return {
            'category': 'Other',
            'priority': 'Standard',
            'reason': 'No description provided.',
            'flag': 'NEEDS_REVIEW'
        }
    
    desc_lower = desc.lower()
    
    # Category mapping based on keywords in description
    category_keywords = {
        'Pothole': ['pothole'],
        'Flooding': ['flood', 'flooded', 'floods'],
        'Streetlight': ['streetlight'],
        'Waste': ['waste', 'garbage', 'overflow'],
        'Noise': ['noise', 'drilling', 'idling'],
        'Road Damage': ['road damage', 'collapsed', 'collapse', 'crater'],
        'Heritage Damage': ['heritage'],
        'Heat Hazard': ['heat'],
        'Drain Blockage': ['drain blocked', 'drain blockage', 'blocked'],
    }
    
    category = 'Other'
    for cat, keywords in category_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            category = cat
            break
    
    # Priority: Urgent if severity keywords present, else Standard
    severity_keywords = ['injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse']
    priority = 'Urgent' if any(kw in desc_lower for kw in severity_keywords) else 'Standard'
    
    # Reason: one sentence citing specific words
    if category != 'Other':
        # Find a matching keyword for reason
        matching_kw = next((kw for cat, kws in category_keywords.items() for kw in kws if kw in desc_lower), 'relevant terms')
        reason = f"The description mentions '{matching_kw}' indicating {category.lower()}."
    else:
        reason = f"The description '{desc}' does not clearly match any category."
    
    # Flag: NEEDS_REVIEW if Other, else blank
    flag = 'NEEDS_REVIEW' if category == 'Other' else ''
    
    return {
        'category': category,
        'priority': priority,
        'reason': reason,
        'flag': flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file {input_path} not found.")
        return
    
    results = []
    for row in rows:
        classified = classify_complaint(row)
        # Merge original row with classified fields
        result_row = {**row, **classified}
        results.append(result_row)
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            if results:
                fieldnames = list(results[0].keys())
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        print(f"Classification complete. Results written to {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
