# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: classify_complaint
    description: Classify the complaint with a category and priority flag.
    input: one complaint row in CSV format
    output: category + priority + reason + flag output
    error_handling: When the input is invalid or ambiguous, it will flag the category as Other and priority as NEEDS_REVIEW or blank. Set when category is genuinely ambiguous. Do not use this if you just couldn't be bothered to figure out the category.

  - name: batch_classify
    description: reads input CSV file, classifies each complaint using classify_complaint skill, and saves the results to an output CSV file
    input: reads input CSV 
    output: output CSV file
    error_handling: When the input CSV file is not found or the file is empty, it will raise an error. When the output CSV file cannot be created, it will raise an error.
