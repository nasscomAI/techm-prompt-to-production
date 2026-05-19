# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as a list of structured numbered sections.
    input: file_path (String) - Path to the policy text file.
    output: sections (List of Objects) - List containing clause numbers and their corresponding text.
    error_handling: Returns an error if the file is not found or is not a .txt file.
 
  - name: summarize_policy
    description: Processes structured policy sections to produce a summary that complies with enforcement rules and includes clause references.
    input: sections (List of Objects) - Structured policy sections.
    output: summary (String) - A compliant summary text.
    error_handling: Returns an error if sections are missing required binding verbs or if obligations are ambiguous.
