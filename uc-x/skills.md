skills:
  - name: retrieve_documents
    description: Loads all 3 policy files and indexes them by document name and section number.
    input: |
      A list of file paths (strings) pointing to the policy documents. Example:
        retrieve_documents(["../data/policy-documents/policy_hr_leave.txt", ...])
    output: |
      A dict/JSON object indexing content by document name and section number. Example:
        {
          "policy_hr_leave.txt": { "2.6": "...", ... },
          "policy_it_acceptable_use.txt": { "3.1": "...", ... }
        }
    error_handling: |
      - If any file is missing or unreadable, raise FileNotFoundError and halt.
      - Do not attempt to parse unstructured text; only index explicitly numbered sections.

  - name: answer_question
    description: Searches indexed documents and returns a single-source answer with a citation, or the exact refusal template.
    input: |
      A question string and the indexed documents object. Example:
        answer_question(question="Can I carry forward unused annual leave?", docs=...)
    output: |
      A plain-text string containing the answer with its document name and section citation, or the exact refusal template.
    error_handling: |
      - If the answer cannot be found in the text, return exactly: "This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance."
      - If answering the question requires combining information from multiple different documents (e.g., HR and IT policies), treat it as ambiguous and return the refusal template instead of blending claims.
      - Never use hedging phrases or guess intent when information is absent.
