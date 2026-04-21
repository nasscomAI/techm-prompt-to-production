"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import re

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    
    TODO: Build this using your AI tool guided by your agents.md and skills.md.
    Your RICE enforcement rules must be reflected in this function's behaviour.
    """
    description = row.get('description', '').lower()
    complaint_id = row.get('complaint_id', '')
    
    # Define category keywords
    categories = {
        'Pothole': ['pothole', 'potholes', 'tyre', 'blowout', 'accident'],
        'Flooding': ['flood', 'water', 'rain', 'drain'],
        'Streetlight': ['lamp', 'light', 'streetlight', 'darkness', 'tripped', 'substation'],
        'Waste': ['waste', 'overflowing', 'piles'],
        'Noise': ['noise', 'band', 'playing', 'amplifiers'],
        'Road Damage': ['road', 'damage', 'broken', 'buckled', 'subsided', 'footpath', 'cobblestone'],
        'Heritage Damage': ['heritage', 'historic', 'defaced', 'billboard'],
        'Heat Hazard': ['heat', 'hazard'],
        'Drain Blockage': ['drain', 'blockage'],
    }
    
    # Find matching categories
    matching_categories = []
    for cat, keywords in categories.items():
        if any(kw in description for kw in keywords):
            matching_categories.append(cat)
    
    if len(matching_categories) == 1:
        category = matching_categories[0]
        flag = ''
    elif len(matching_categories) > 1:
        category = 'Other'
        flag = 'NEEDS_REVIEW'
    else:
        category = 'Other'
        flag = 'NEEDS_REVIEW'
    
    # Priority
    severity_keywords = ['injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse']
    if any(kw in description for kw in severity_keywords):
        priority = 'Urgent'
    else:
        priority = 'Standard'
    
    # Reason
    if category != 'Other':
        cited_words = []
        for kw in categories[category]:
            if kw in description:
                cited_words.append(f"'{kw}'")
        reason = f"Classified as {category} because description contains {', '.join(cited_words)}."
    else:
        if len(matching_categories) > 1:
            all_cited = set()
            for cat in matching_categories:
                for kw in categories[cat]:
                    if kw in description:
                        all_cited.add(f"'{kw}'")
            reason = f"Classified as Other because description contains conflicting keywords {', '.join(sorted(all_cited))} matching multiple categories."
        elif len(matching_categories) == 0:
            reason = "Classified as Other because description does not contain keywords matching any specific category."
        else:
            reason = "Classified as Other based on description analysis."
    
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
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    classified = classify_complaint(row)
                    results.append(classified)
                except Exception as e:
                    # On failure, add with Other and flag
                    results.append({
                        'complaint_id': row.get('complaint_id', ''),
                        'category': 'Other',
                        'priority': 'Standard',
                        'reason': f'Classification failed: {str(e)}',
                        'flag': 'NEEDS_REVIEW'
                    })
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Write output
    if results:
        fieldnames = ['complaint_id', 'category', 'priority', 'reason', 'flag']
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        except Exception as e:
            print(f"Error writing output file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
