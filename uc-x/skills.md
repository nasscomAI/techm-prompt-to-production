# skills.md

skills:
  - name: retrieve_documents
    description: Load all three policy documents, parse by section number, and index for single-source retrieval.
    input: |
      Parameters:
      - document_paths: list of paths to policy files (default: ["../data/policy-documents/policy_hr_leave.txt", "../data/policy-documents/policy_it_acceptable_use.txt", "../data/policy-documents/policy_finance_reimbursement.txt"])
      Returns: indexed document structure with:
      - loaded_documents: list of successfully loaded files
      - document_index: sections indexed by document name and section number
    output: |
      Document index object (dict/JSON) with:
      - status: "SUCCESS" or "FAILED"
      - timestamp: ISO datetime of load
      - documents: dict with keys = document names (policy_hr_leave, policy_it_acceptable_use, policy_finance_reimbursement)
      - document_content: dict with structure:
        - [document_name]:
          - full_text: complete document text
          - sections: dict indexed by section number (e.g., "2.3", "5.2")
            - [section_num]: object containing:
              - section_text: verbatim text of the section
              - section_title: title/heading if present
              - conditions: list of all conditions/requirements in the section
              - binding_statements: exact phrases with shall, must, may, cannot, prohibited, required
      - searchable_index: text search index mapping keywords to (document, section) tuples
      - total_sections_parsed: count of sections across all documents
      - parse_errors: list of any parsing issues encountered
    error_handling: |
      If any document file not found: log error, load remaining documents, continue (do not halt).
      If file is empty or unreadable: mark as failed, include in parse_errors, continue with other documents.
      If section number format not found (missing numbered sections like 2.3): log warning that document may not follow standard numbering; parse by heading instead.
      If a section contains multiple conditions joined by AND: extract and store as separate items in conditions list with AND relationship marked.
      If load completes with fewer than 3 documents: set status="SUCCESS" with warning; note which documents loaded successfully.
      After load: report total documents loaded, total sections parsed, any parse errors or fallback parsing strategies used.

  - name: answer_question
    description: Search indexed documents for single-source answer to an employee policy question, return citation + answer or exact refusal template.
    input: |
      Parameters:
      - question: employee question (string, natural language)
      - document_index: indexed documents (output of retrieve_documents)
      - refusal_template: required exact refusal wording to use for out-of-scope questions (default: "This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance.")
      Returns: answer object with:
      - question: echoed from input
      - answer: single-source answer with citation OR refusal template
      - source_document: name of source document if answer found
      - source_section: section number if answer found
    output: |
      Answer object (dict/JSON) with:
      - question: string (echoed)
      - answer_type: "FOUND" (single-source answer) or "REFUSED" (out-of-scope or cross-document risk)
      - answer: string containing either:
        (a) Single-source answer with format: "[Answer] (Source: [Document Name], Section [X.Y])" — every factual claim cited
        (b) Exact refusal template if out-of-scope or cross-document risk detected
      - source_document: document name (null if REFUSED)
      - source_section: section number (null if REFUSED)
      - source_text: verbatim quoted text from source section (if single-source answer found)
      - confidence: "HIGH" (clear single source), "MEDIUM" (answer found but multiple sections involved), or "LOW" / "REFUSED" (no clear single source or cross-document risk)
      - flags: list of flags raised (e.g., "#FLAG: Cross-document blending detected — refusing", "#FLAG: Hedging language detected in answer — refusing", "#FLAG: Condition drop risk detected")
    error_handling: |
      If question is not found in any document section: set answer_type="REFUSED", answer=refusal_template, confidence="REFUSED".
      If question could be answered by combining facts from two different documents (cross-document blending): set answer_type="REFUSED", answer=refusal_template, flags="#FLAG: Cross-document blending detected — refusing to synthesize across documents".
      If answer requires citing a multi-part AND condition (e.g., "requires approval from Department Head AND HR Director"): include ALL conditions in answer; if only partial conditions would fit answer format, refuse with flag "#FLAG: Condition drop risk — cannot answer without losing critical condition".
      If answer source contains a clause that contradicts or conflicts with another document: refuse with refusal_template and flag "#FLAG: Potential conflict across documents — refusing for safety".
      If answer is found but begins with hedging phrases ("while not explicitly", "typically", "generally", "common practice"): reject the answer, set answer_type="REFUSED", flag "#FLAG: Hedging language detected — answer rejected as speculative".
      If keyword search returns multiple possible answers from same document(s) at different sections: check if both are single-source or if they represent different sub-questions; if ambiguous, prefer the section with highest text overlap to question.
      If no search results but question is asked again: rephrase question keywords and retry search; if still no results, use refusal template.
      After answer generation: validate that answer does NOT contain hedging language, does NOT blend documents, does preserve conditions — if validation fails, replace with refusal_template.
