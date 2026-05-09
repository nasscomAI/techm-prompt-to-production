import csv
import argparse
import os
import re

class ComplaintClassifier:
    def __init__(self):
        self.allowed_categories = [
            "Pothole", "Flooding", "Streetlight", "Waste", "Noise", 
            "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other"
        ]
        self.urgent_keywords = [
            "injury", "child", "school", "hospital", "ambulance", 
            "fire", "hazard", "fell", "collapse"
        ]

    def classify_complaint(self, description):
        """
        Skill: classify_complaint
        Processes a single complaint to determine category, priority, and reason.
        """
        if not isinstance(description, str) or not description.strip():
            return {
                "category": "Other",
                "priority": "Low",
                "reason": "Invalid or missing description.",
                "flag": "NEEDS_REVIEW"
            }

        desc_lower = description.lower()
        
        # 1. Determine Priority (Enforcement Rule 2)
        priority = "Standard"
        found_urgent_word = next((word for word in self.urgent_keywords if word in desc_lower), None)
        if found_urgent_word:
            priority = "Urgent"

        # 2. Determine Category (Enforcement Rule 1)
        # Simplified logic for matching keywords to categories
        category = "Other"
        flag = ""
        
        category_map = {
            "pothole": "Pothole",
            "flood": "Flooding",
            "water": "Flooding",
            "light": "Streetlight",
            "waste": "Waste",
            "garbage": "Waste",
            "noise": "Noise",
            "road": "Road Damage",
            "heritage": "Heritage Damage",
            "heat": "Heat Hazard",
            "drain": "Drain Blockage"
        }

        matches = []
        for key, val in category_map.items():
            if key in desc_lower:
                matches.append(val)
        
        if len(matches) == 1:
            category = matches[0]
        elif len(matches) > 1 or not matches:
            category = "Other"
            flag = "NEEDS_REVIEW"

        # 3. Generate Reason (Enforcement Rule 3)
        # Rule: One sentence, must cite specific words.
        keyword_cite = found_urgent_word if found_urgent_word else (matches[0] if matches else "unclear content")
        reason = f"The complaint is classified as {category} because the description mentions '{keyword_cite}'."

        return {
            "category": category,
            "priority": priority,
            "reason": reason,
            "flag": flag
        }

    def batch_classify(self, input_path, output_path):
        """
        Skill: batch_classify
        Reads CSV, processes all rows, and writes output.
        """
        if not os.path.exists(input_path):
            print(f"Error: Input file {input_path} not found.")
            return

        results = []
        
        try:
            with open(input_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    classification = self.classify_complaint(row.get('description', ''))
                    results.append(classification)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

            with open(output_path, mode='w', encoding='utf-8', newline='') as f:
                fieldnames = ['category', 'priority', 'reason', 'flag']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            print(f"Successfully processed {len(results)} rows to {output_path}")

        except Exception as e:
            print(f"Error handling CSV: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    
    args = parser.parse_args()
    
    classifier = ComplaintClassifier()
    classifier.batch_classify(args.input, args.output)