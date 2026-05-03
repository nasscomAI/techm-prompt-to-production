# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retreive_policy
    description: retreive_policy reads the input policy document and returns it as a structured numbered section
    input: reads input .txt file
    output: structured numbered sections of the policy document
    error_handling: When the input .txt file is not found or the file is empty, it will raise an error.

  - name: summarize_policy
    description: summarize_policy takes the structured numbered sections from retreive_policy skill and produces a compliant summary with clause references
    input: structured numbered sections of the policy document
    output: compliant summary with clause references
    error_handling: When the structured numbered sections is not found or the section is empty, it will raise an error.
