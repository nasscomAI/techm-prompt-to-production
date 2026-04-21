# skills.md

skills:
  - name: retrieve_documents
    description: Loads all 3 policy files (HR, IT, Finance) and indexes their contents by document name and section number.
    input: The directory path containing the .txt policy documents.
    output: A structured index mapping document titles and section numbers to their verbatim text rules.
    error_handling: Refuses to process if any of the three core documents are unreadable or missing.

  - name: answer_question
    description: Searches the indexed documents and returns a single-source answer with explicit section citations for each component of the user's query, or the exact refusal template.
    input: A user question (string) and the indexed policy data.
    output: A strictly formatted response containing one or more explicit citations (e.g., "According to [Document] (section [X.X]): [Rule]"), or the exact refusal template.
    error_handling: If the query cannot be matched with high confidence to explicit rules, or if answering would require synthesizing unstated rules, it falls back immediately to the exact refusal template.
