import argparse
import csv
import os

# --- SKILLS DEFINED IN skills.md ---

def classify_complaint(row: dict) -> dict:
    """
    Classifies a single citizen complaint row into a strict taxonomy and priority level with justification.
    Follows enforcement rules in agents.md.
    """
    description = row.get("description", "").lower()
    complaint_id = row.get("complaint_id", "Unknown")
    
    # 1. Enforcement: Priority Assessment (Severity Triggers)
    # Severity keywords that must trigger Urgent: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse
    priority = "Standard"
    severity_keywords = ["injury", "child", "school", "hospital", "ambulance", "fire", "hazard", "fell", "collapse"]
    found_severity_keywords = [word for word in severity_keywords if word in description]
    
    if found_severity_keywords:
        priority = "Urgent"
    else:
        # Defaulting to Standard as per common practice in this UC
        priority = "Standard"

    # 2. Enforcement: Category Classification (Strict Taxonomy)
    # Allowed: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other
    taxonomy = {
        "Pothole": ["pothole", "crater", "pitted"],
        "Flooding": ["flood", "rainwater", "inundation", "waterlogged", "flooding"],
        "Streetlight": ["light", "dark", "lamp", "bulb", "streetlight"],
        "Waste": ["garbage", "waste", "litter", "trash", "dump"],
        "Noise": ["noise", "drilling", "loud", "idling", "sound"],
        "Road Damage": ["collapsed", "damage", "crack", "pavement"],
        "Heritage Damage": ["heritage", "monument", "statue", "ancient"],
        "Heat Hazard": ["heat", "hot", "sun", "warm", "temperature"],
        "Drain Blockage": ["drain", "blocked", "clogged", "sewage", "blockage"]
    }
    
    matched_categories = []
    for cat, keywords in taxonomy.items():
        if any(kw in description for kw in keywords):
            matched_categories.append(cat)
    
    category = "Other"
    flag = ""
    
    if len(matched_categories) == 1:
        category = matched_categories[0]
    elif len(matched_categories) > 1:
        # Genuinely ambiguous (e.g., mentions both drain and flooding)
        category = matched_categories[0] 
        flag = "NEEDS_REVIEW"
    else:
        category = "Other"
        # If it matches nothing but has text, it might be ambiguous
        if description.strip():
            flag = "NEEDS_REVIEW"

    # 3. Enforcement: Reason Citation (Exactly one sentence)
    if matched_categories:
        # Cite specific words from description
        cited_words = []
        for kw in taxonomy[category]:
            if kw in description:
                cited_words.append(kw)
        reason = f"Classified as {category} because the description mentions '{', '.join(cited_words)}'."
    else:
        reason = "Classified as Other because no specific taxonomy keywords were identified in the description."

    if priority == "Urgent" and found_severity_keywords:
        # Append to the sentence to keep it as one compound sentence or just refine it
        reason = reason.rstrip('.') + f" and assigned Urgent priority due to the severity trigger '{found_severity_keywords[0]}'."

    # Final result row
    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag
    }

def batch_classify(input_path: str, output_path: str):
    """
    Automates the classification of complaints by processing an input CSV file and generating an output results CSV.
    Handles empty files, missing justifications, and maintains taxonomic consistency.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    results = []
    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
            
            if not rows:
                print(f"Warning: Input file {input_path} is empty.")
                return

            for row in rows:
                try:
                    results.append(classify_complaint(row))
                except Exception as e:
                    # Error handling: flagging failed rows
                    results.append({
                        "complaint_id": row.get("complaint_id", "Unknown"),
                        "category": "Other",
                        "priority": "Standard",
                        "reason": f"Internal processing error: {str(e)}",
                        "flag": "NEEDS_REVIEW"
                    })

        # Write output
        if results:
            # UC README intent: category, priority, reason, flag
            # We include complaint_id to make the results traceable
            fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
            
            with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"Successfully processed {len(results)} rows and saved to {output_path}")

    except Exception as e:
        print(f"Fatal error during batch processing: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to input test CSV")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    batch_classify(args.input, args.output)
