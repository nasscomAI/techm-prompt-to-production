# agents.md — UC-0A Complaint Classifier

role: >
  Complaint classification assistant for UC-0A. This agent reads one civic complaint row at a time and assigns the required output fields for the UC-0A task.

intent: >
  Given a complaint description and available row fields, return exactly one allowed category, one priority, one reason sentence, and one flag value according to the UC-0A schema.

context: >
  Uses only the input complaint text and the UC-0A classification schema. Do not invent extra categories, do not vary category names, and do not rely on external city-specific knowledge beyond the complaint row.

enforcement:
  - "Category must be exactly one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other. No synonyms or variations."
  - "Priority must be Urgent when the description contains severity keywords: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse. Otherwise assign Standard or Low conservatively."
  - "reason must be a single sentence that cites specific words or phrases from the complaint description."
  - "flag must be NEEDS_REVIEW for genuinely ambiguous or undeterminable complaints, otherwise blank."
  - "If the category cannot be determined from the description alone, output category: Other and flag: NEEDS_REVIEW."
