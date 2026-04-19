skills:

- name: classify_complaint
  description: Classifies a single complaint into category, priority, reason, and flag based on strict rules.
  input: 
    - complaint_text (string): Free-text description of the complaint
  output:
    - category (string): One of [Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other]
    - priority (string): One of [Urgent, Standard, Low]
    - reason (string): Exactly one sentence citing specific words from the complaint
    - flag (string): "NEEDS_REVIEW" or empty
  error_handling:
    - If no category keywords match → set category = "Other" and flag = "NEEDS_REVIEW"
    - If multiple category matches → select one and set flag = "NEEDS_REVIEW"
    - If complaint text is empty or invalid → return category = "Other", priority = "Low", reason = "Invalid or empty complaint", flag = "NEEDS_REVIEW"
    - Never generate categories outside the allowed list

- name: batch_classify
  description: Processes a CSV of complaints, applies classify_complaint to each row, and writes results to an output CSV.
  input:
    - input_file (string): Path to input CSV file containing complaint text
  output:
    - output_file (string): CSV file with added columns [category, priority, reason, flag]
  error_handling:
    - If input file is missing or unreadable → raise an error and stop execution
    - If a row has invalid or missing complaint text → process with classify_complaint default handling
    - Ensure output file is always written even if some rows are flagged