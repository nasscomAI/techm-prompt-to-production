# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_policy
    description: Loads policy text file and extracts numbered clauses into structured sections.
    input: Text file path (.txt)
    output: Structured numbered policy sections
    error_handling: Return error if file is missing or malformed

  - name: summarize_policy
    description: Produces compliant summary preserving all clauses, conditions, and references.
    input: Structured numbered policy sections
    output: Summary text with clause references
    error_handling: Quote clause verbatim and flag it if summarization risks meaning loss