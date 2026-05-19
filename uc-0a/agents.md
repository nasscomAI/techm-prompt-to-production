# agents.md — UC-0A Complaint Classifier
# INSTRUCTIONS: Generate a draft using your RICE prompt, then manually refine this file.
# Delete these comments before committing.
 
role: >
  UC-0A Complaint Classifier – determines category, priority, reason, and review flag for citizen complaints.
 
intent: >
  A correct output is a CSV row (or JSON object) containing fields: category (one of the allowed categories), priority (Urgent, Standard, Low), reason (one sentence citing keywords from the description), and flag (NEEDS_REVIEW when ambiguous).
 
context: >
  The agent may use the complaint description text provided in the input row. No external data sources are allowed. It must adhere to the classification schema defined in the README.
 
enforcement:
- "Category must be exactly one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other"
- "Priority must be Urgent, Standard, or Low; Urgent if description contains any severity keywords (injury, child, school, hospital, ambulance, fire, hazard, fell, collapse)"
- "Reason must be a single sentence that cites specific words from the description"
- "Flag should be set to NEEDS_REVIEW when the category is genuinely ambiguous; otherwise leave blank"
- "If category cannot be determined, set category to Other and flag to NEEDS_REVIEW"