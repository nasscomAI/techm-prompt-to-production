"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import json
import os
import sys

# Setup path to import llm_adapter from uc-mcp
# This ensures we can reuse the shared LLM adapter logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uc-mcp")))
from llm_adapter import call_llm

# Enforcement Rules from agents.md
CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
]

PRIORITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse"
]

SYSTEM_PROMPT = f"""
You are a Citizen Complaint Classifier for a municipal government.
Your operational boundary is to analyze incoming citizen reports and accurately categorize and prioritize them.

ENFORCEMENT RULES:
1. Category must be EXACTLY ONE of: {", ".join(CATEGORIES)}.
2. Priority must be "Urgent" if the description contains any of: {", ".join(PRIORITY_KEYWORDS)}. Otherwise use "Standard" or "Low".
3. Reason field must cite specific words from the description.
4. If category is underdetermined, use Category: "Other" and Flag: "NEEDS_REVIEW". Otherwise, leave Flag blank.

Output format: Return ONLY a JSON object with keys: category, priority, reason, flag.
"""

def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = row.get("description", "").lower()
    complaint_id = row.get("complaint_id", "UNKNOWN")
    
    # Priority Rule (Python-level for strict enforcement)
    # We check these keywords in Python to ensure 100% compliance with agents.md
    priority_override = None
    matched_keywords = [word for word in PRIORITY_KEYWORDS if word in description]
    if matched_keywords:
        priority_override = "Urgent"

    # Call LLM for categorization and reasoning
    prompt = f"{SYSTEM_PROMPT}\n\nDescription: {row.get('description')}\n\nJSON Output:"
    
    response_text = call_llm(prompt).strip()
    
    # Clean response (sometimes LLMs wrap in backticks or include preamble)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].strip()
    
    try:
        result = json.loads(response_text)
    except Exception:
        # Fallback if LLM output is not valid JSON
        result = {
            "category": "Other",
            "priority": priority_override or "Standard",
            "reason": "Failed to parse LLM response.",
            "flag": "NEEDS_REVIEW"
        }
    
    # Force compliance with enforcement rules
    result["complaint_id"] = complaint_id
    
    # Apply keyword-based priority override for safety
    if priority_override:
        result["priority"] = priority_override
    
    # Ensure category is exactly from the allowed list
    if result.get("category") not in CATEGORIES:
        result["category"] = "Other"
        result["flag"] = "NEEDS_REVIEW"
        
    return result


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    results = []
    with open(input_path, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            if not row.get("description"):
                # Handle nulls
                results.append({
                    "complaint_id": row.get("complaint_id", "UNKNOWN"),
                    "category": "Other",
                    "priority": "Low",
                    "reason": "Missing description",
                    "flag": "NEEDS_REVIEW"
                })
                continue
                
            try:
                classified = classify_complaint(row)
                results.append(classified)
            except Exception as e:
                # Don't crash on bad rows
                print(f"Error processing row {row.get('complaint_id')}: {e}")
                results.append({
                    "complaint_id": row.get("complaint_id", "UNKNOWN"),
                    "category": "Other",
                    "priority": "Standard",
                    "reason": f"System error: {str(e)}",
                    "flag": "NEEDS_REVIEW"
                })

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")

