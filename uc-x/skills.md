# skills.md

skills:
  - name: retrieve_documents
    description: Loads all policy text files and parses them into structured sections indexed by document name and section number.
    input: None (uses predefined paths to policy_hr_leave.txt, policy_it_acceptable_use.txt, and policy_finance_reimbursement.txt).
    output: A collection of structured documents with searchable sections.
    error_handling: Reports an error if any policy file is missing or unreadable.

  - name: answer_question
    description: Searches the indexed policy documents for information relevant to a user's question and returns a single-source answer with citations or a refusal template.
    input: A user's question (string).
    output: A string containing the answer with citation (Doc Name + Section) OR the verbatim refusal template.
    error_handling: Strictly refuses to combine information from multiple documents or use hedging language.
