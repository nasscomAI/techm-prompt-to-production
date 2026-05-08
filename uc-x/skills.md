# skills.md

skills:
  - name: retrieve_documents
    description: Loads all three policy files and builds an index keyed by document name and section number, ready for lookup.
    input: List of file paths (strings) — policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt.
    output: Indexed document store — a map of {document_name → {section_number → section_text}} for all parsed sections.
    error_handling: >
      Raises an error if any file is missing or unreadable.
      If a file contains no parseable sections, reports the document name and
      refuses to proceed silently — does not index an empty document.
      Does not merge or cross-link content between documents at index time.

  - name: answer_question
    description: Searches the indexed documents for a single-source answer to the user's question and returns the answer with a citation, or the refusal template if no single document covers it.
    input: >
      User question (string); indexed document store (from retrieve_documents).
    output: >
      One of two responses:
      (1) Answer object — {answer: string, source_document: string, section: string}
          where answer contains only claims from that one section.
      (2) Refusal string — the exact refusal template with no modifications:
          "This question is not covered in the available policy documents
          (policy_hr_leave.txt, policy_it_acceptable_use.txt,
          policy_finance_reimbursement.txt). Please contact [relevant team]
          for guidance."
    error_handling: >
      If the question matches content in more than one document and combining
      them would produce a claim not present in either alone, returns the
      refusal template — never blends.
      If the question is ambiguous but answerable from a single section,
      answers from that section and notes the scope of the citation.
      Never returns a partial answer with hedging language as a fallback.
