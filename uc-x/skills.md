# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_documents
    description: Load the three policy text files and index them by document name and section number.
    input: List of file paths.
    output: A collection of structured sections with metadata.
    error_handling: Report if any document could not be loaded.

  - name: answer_question
    description: Search the indexed documents to find the most relevant single-source answer.
    input: User question and the structured index.
    output: A string containing the answer with citation, or the strict refusal template.
    error_handling: Return the refusal template if no clear single-source evidence is found or if the answer would require blending multiple sources.
