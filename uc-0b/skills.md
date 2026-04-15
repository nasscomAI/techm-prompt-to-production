# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_policy
    description: Load a .txt policy file and return its content as a structured list of numbered sections.
    input: Absolute path to the policy text file.
    output: List of dictionaries, each with 'clause_id' and 'text'.
    error_handling: Return an empty list if the file is not found or is unreadable.

  - name: summarize_policy
    description: Process structured policy sections into a summary that preserves all core obligations and binding verbs.
    input: List of structured policy sections.
    output: String representing the finalized summary.
    error_handling: For any clause that cannot be safely summarized, include the verbatim text with a warning tag.
