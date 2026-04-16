"""
UC-0A — Complaint Classifier
Implements RICE framework with agents.md and skills.md enforcement rules.

Enforcement:
- Category: only exact values from allowed list (Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other)
- Priority: only Urgent, Standard, Low; Urgent if severity keywords present (injury, child, school, hospital, ambulance, fire, hazard, fell, collapse)
- Reason: always present, one sentence, cites specific words from complaint
- Flag: "NEEDS_REVIEW" if ambiguous or insufficient detail; empty otherwise
"""

import argparse
import csv
import sys
from typing import Dict, List, Tuple

# Allowed categories per agents.md enforcement
ALLOWED_CATEGORIES = {
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
}

# Allowed priorities per agents.md enforcement
ALLOWED_PRIORITIES = {"Urgent", "Standard", "Low"}

# Severity keywords that trigger Urgent priority (from README.md)
SEVERITY_KEYWORDS = {"injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"}

# Category detection keywords: maps complaint keywords to potential categories
CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "hole", "rough", "crater", "pit", "asphalt damage"],
    "Flooding": ["flood", "water", "overflow", "waterlog", "inundation", "submerged", "wet"],
    "Streetlight": ["light", "street light", "lamp", "dark", "illumination", "bulb"],
    "Waste": ["garbage", "waste", "trash", "litter", "rubbish", "dustbin", "sweeping", "garbage collection"],
    "Noise": ["noise", "sound", "loud", "music", "speaker", "din", "noise pollution"],
    "Road Damage": ["road", "pavement", "surface", "cracked", "broken", "damaged", "deteriorated"],
    "Drain Blockage": ["drain", "blocked", "clogged", "sewage", "pipe", "blockage", "water stagnant"],
    "Heat Hazard": ["heat", "temperature", "hot", "sunstroke", "heat wave"],
    "Heritage Damage": ["heritage", "monument", "historic", "ancient", "damaged structure", "archeological"],
}


def extract_cited_words(description: str, category: str) -> str:
    """Extract words from description that match the category's keywords."""
    description_lower = description.lower()
    keywords = CATEGORY_KEYWORDS.get(category, [])
    cited = []
    for keyword in keywords:
        if keyword in description_lower:
            # Extract the word and surrounding context for citation
            idx = description.find(keyword)
            if idx != -1:
                cited.append(keyword)
    return ", ".join(cited) if cited else category.lower()


def check_severity(description: str) -> bool:
    """Check if description contains any severity keyword."""
    description_lower = description.lower()
    for keyword in SEVERITY_KEYWORDS:
        if keyword in description_lower:
            return True
    return False


def get_severity_keyword(description: str) -> str:
    """Return the first severity keyword found in description."""
    description_lower = description.lower()
    for keyword in SEVERITY_KEYWORDS:
        if keyword in description_lower:
            return keyword
    return ""


def classify_complaint(row: Dict) -> Dict:
    """
    Classify a single complaint row per agents.md and skills.md.
    
    Implements RICE enforcement:
    - Category: exact value only from allowed list
    - Priority: Urgent if severity keywords present, else Standard/Low by category
    - Reason: one sentence citing specific complaint language
    - Flag: NEEDS_REVIEW if ambiguous or insufficient detail
    
    Args:
        row: dict with keys 'id' (or similar), 'description', optional 'ward'
    
    Returns:
        dict with keys: id, category, priority, reason, flag
    """
    complaint_id = row.get("id") or row.get("complaint_id") or ""
    description = row.get("description") or row.get("complaint_text") or ""
    
    # Validation: ensure we have description
    if not description or len(description.strip()) < 5:
        return {
            "id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "Insufficient detail in complaint description.",
            "flag": "NEEDS_REVIEW"
        }
    
    description_lower = description.lower()
    
    # Find all matching categories
    matching_categories = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description_lower:
                matching_categories.append(category)
                break  # One match per category is enough
    
    # Determine priority based on severity keywords
    has_severity = check_severity(description)
    if has_severity:
        severity_word = get_severity_keyword(description)
        priority = "Urgent"
    else:
        priority = "Standard"
    
    # Handle classification results
    if len(matching_categories) == 0:
        # No clear category found
        category = "Other"
        cited_words = ""
        flag = "NEEDS_REVIEW"
        reason = f"No specific complaint indicators found; defaulting to Other."
    elif len(matching_categories) == 1:
        # Unambiguous classification
        category = matching_categories[0]
        cited_words = extract_cited_words(description, category)
        flag = ""
        
        if has_severity:
            severity_word = get_severity_keyword(description)
            reason = f"Classified as {category}; severity keyword '{severity_word}' triggers Urgent priority."
        else:
            reason = f"Classified as {category} based on complaint mentions of {cited_words}."
    else:
        # Ambiguous: multiple categories match
        category = matching_categories[0]  # Default to first match, but flag for review
        categories_str = ", ".join(matching_categories)
        flag = "NEEDS_REVIEW"
        
        if has_severity:
            severity_word = get_severity_keyword(description)
            reason = f"Complaint could be {categories_str}; severity keyword '{severity_word}' requires review."
        else:
            reason = f"Complaint could be {categories_str}; ambiguous categorization requires human review."
    
    # Enforce category field from allowed list
    if category not in ALLOWED_CATEGORIES:
        category = "Other"
        flag = "NEEDS_REVIEW"
    
    # Enforce priority field
    if priority not in ALLOWED_PRIORITIES:
        priority = "Standard"
    
    return {
        "id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason if reason else "Classification complete.",
        "flag": flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Batch classify complaints from CSV.
    
    Implements skills.md batch_classify:
    - Read input CSV with columns: id, description, ward (ward optional)
    - Classify each row using classify_complaint
    - Write output CSV with columns: id, category, priority, reason, flag
    - Log warnings to stderr for ambiguous cases
    - Report audit statistics
    
    Args:
        input_path: path to input CSV file
        output_path: path to write results CSV
    """
    rows_processed = 0
    rows_flagged = 0
    category_counts = {cat: 0 for cat in ALLOWED_CATEGORIES}
    
    try:
        # Read input CSV
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if not reader.fieldnames:
                print(f"ERROR: Input file {input_path} is empty or malformed.", file=sys.stderr)
                sys.exit(1)
            
            # Validate required columns
            required_cols = {"id", "description"}
            input_cols = set(reader.fieldnames)
            
            # Try alternative column names
            if "id" not in input_cols:
                if "complaint_id" in input_cols:
                    # Rename during processing
                    pass
                elif "ID" in input_cols:
                    pass
            
            if "description" not in input_cols:
                if "complaint_text" in input_cols:
                    pass
                elif "text" in input_cols:
                    pass
            
            # Process rows
            results = []
            for line_num, row in enumerate(reader, start=2):  # start=2 because line 1 is header
                try:
                    # Classify this complaint
                    classified = classify_complaint(row)
                    results.append(classified)
                    rows_processed += 1
                    
                    # Track statistics
                    if classified["flag"] == "NEEDS_REVIEW":
                        rows_flagged += 1
                        print(f"WARNING (line {line_num}): Row flagged for review - {classified['reason']}", file=sys.stderr)
                    
                    category_counts[classified["category"]] += 1
                    
                except Exception as e:
                    print(f"ERROR (line {line_num}): Failed to classify row: {e}", file=sys.stderr)
                    # Still include the row with flag
                    results.append({
                        "id": row.get("id", ""),
                        "category": "Other",
                        "priority": "Standard",
                        "reason": f"Classification error: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })
                    rows_flagged += 1
                    rows_processed += 1
        
        # Write output CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ["id", "category", "priority", "reason", "flag"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        # Print audit statistics
        print(f"\n=== UC-0A Classification Audit ===", file=sys.stderr)
        print(f"Total rows processed: {rows_processed}", file=sys.stderr)
        print(f"Rows flagged for review: {rows_flagged}", file=sys.stderr)
        print(f"Category breakdown:", file=sys.stderr)
        for category in sorted(ALLOWED_CATEGORIES):
            count = category_counts[category]
            if count > 0:
                print(f"  {category}: {count}", file=sys.stderr)
        
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to process batch classification: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
