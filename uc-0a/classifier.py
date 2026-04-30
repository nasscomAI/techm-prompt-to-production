"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row based on rules defined in agents.md and skills.md.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = str(row.get('description', '')).lower()
    
    # Priority logic
    priority_keywords = ['injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse']
    priority = 'Standard'
    reason_keyword = ''
    for kw in priority_keywords:
        if kw in description:
            priority = 'Urgent'
            reason_keyword = kw
            break
            
    # Category logic
    category = 'Other'
    if 'pothole' in description:
        category = 'Pothole'
    elif 'flood' in description or 'rain' in description:
        category = 'Flooding'
    elif 'drain' in description or 'manhole' in description:
        category = 'Drain Blockage'
    elif 'streetlight' in description or 'lights out' in description:
        category = 'Streetlight'
    elif 'garbage' in description or 'waste' in description or 'animal' in description:
        category = 'Waste'
    elif 'music' in description or 'noise' in description:
        category = 'Noise'
    elif 'cracked' in description or 'broken' in description:
        category = 'Road Damage'
    elif 'heritage' in description:
        category = 'Heritage Damage'
    elif 'heat' in description:
        category = 'Heat Hazard'
        
    # Reason logic
    if reason_keyword:
        reason = f"Classified as Urgent because description contains '{reason_keyword}'."
    else:
        # Find a noun or descriptive word to cite
        words = [w for w in description.split() if len(w) > 4]
        if words:
            reason = f"Classified based on keywords like '{words[0]}' in description."
        else:
            reason = "Classified based on general description context."

    # Flag logic for ambiguity
    flag = ''
    if category == 'Other' or not description.strip():
        flag = 'NEEDS_REVIEW'

    return {
        'complaint_id': row.get('complaint_id', ''),
        'category': category,
        'priority': priority,
        'reason': reason,
        'flag': flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    results = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    classification = classify_complaint(row)
                    row.update(classification)
                    results.append(row)
                except Exception as e:
                    print(f"Skipping malformed row {row.get('complaint_id', 'unknown')}: {e}")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    if not results:
        print("No valid rows processed. Exiting.")
        return

    try:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = list(results[0].keys())
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
