skills:
  - name: retrieve_documents
    description: Loads all 3 policy text files and parses them into an indexed dictionary searchable by document name and section number.
    input: File paths to policy_hr_leave.txt, policy_it_acceptable_use.txt, and policy_finance_reimbursement.txt
    output: A structured, indexed collection mapping section numbers to their exact texts for each document.
    error_handling: Halts execution if a document is missing or unreadable.

  - name: answer_question
    description: Searches indexed documents to match a user query, returning a single-source answer with a citation or a refusal.
    input: A user question (string) and the indexed documents object.
    output: A precise answer string appended with an exact citation (document name + section), OR the exact refusal template.
    error_handling: Immediately returns the verbatim refusal template if the answer is not found or requires blending policies across documents.
