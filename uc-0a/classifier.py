"""
UC-0A — Complaint Classifier
Built using the RICE → agents.md → skills.md → CRAFT workflow.
Enforces exact schema matching, severity detection, and ambiguity flagging.
"""
import argparse
import csv
import re
from typing import Dict, List

# ============================================================================
# ENFORCEMENT CONSTANTS (from skills.md)
# ============================================================================

ALLOWED_CATEGORIES = {
    "Pothole",
    "Flooding",
    "Streetlight",
    "Waste",
    "Noise",
    "Road Damage",
    "Heritage Damage",
    "Heat Hazard",
    "Drain Blockage",
    "Other"
}

ALLOWED_PRIORITIES = {"Urgent", "Standard", "Low"}

# Severity keywords that trigger Urgent priority (case-insensitive)
SEVERITY_KEYWORDS = {
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse"
}

# Category detection patterns (simplified heuristics)
CATEGORY_PATTERNS = {
    "Pothole": r"\b(pothole|hole|pit|crater)\b",
    "Flooding": r"\b(flood|water|submerged|waterlogged)\b",
    "Streetlight": r"\b(light|streetlight|lamp|bulb|dark)\b",
    "Waste": r"\b(waste|garbage|rubbish|trash|litter)\b",
    "Noise": r"\b(noise|sound|loud|honking|traffic noise)\b",
    "Road Damage": r"\b(road damage|asphalt|pavement|broken road|uneven)\b",
    "Heritage Damage": r"\b(heritage|monument|historical|structure)\b",
    "Heat Hazard": r"\b(heat|temperature|hot|burning)\b",
    "Drain Blockage": r"\b(drain|blocked|blockage|sewage|clogged)\b",
}

# ============================================================================
# SKILL 1: classify_complaint
# ============================================================================

def classify_complaint(row: dict, row_id: int = None) -> dict:
    """
    Classify a single complaint row into category, priority, reason, and flag.
    
    Implements Skill 1 from skills.md:
    - Input: complaint description text
    - Output: category, priority, reason, flag
    - Enforces exact category matching
    - Detects severity keywords for Urgent priority
    - Flags genuinely ambiguous complaints for review
    
    Args:
        row: dict with complaint data (must contain 'description' or similar text field)
        row_id: optional row number for error tracking
    
    Returns:
        dict with keys: complaint_id, category, priority, reason, flag
    """
    # Extract complaint text (try common field names)
    description = row.get("description") or row.get("complaint") or row.get("text") or ""
    complaint_id = row.get("complaint_id") or row.get("id") or f"row_{row_id}"
    
    if not description or not description.strip():
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "No description provided",
            "flag": "NEEDS_REVIEW"
        }
    
    description_lower = description.lower()
    
    # ========================================================================
    # RULE 1: Detect severity keywords → Urgent priority
    # ========================================================================
    has_severity = any(keyword in description_lower for keyword in SEVERITY_KEYWORDS)
    priority = "Urgent" if has_severity else "Standard"
    
    # ========================================================================
    # RULE 2: Detect category via pattern matching
    # ========================================================================
    matched_categories = []
    for category, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, description_lower, re.IGNORECASE):
            matched_categories.append(category)
    
    # Determine category and flag
    if len(matched_categories) == 0:
        category = "Other"
        reason = f"No specific category keywords found."
        flag = "NEEDS_REVIEW"
    elif len(matched_categories) == 1:
        category = matched_categories[0]
        # Extract relevant words for reason
        reason = f"Classified as {category} based on complaint description."
        flag = ""  # Clear flag when unambiguous
    else:
        # Multiple categories match → ambiguous
        category = matched_categories[0]  # Pick first; all are plausible
        reason = f"Multiple categories possible: {', '.join(matched_categories)}. Selected {category}."
        flag = "NEEDS_REVIEW"
    
    # ========================================================================
    # RULE 3: Ensure reason cites specific words from description
    # ========================================================================
    # Extract first few keywords from description for reason
    words = [w for w in description.split() if len(w) > 3][:3]
    cited_words = ", ".join(words) if words else "complaint details"
    reason = f"{category} classification based on '{cited_words}'."
    
    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }


# ============================================================================
# SKILL 2: batch_classify
# ============================================================================

def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    
    Implements Skill 2 from skills.md:
    - Reads input CSV file
    - Applies classify_complaint to each row
    - Writes output CSV with classified results
    - Handles errors gracefully without crashing
    
    Args:
        input_path: path to input CSV file
        output_path: path to write results CSV
    """
    results = []
    error_count = 0
    
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for row_num, row in enumerate(reader, start=2):  # 2 = header is row 1
                try:
                    result = classify_complaint(row, row_id=row_num)
                    results.append(result)
                except Exception as e:
                    error_count += 1
                    print(f"Warning: Row {row_num} failed: {e}")
                    # Still add a result row so output has all rows
                    results.append({
                        "complaint_id": row.get("complaint_id", f"row_{row_num}"),
                        "category": "Other",
                        "priority": "Standard",
                        "reason": f"Processing error: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })
    
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Write results CSV
    try:
        fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"✓ Classified {len(results) - error_count} rows successfully")
        if error_count > 0:
            print(f"⚠ {error_count} rows had errors (flagged for review)")
        print(f"✓ Results written to {output_path}")
    
    except Exception as e:
        print(f"Error writing output file: {e}")
        return


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
