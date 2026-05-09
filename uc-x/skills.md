# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_documents
    description: Loads all policy files and indexes them by document name and section number.
    input: List of policy text files
    output: Indexed policy documents
    error_handling: Return error if any file is missing or unreadable

  - name: answer_question
    description: Searches indexed documents and returns a single-source answer with citation or exact refusal template.
    input: User question + indexed documents
    output: Answer with citation or refusal template
    error_handling: Refuse if answer requires cross-document blending or is not found
