"""
UC-0A — Complaint Classifier
Enforces exact category taxonomy (agents.md), severity-based priority rules, and reason citations.
Implements classify_complaint and batch_classify skills as per skills.md.
"""
import argparse
import csv
import re
from typing import Dict, Tuple

# Severity keywords that trigger Urgent priority per agents.md enforcement
SEVERITY_KEYWORDS = {
    'injury', 'child', 'school', 'hospital', 'ambulance', 'fire', 'hazard', 'fell', 'collapse'
}

# Low priority indicators - minor/cosmetic/non-urgent issues
LOW_PRIORITY_KEYWORDS = {
    'minor', 'small', 'cosmetic', 'aesthetic', 'paint', 'faded', 'worn'
}

# Exact category list from agents.md enforcement
ALLOWED_CATEGORIES = {
    'Pothole', 'Flooding', 'Streetlight', 'Waste', 'Noise', 
    'Road Damage', 'Heritage Damage', 'Heat Hazard', 'Drain Blockage', 'Other'
}

# Category keyword patterns for classification per agents.md taxonomy
CATEGORY_PATTERNS = {
    'Pothole': [
        r'\bpothole', r'\bpotholes', r'\bholes?\b', r'\bcracked.*road', r'\bcrack.*road',
        r'\btyre\s*damage', r'\bwheel.*damage', r'\buneven.*surface'
    ],
    'Flooding': [
        r'\bflooded?', r'\bflooding', r'\bfloods?\b', r'\bwater\s*(?:logging|logged|level)',
        r'\bstagnant\s*water', r'\binundated', r'\bsubmerged', r'\bwater\b'
    ],
    'Streetlight': [
        r'\bstreetlight', r'\bstreet.*light', r'\blamp.*not.*working', r'\blights?\s*out',
        r'\blight.*spark', r'\bflicker', r'\belectrical\s*hazard', r'\bsparking'
    ],
    'Waste': [
        r'\bgarbage', r'\bwaste', r'\btrash', r'\blitter', r'\bwaste.*bin', r'\boverflow',
        r'\bdead\s*animal', r'\bdump.*public.*road', r'\bsmell', r'\brefuse', r'\bbin'
    ],
    'Noise': [
        r'\bnoise', r'\bmusic\s*(?:past|after)', r'\bloud', r'\bsound', r'\bpollution.*noise'
    ],
    'Road Damage': [
        r'\broad\s*(?:surface|cracked|sinking|damage)', r'\bapproach.*flood',
        r'\bmanhole\s*(?:cover\s*missing|uncovered)', r'\bupturned', r'\btiles?\s*broken',
        r'\bfootpath\s*tiles'
    ],
    'Heritage Damage': [
        r'\bheritage', r'\bold\s*city', r'\bhistoric', r'\barchaeological'
    ],
    'Heat Hazard': [
        r'\bheat\s*(?:hazard|wave)', r'\bhigh\s*temperature', r'\bextreme\s*heat'
    ],
    'Drain Blockage': [
        r'\bdrain\s*(?:block|clogged|obstructed)', r'\bblocked\s*drain', r'\bsewage',
        r'\bclogged.*drain', r'\bdrain\s*blocked'
    ]
}

def extract_keyword_match(description: str, patterns: list) -> Tuple[str, bool]:
    """
    Extract matched keyword from description for citation in reason field.
    Returns: (matched_text, was_matched)
    """
    description_lower = description.lower()
    for pattern in patterns:
        match = re.search(pattern, description_lower)
        if match:
            # Return the actual matched text from original description
            matched_text = match.group(0)
            return matched_text, True
    return "", False

def check_severity_keywords(description: str) -> bool:
    """
    Check if description contains ANY severity keywords per agents.md.
    Severity keywords: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse
    """
    description_lower = description.lower()
    return any(keyword in description_lower for keyword in SEVERITY_KEYWORDS)

def check_low_priority_indicators(description: str) -> bool:
    """Check if description contains low priority indicators for Standard→Low demotion."""
    description_lower = description.lower()
    return any(keyword in description_lower for keyword in LOW_PRIORITY_KEYWORDS)

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row per skills.md specification.
    
    Input: Dictionary with keys: complaint_id (str), description (str), ...other fields
    Output: Dictionary with keys: category, priority, reason, flag
    
    Enforces:
    - Exact category from allowed list per agents.md
    - Priority: Urgent if severity keywords present, Standard otherwise (Low only if explicit low indicators)
    - Reason: One sentence citing specific words from description
    - Flag: NEEDS_REVIEW if ambiguous, empty string otherwise
    """
    description = row.get('description', '').strip()
    
    # Handle empty/invalid input
    if not description:
        return {
            'category': 'Other',
            'priority': 'Standard',
            'reason': 'Insufficient information to classify complaint.',
            'flag': 'NEEDS_REVIEW'
        }
    
    # Determine priority per agents.md enforcement rule
    has_severity = check_severity_keywords(description)
    has_low_indicator = check_low_priority_indicators(description)
    
    if has_severity:
        priority = 'Urgent'
    elif has_low_indicator:
        priority = 'Low'
    else:
        priority = 'Standard'
    
    # Try to classify into categories
    matched_categories = []
    matched_keywords = {}
    
    for category, patterns in CATEGORY_PATTERNS.items():
        keyword, matched = extract_keyword_match(description, patterns)
        if matched:
            matched_categories.append(category)
            matched_keywords[category] = keyword
    
    # Apply classification logic per agents.md
    if len(matched_categories) == 0:
        # No match - output Other with NEEDS_REVIEW
        category = 'Other'
        reason = 'No recognizable complaint category identified from description.'
        flag = 'NEEDS_REVIEW'
    
    elif len(matched_categories) == 1:
        # Single match - confident classification
        category = matched_categories[0]
        keyword = matched_keywords[category]
        reason = f'Description contains "{keyword}" indicating {category.lower()} complaint.'
        flag = ''
    
    else:
        # Multiple matches - ambiguous, flag for human review per agents.md
        categories_str = ', '.join(matched_categories)
        category = 'Other'
        reason = f'Multiple categories match (could be {categories_str}); requires human review.'
        flag = 'NEEDS_REVIEW'
    
    # Validate category is in allowed list (enforcement)
    assert category in ALLOWED_CATEGORIES, f"Invalid category: {category}"
    assert priority in ['Urgent', 'Standard', 'Low'], f"Invalid priority: {priority}"
    assert flag in ['NEEDS_REVIEW', ''], f"Invalid flag: {flag}"
    
    return {
        'category': category,
        'priority': priority,
        'reason': reason,
        'flag': flag
    }


def batch_classify(input_path: str, output_path: str):
    """
    Batch classification skill per skills.md specification.
    
    Input: Path to CSV with columns: complaint_id, date_raised, city, ward, location, 
                                     description, reported_by, days_open
    Output: CSV with added columns: category, priority, reason, flag
    
    Error handling: Gracefully handles read/write errors and row-level classification failures.
    Flags failed rows as NEEDS_REVIEW without stopping batch.
    """
    try:
        # Read input CSV
        input_rows = []
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                input_rows = list(reader)
        except FileNotFoundError:
            print(f"Error: Input file {input_path} not found.")
            return
        except IOError as e:
            print(f"Error: Cannot read {input_path}: {e}")
            return
        
        if not input_rows:
            print(f"Warning: Input file {input_path} is empty.")
            return
        
        # Validate input CSV has required columns
        required_columns = {'complaint_id', 'date_raised', 'city', 'ward', 'location', 
                           'description', 'reported_by', 'days_open'}
        if not required_columns.issubset(input_rows[0].keys()):
            print(f"Error: Input CSV missing required columns. Expected: {required_columns}")
            return
        
        # Classify each row per classify_complaint skill
        output_rows = []
        success_count = 0
        error_count = 0
        
        for idx, row in enumerate(input_rows, start=1):
            try:
                classification = classify_complaint(row)
                output_row = {**row, **classification}
                output_rows.append(output_row)
                success_count += 1
            except Exception as e:
                # Graceful error handling - flag row for review
                error_count += 1
                output_row = {
                    **row,
                    'category': 'Other',
                    'priority': 'Standard',
                    'reason': f'Classification error: {str(e)}',
                    'flag': 'NEEDS_REVIEW'
                }
                output_rows.append(output_row)
        
        # Write output CSV with new columns
        if output_rows:
            try:
                fieldnames = list(input_rows[0].keys()) + ['category', 'priority', 'reason', 'flag']
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(output_rows)
                
                print(f"Classified {success_count} complaints successfully, {error_count} errors flagged for review.")
                print(f"Results written to {output_path}")
            except IOError as e:
                print(f"Error: Cannot write to {output_path}: {e}")
    
    except Exception as e:
        print(f"Error: Batch classification failed: {e}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="UC-0A Complaint Classifier - Classifies municipal complaints per agents.md and skills.md"
    )
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv (e.g., ../data/city-test-files/test_pune.csv)")
    parser.add_argument("--output", required=True, help="Path to write results CSV (e.g., results_pune.csv)")
    args = parser.parse_args()
    
    print(f"Starting complaint classification: {args.input} → {args.output}")
    batch_classify(args.input, args.output)
