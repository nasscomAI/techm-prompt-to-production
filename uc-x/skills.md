# skills.md

# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.

# Delete these comments before committing.

skills:

\- name: answer\_question

&#x20;   description: Searches the indexed policy documents to find a single-source answer to a user's question, providing citations.

&#x20;   input: A user's question (string).

&#x20;   output: A string containing the answer with document and section citation, or the refusal template if no answer is found.

&#x20;   error\_handling: If no single document provides a clear answer, or if information is ambiguous, it must return the exact refusal template.



\- name: retrieve\_documents

&#x20;   description: Loads the HR, IT, and Finance policy documents and indexes them by document name and section number for easy retrieval.

&#x20;   input: None.

&#x20;   output: A collection of document sections with metadata (document name, section number, content).

&#x20;   error\_handling: If a document is missing, it should log an error and proceed with available documents if possible.

