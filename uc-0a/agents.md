role: >
  Civic complaint classifier for the City Municipal Corporation.
  Input: a CSV row describing a citizen complaint (complaint_id, description, etc.).
  Output: category, priority, reason, and flag fields for that row.

intent: >
  Every complaint must be classified into exactly one of the 10 allowed categories
  (Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage,
  Heat Hazard, Drain Blockage, Other). Priority must be Urgent if severity keywords
  are present, otherwise Standard. A one-sentence reason must cite specific words
  from the description. The flag field must be NEEDS_REVIEW only when the category
  is genuinely ambiguous, otherwise blank.

context: >
  The classifier may use only the complaint description text and the keyword rules
  defined in enforcement. It must not use external knowledge, the city name, the
  ward, the reported_by channel, or the days_open field. It must not invent
  categories outside the allowed list. It must not use LLM or API calls — this is
  a pure keyword-based classifier.

enforcement:
  - "Category must be exactly one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other. No variations, no sub-categories."
  - "Priority must be Urgent if the description contains any of these severity keywords: injury, child, school, hospital, ambulance, fire, hazard, fell, collapse. Otherwise Standard."
  - "Every output row must include a reason field that cites the specific keyword(s) from the description that triggered the classification."
  - "If the description matches keywords for two or more categories, apply disambiguation rules and set flag to NEEDS_REVIEW. If no keywords match at all, set category to Other with blank flag."
  - "Never set flag to values other than NEEDS_REVIEW or blank. Never set PROCESSING_ERROR or any custom flag value."
  - "The classifier must process all rows without crashing. Bad rows must produce a row in the output with category Other, flag NEEDS_REVIEW, and a reason describing the error."
