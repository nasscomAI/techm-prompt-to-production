"""
UC-0A — Complaint Classifier
"""

import argparse
import csv

# --- Constants ---

SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital",
    "ambulance", "fire", "hazard", "fell", "collapse"
]

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole"],
    "Flooding": ["flood", "waterlogging"],
    "Streetlight": ["streetlight", "light not working", "dark"],
    "Waste": ["garbage", "trash", "waste"],
    "Noise": ["noise", "loud"],
    "Road Damage": ["crack", "road broken"],
    "Heritage Damage": ["monument", "heritage"],
    "Heat Hazard": ["heat", "hot"],
    "Drain Blockage": ["drain", "sewage", "blocked"]
}


# --- Core Function ---

def classify_complaint(row: dict) -> dict:
    text = (row.get("description") or "").strip()
    text_lower = text.lower()

    # --- Category Detection (STRICT: ONE MATCH ONLY) ---
    category = "Other"
    matched_word = None

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                category = cat
                matched_word = keyword
                break
        if matched_word:
            break  # ✅ stop after FIRST valid category match

    # --- Priority Detection ---
    priority = "Low"
    severity_word = None

    for word in SEVERITY_KEYWORDS:
        if word in text_lower:
            priority = "Urgent"
            severity_word = word
            break

    if priority != "Urgent":
        priority = "Standard"

    # --- Reason ---
    if not text:
        reason = "Invalid or empty complaint"
        flag = "NEEDS_REVIEW"
        category = "Other"
        priority = "Low"

    elif severity_word:
        reason = f"Contains '{severity_word}' indicating high severity"
        flag = ""

    elif matched_word:
        reason = f"Contains '{matched_word}' indicating {category.lower()} issue"
        flag = ""

    else:
        first_word = text.split()[0] if text.split() else "text"
        reason = f"Contains '{first_word}' but no category keyword matched"
        flag = ""

    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


# --- Batch Processing ---

def batch_classify(input_path: str, output_path: str):
    results = []

    with open(input_path, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            try:
                result = classify_complaint(row)
                results.append(result)

            except Exception:
                results.append({
                    "complaint_id": row.get("complaint_id", ""),
                    "category": "Other",
                    "priority": "Low",
                    "reason": "Processing error",
                    "flag": "NEEDS_REVIEW"
                })

    # --- Write Output ---
    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]

    with open(output_path, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


# --- CLI Entry ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()
    batch_classify(args.input, args.output)

    print(f"Done. Results written to {args.output}")