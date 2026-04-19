skills:
  - name: retrieve_documents
    description: Loads all 3 policy files and indexes them by document name and section number.
    input: List of file paths pointing to the policy documents.
    output: An indexed data structure containing the text of each document, keyed by document name and section number.
    error_handling: If a file path is invalid or missing, raise a FileNotFoundError and halt execution.

  - name: answer_question
    description: Searches indexed documents to find an answer, returning either a single-source answer with a citation or the exact refusal template.
    input: The user's query string and the indexed document structure from `retrieve_documents`.
    output: A response string formatted as either a direct answer with "[Document Name] - Section [Number]" citation, or the exact refusal template.
    error_handling: If the query requires combining multiple documents to answer or if the answer is absent, return the exact refusal template: "This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance."
