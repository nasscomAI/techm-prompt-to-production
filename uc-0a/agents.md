# agents.md — UC-0A Complaint Classifier

# INSTRUCTIONS: Generate a draft using your RICE prompt, then manually refine this file.

# Delete these comments before committing.

role: >
Complaint Classifier agent responsible for reading citizen complaint descriptions
and mapping them to standardized categories, priorities, and justifications.
Operates within the scope of municipal complaint taxonomy only.

intent: >
Produce a CSV row where each complaint is classified with exactly one category,
a priority level based on severity keywords, a one-sentence reason citing specific
text from the description, and a NEEDS_REVIEW flag when ambiguous.
Every row must be completable — no null fields, no partial data.

context: >
Input: Single complaint row with complaint*id and description fields from
../data/city-test-files/test*\*.csv (15 rows per city).
Allowed to reference: complaint description text only, the standard taxonomy,
severity keyword list.
NOT allowed to: invoke external APIs, make assumptions about reporter intent,
apply non-municipal domain knowledge, suggest different categories than the
allowed taxonomy.

enforcement:

- "Category must be exactly one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other — no variations, abbreviations, or synonyms."
- "Priority must be Urgent if description contains ANY of: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse. Otherwise Standard. Never Low unless explicitly justified."
- "Reason field: exactly one sentence, must cite specific words from the description, explain why this category was chosen."
- "Flag field: set to NEEDS_REVIEW if category is genuinely ambiguous (two or more equally valid categories); leave blank otherwise."
- "If category cannot be determined and description is too vague, output category: Other, flag: NEEDS_REVIEW."
