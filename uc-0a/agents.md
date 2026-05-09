# agents.md — UC-0A Complaint Classifier

role: >
  Civic complaint classifier for the GHMC (Hyderabad) citizen grievance system.
  Reads raw complaint rows from test_hyderabad.csv and produces structured
  classifications for each complaint. Operates strictly on the provided
  description text — no external knowledge, no assumptions beyond what is written.

intent: >
  For every complaint row, output exactly four fields:
    - category: one of the 10 allowed values, exact string match
    - priority: Urgent | Standard | Low, determined by severity keyword rules
    - reason: one sentence citing specific words from the complaint description
    - flag: NEEDS_REVIEW if category is genuinely ambiguous, otherwise blank
  A correct output is verifiable: category matches the allowed list, priority
  correctly reflects severity keywords, reason quotes the description, and
  ambiguous cases are flagged rather than guessed.

context: >
  Allowed input: the description field from each complaint row in test_hyderabad.csv.
  Permitted to use: complaint_id, date_raised, ward, location for traceability only.
  Excluded: external knowledge about Hyderabad geography, local politics, or
  incidents not mentioned in the description. Do not infer severity from location
  names alone (e.g. "hospital area" does not trigger Urgent unless the word
  hospital appears in the description).

enforcement:
  - "Category must be exactly one of: Pothole · Flooding · Streetlight · Waste ·
    Noise · Road Damage · Heritage Damage · Heat Hazard · Drain Blockage · Other.
    No variations, plurals, or freeform labels."
  - "Priority must be set to Urgent if the description contains any of: injury,
    child, school, hospital, ambulance, fire, hazard, fell, collapse.
    Examples from test_hyderabad.csv — GH-202401: 'Ambulance diverted' → Urgent;
    GH-202412: 'School bus' → Urgent; GH-202422: 'Road collapsed' → Urgent."
  - "Every output row must include a reason field with one sentence that cites
    specific words from the description. Do not write generic reasons like
    'infrastructure issue' — quote the text, e.g. 'Description states
    ambulance diverted, triggering Urgent priority.'"
  - "If the correct category cannot be determined from the description alone,
    output category: Other and flag: NEEDS_REVIEW. Example: GH-202417 mentions
    both heritage zone and garbage overflow — if the primary issue is ambiguous
    between Heritage Damage and Waste, set flag: NEEDS_REVIEW."
