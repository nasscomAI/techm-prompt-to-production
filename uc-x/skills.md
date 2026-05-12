skills:
  - name: retrieve_documents
    description: >
      Loads all three policy text files from disk, parses each into numbered
      sections, and returns a searchable index keyed by document name and
      section number with the verbatim body text of every section preserved.
    input:
      type: list
      format: >
        List of file paths (strings) pointing to the three policy documents:
          - ../data/policy-documents/policy_hr_leave.txt
          - ../data/policy-documents/policy_it_acceptable_use.txt
          - ../data/policy-documents/policy_finance_reimbursement.txt
    output:
      type: object
      format: >
        An object (document index) containing:
          - documents: a dict keyed by document filename (e.g.
            "policy_hr_leave.txt"), each value being an ordered list of
            section objects containing:
              - section_id: string (e.g. "2.6", "3.1")
              - heading: string (section heading if present, else null)
              - body: string (verbatim section text as it appears in the file)
          - document_names: list of the three document filenames loaded
          - section_count: total number of sections across all documents
    error_handling:
      file_not_found: >
        If any of the three policy files does not exist at its expected path,
        raise a FileNotFoundError naming the missing file. Do not proceed with
        a partial document set — all three must be present.
      unreadable_or_empty: >
        If any file exists but is empty or cannot be decoded as UTF-8, raise
        an IOError stating which file is unreadable. Do not index a partial or
        corrupt document.
      no_sections_detected: >
        If any file contains no recognisable numbered sections (pattern
        N.N), raise a StructureError naming the file and stating that it may
        not be a structured policy document. Do not pass unstructured text to
        answer_question.
      duplicate_section_ids: >
        If a document contains duplicate section numbers, emit a warning but
        keep both entries in order. The answer_question skill should use the
        first occurrence if ambiguity arises.

  - name: answer_question
    description: >
      Searches the indexed documents for sections relevant to the user's
      question, returns a single-source answer citing document name and
      section number, or returns the exact refusal template if the question
      is not covered in any document.
    input:
      type: object
      format: >
        An object containing:
          - question: string — the user's natural-language policy question
          - document_index: the full document index object returned by
            retrieve_documents
    output:
      type: object
      format: >
        An object containing:
          - answer: string — the response text, either a factual answer with
            inline citation(s) in the format "[document_name, Section N.N]",
            or the exact refusal template
          - source_document: string — the single document filename the answer
            is drawn from, or null if refusal
          - source_sections: list of section_id strings cited in the answer,
            or empty list if refusal
          - is_refusal: boolean — true if the refusal template was used
    error_handling:
      question_not_covered: >
        If no section in any of the three documents contains information
        relevant to the question, return the exact refusal template:
        "This question is not covered in the available policy documents
        (policy_hr_leave.txt, policy_it_acceptable_use.txt,
        policy_finance_reimbursement.txt). Please contact [relevant team] for
        guidance." Set is_refusal to true. Do not hedge, speculate, or offer
        partial answers.
      cross_document_blend_detected: >
        If relevant sections are found in two or more documents and answering
        the question requires combining claims from both, do NOT blend them.
        Either answer from the single most directly relevant document only, or
        if genuine ambiguity exists between the documents, return the refusal
        template. Never merge claims from policy_hr_leave.txt and
        policy_it_acceptable_use.txt (or any other pair) into one answer.
      hedging_phrase_detected: >
        Before returning any answer, scan the draft for the banned phrases:
        "while not explicitly covered", "typically", "generally understood",
        "it is common practice", "generally expected to", "as is standard
        practice". If any banned phrase is found, discard the draft and
        regenerate or return the refusal template. A hedged answer is never
        acceptable.
      missing_citation: >
        Before returning any non-refusal answer, verify that every factual
        claim includes a citation in the format "[document_name, Section N.N]".
        If any claim lacks a citation, add it from the source section. An
        uncited factual claim is a critical failure.
      condition_drop_detected: >
        For multi-condition obligations (e.g. HR section 5.2 requiring both
        Department Head AND HR Director), verify that ALL conditions are named
        in the answer. If any condition is missing, add it before returning.
        Dropping a condition is a meaning-loss failure.
      empty_question: >
        If the question string is empty or whitespace-only, return a prompt
        asking the user to enter a question. Do not attempt to search or
        answer.
      ambiguous_question: >
        If the question is too vague to map to a specific section but the
        topic exists in a document, ask the user to be more specific rather
        than guessing which section to cite. Never fabricate specificity.
