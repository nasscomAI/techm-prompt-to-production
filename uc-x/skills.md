# skills.md

skills:
  - name: retrieve_documents
    description: Loads all three policy files and indexes their content by document name and section number.
    input: None — file paths are fixed (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
    output: An indexed structure mapping each document name and section number to its text content.
    error_handling: If a file is missing or unreadable, raise an error naming the missing file — do not proceed with partial documents.

  - name: answer_question
    description: Searches the indexed documents for a single-source answer to the user's question and returns it with a citation, or returns the refusal template if no answer is found.
    input: A natural-language question string and the indexed document structure from retrieve_documents.
    output: A plain-text answer citing exactly one source (document name + section number), OR the verbatim refusal template if the question is not covered.
    error_handling: If the question matches content in more than one document and combining them would be required to answer, return the refusal template rather than blending sources.
