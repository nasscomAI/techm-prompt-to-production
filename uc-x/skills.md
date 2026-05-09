skills:
  - name: retrieve_documents
    description: Loads all three policy files and indexes them by document name and section number for searchability.
    input: A list of three file paths pointing to policy_hr_leave.txt, policy_it_acceptable_use.txt, and policy_finance_reimbursement.txt.
    output: A dictionary indexed by document name and section number, containing the structured policy content ready for searching.
    error_handling: If any file is not found or unreadable, return an error message and halt; if section numbers cannot be extracted, flag the issue and skip that section.

  - name: answer_question
    description: Searches indexed policy documents and returns a single-source answer with citation or uses the refusal template if not covered.
    input: A question string and the indexed policy documents dictionary from retrieve_documents.
    output: An answer string that either cites a specific document name and section number with the factual response, or returns the exact refusal template.
    error_handling: If the question matches content from multiple documents, return a refusal or single-source answer only; never blend claims; if question is not covered, return the refusal template exactly without hedging; to prevent condition dropping, include all conditions from the source document.
