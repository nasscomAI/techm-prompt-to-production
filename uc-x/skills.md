# skills.md — UC-X Ask My Documents

skills:
  - name: retrieve_documents
    description: Load the three policy text files and prepare their content with source document filenames.
    input: None (hardcoded paths to policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
    output: String combining the contents of all three documents clearly delineated by filename.
    error_handling: Return an error if any file fails to load.

  - name: answer_question
    description: Pass the loaded document context and the user's question to the LLM configured with strict RICE rules to produce an exact, non-blended, cited answer.
    input: String context (documents), String user_question.
    output: String response from the LLM.
    error_handling: Return the strict refusal template if the LLM fails or the question is unanswerable.
