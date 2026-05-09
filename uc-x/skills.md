# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: `retrieve_documents`
    description: Load and index the three policy files into a structured store keyed by (filename, section id).
    input:
      - List of file paths (expected exactly):
        - `data/policy-documents/policy_hr_leave.txt`
        - `data/policy-documents/policy_it_acceptable_use.txt`
        - `data/policy-documents/policy_finance_reimbursement.txt`
    output:
      - Indexed document store (list/map of entries as above).
    error_handling: If a file is missing or unreadable, raise an explicit error listing missing paths.

  - name: `answer_question`
    description: Deterministically locate a single-source answer or return the exact refusal template.
    input:
      - `question` (string)
      - `indexed_document_store` (output from `retrieve_documents`)
    output:
      - Either:
        - Factual answer string ending with `(Source: <filename>, section <X.Y>)`, or
        - The refusal template verbatim.
    error_handling:
      - If the indexed store is unavailable or corrupted → return refusal template (do not attempt to answer).
      - Do not return partial answers or combine sections from different documents.
