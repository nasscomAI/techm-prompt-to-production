# skills.md

skills:
  - name: retrieve_documents
    description: Loads all 3 policy files and indexes them by document name and section number for efficient searching.
    input: File paths to the three policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
    output: Indexed data structure containing document content organized by document name and section numbers.
    error_handling: If a file is missing or unreadable, raise an error and stop processing.

  - name: answer_question
    description: Searches the indexed documents for relevant information and returns a single-source answer with citation or the refusal template.
    input: A question string and the indexed documents.
    output: Either an answer with document name and section citation, or the exact refusal template if not covered.
    error_handling: If no relevant information is found, use the refusal template; if multiple documents match, refuse to avoid blending.
