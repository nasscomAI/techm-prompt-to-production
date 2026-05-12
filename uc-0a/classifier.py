"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    complaint_id = row.get('complaint_id', row.get('id', 'unknown'))
    desc_raw = row.get('description', '')
    
    # Error handling for nulls/empty
    if not desc_raw or str(desc_raw).strip() == '':
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Normal",
            "reason": "Description is missing or empty.",
            "flag": "NEEDS_REVIEW"
        }
        
    desc = str(desc_raw).lower()
    
    # 1. Category Classification & Reasons
    category = "Other"
    flag = ""
    reason = ""
    
    if "pothole" in desc:
        category = "Pothole"
        reason = "Description contains 'pothole'."
    elif "flood" in desc or "water" in desc:
        category = "Flooding"
        reason = "Description contains 'flood' or 'water'."
    else:
        # Refusal condition
        category = "Other"
        flag = "NEEDS_REVIEW"
        reason = "Category cannot be determined from description alone."
        
    # 2. Priority Rules
    urgent_keywords = ["injury", "child", "school"]
    found_urgent = [kw for kw in urgent_keywords if kw in desc]
    
    if found_urgent:
        priority = "Urgent"
        reason += f" Flagged as Urgent due to: {', '.join(found_urgent)}."
    else:
        priority = "Normal"
        
    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason.strip(),
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    results = []
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row_idx, row in enumerate(reader):
                try:
                    result = classify_complaint(row)
                    results.append(result)
                except Exception as e:
                    # Catch-all to prevent crash on bad rows
                    results.append({
                        "complaint_id": row.get('complaint_id', f"row_{row_idx}"),
                        "category": "Error",
                        "priority": "Unknown",
                        "reason": f"Processing error: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })
    except Exception as e:
        print(f"Error reading input file {input_path}: {e}")
        return
        
    if not results:
        print("No results generated.")
        return

    try:
        fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    except Exception as e:
        print(f"Error writing to output file {output_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
