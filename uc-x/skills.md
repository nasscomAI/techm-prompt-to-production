# skills.md
skills:

  - name: retrieve_documents
    description: Loads all three policy .txt files from disk and returns a unified
      index keyed by document name and section number, with each section's verbatim
      body text preserved for single-source retrieval.
    input:
      type: object
      format:
        fields:
          - name: file_paths
            type: list
            required: true
            notes: Ordered list of exactly three absolute or relative paths —
              ../data/policy-documents/policy_hr_leave.txt,
              ../data/policy-documents/policy_it_acceptable_use.txt,
              ../data/policy-documents/policy_finance_reimbursement.txt.
              All three must be present and readable.
    output:
      type: object
      format:
        fields:
          - name: index
            type: dict
            notes: >
              Nested dict structured as
              { document_name: { section_number: { heading: str|null, body: str } } }.
              document_name is the bare filename (e.g. "policy_hr_leave.txt").
              section_number is a string (e.g. "2.6", "3.1").
              body is the full verbatim text of that section as it appears in
              the source file — no paraphrasing, no truncation.
          - name: load_errors
            type: list
            notes: List of error objects { file_path, reason } for any file that
              could not be loaded. Empty list when all files loaded successfully.
              Presence of any entry here must halt answer_question and surface
              the error to the caller before any question is processed.
    error_handling:
      - trigger: one or more file paths do not exist or cannot be read
        action: Add the failed path and reason to load_errors. If any file fails
          to load, halt immediately and raise a file-not-found error listing all
          failed paths. Do not return a partial index — all three documents must
          be loaded before the index is usable.
      - trigger: a file is empty or contains no parseable numbered sections
        action: Add the file to load_errors with reason "no numbered sections
          found". Halt and raise a parse error. Do not silently return an index
          missing one document.
      - trigger: clause numbering is non-standard or inconsistent within a file
        action: Log a warning identifying the anomalous lines and their file,
          include them as unnumbered entries with section_number set to null,
          and continue parsing the remaining sections in that file.
      - trigger: fewer or more than three file paths are provided
        action: Raise a configuration error stating the exact count received and
          the three required paths. Do not attempt partial loading.

  - name: answer_question
    description: Accepts a natural-language question and the document index produced
      by retrieve_documents, searches for a single-source answer with a section
      citation, and returns either that answer or the exact refusal template when
      no single-source answer exists.
    input:
      type: object
      format:
        fields:
          - name: question
            type: string
            required: true
            notes: Free-text employee question. Must be non-empty. No preprocessing
              or rephrasing is applied — the question is matched against the index
              as submitted.
          - name: index
            type: dict
            required: true
            notes: The index object returned by retrieve_documents. Must contain
              all three documents. If any document is missing from the index this
              skill must refuse all questions and surface a load error.
    output:
      type: object
      format:
        fields:
          - name: answer
            type: string
            notes: >
              Either a factual answer string or the verbatim refusal template.
              Factual answers must end with an inline citation in the format
              [source: <document_name>, section <section_number>].
              The refusal template when used must be exactly —
              "This question is not covered in the available policy documents
              (policy_hr_leave.txt, policy_it_acceptable_use.txt,
              policy_finance_reimbursement.txt). Please contact [relevant team]
              for guidance." — with no additions, omissions, or rephrasing.
          - name: source_document
            type: string
            notes: Bare filename of the single document the answer was drawn from
              (e.g. "policy_it_acceptable_use.txt"). Null when the refusal
              template is returned.
          - name: source_section
            type: string
            notes: Section number within source_document (e.g. "3.1"). Null when
              the refusal template is returned.
          - name: is_refusal
            type: boolean
            notes: True when the refusal template was returned, false when a
              factual answer was produced.
    error_handling:
      - trigger: question is empty or whitespace only
        action: Return is_refusal true with the verbatim refusal template. Do
          not attempt to search the index with an empty query.
      - trigger: relevant sections are found in more than one document and
          combining them would be required to produce a complete answer
          (cross-document blending risk)
        action: Return is_refusal true with the verbatim refusal template. Never
          combine claims from two documents into a single answer regardless of
          how closely related the sections appear. This includes the case where
          IT policy section 3.1 and HR policy both contain terms related to
          remote work or personal devices — the answer must come from one
          document only or be refused.
      - trigger: the best matching section exists but answering it faithfully
          would require dropping a condition (e.g. omitting one of two required
          approvers, omitting a forfeiture date, omitting a monetary limit)
        action: Include all conditions from the source section in the answer.
          If all conditions cannot be preserved in a single coherent answer
          sentence, quote the section body verbatim rather than paraphrase.
          Never drop a condition silently.
      - trigger: no section in any document matches the question with sufficient
          confidence
        action: Return is_refusal true with the verbatim refusal template. Do
          not produce a hedged or speculative answer. Do not use phrases such as
          "while not explicitly covered", "typically", "generally understood",
          or "it is common practice".
      - trigger: a hedging phrase is detected in a candidate answer before output
          ("while not explicitly covered", "typically", "generally understood",
          "it is common practice", "usually", "in most organisations",
          "it can be assumed")
        action: Discard the candidate answer entirely. Return is_refusal true
          with the verbatim refusal template. Hedging phrases are never permitted
          in output under any condition.
      - trigger: a binding verb in the source section — must, requires, not
          permitted, prohibited, will — would be replaced by a weaker equivalent
          in the produced answer
        action: Retain the original binding verb exactly as it appears in the
          source section. If retention is not possible without meaning loss,
          quote the section body verbatim rather than paraphrase.
      - trigger: index is missing one or more of the three required documents
        action: Halt immediately and raise a configuration error listing the
          missing documents. Do not attempt to answer any question from an
          incomplete index.
