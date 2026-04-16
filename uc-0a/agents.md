# agents.md — UC-0A Complaint Classifier

role: >
  Classifies citizen complaints into categories and priority levels for municipal complaint resolution.
  Operational boundary: Only classify complaints based on description text, no external knowledge.

intent: >
  Correct output: Each row has category (exact string from allowed list), priority (Urgent/Standard/Low),
  reason (one sentence citing specific words from description), flag (NEEDS_REVIEW or blank).
  All category values must be exactly one of: Pothole, Flooding, Streetlight, Waste, Noise,
  Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other.

context: >
  Input: CSV with description column (category and priority_flag stripped).
  Allowed categories: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage,
  Heat Hazard, Drain Blockage, Other.
  Priority rules: Urgent if description contains injury, child, school, hospital, ambulance,
  fire, hazard, fell, or collapse. Otherwise Standard. Low not used in this dataset.
  Reason: Must cite specific words from the complaint description.

enforcement:
  - "Category must be exactly one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other — no variations or synonyms"
  - "Priority must be Urgent if description contains any of: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse — otherwise Standard"
  - "Every output row must include a reason field with one sentence citing specific words from the description"
  - "If category cannot be confidently determined from description alone, set category to Other and flag to NEEDS_REVIEW"