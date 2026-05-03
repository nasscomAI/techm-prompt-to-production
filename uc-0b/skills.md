skills:

  - name: retrieve_policy
    description: >
      Loads a plain-text policy document from the specified file path and returns
      its content parsed into structured, numbered sections. Each section is
      identified by its clause number and heading so that downstream skills can
      reference clauses by ID. Preserves the original binding language (must,
      will, requires, not permitted) without modification.
    input:
      file_path:
        type: string
        description: >
          Absolute or relative path to the .txt policy file.
          Example: ../data/policy-documents/policy_hr_leave.txt
        required: true
    output:
      type: list
      description: >
        An ordered list of clause objects, each containing:
          - clause_id: the numbered identifier (e.g. "2.3", "5.2")
          - heading: the clause title if present, otherwise null
          - body: the full verbatim text of the clause
          - binding_verb: the primary obligation verb extracted from the clause
            (must | will | requires | not permitted | may)
    error_handling:
      - If the file path does not exist, raise FileNotFoundError with the
        resolved path included in the message; do not proceed.
      - If the file is empty, raise ValueError stating the document contains
        no content; do not return an empty list silently.
      - If the file cannot be parsed into numbered sections, return the raw
        text as a single clause with clause_id "unparsed" and log a warning
        so the caller can decide whether to abort.
      - Do not infer, rewrite, or normalise any clause text during loading.

  - name: summarize_policy
    description: >
      Accepts the structured clause list produced by retrieve_policy and generates
      a compliant, clause-accurate summary. Every input clause must appear in the
      output, referenced by its clause_id. Multi-condition obligations must
      preserve all conditions. Binding verbs must not be softened. No information
      absent from the source clauses may be introduced. If any clause cannot be
      summarised without meaning loss, it is quoted verbatim and flagged with
      [VERBATIM] in the output.
    input:
      clauses:
        type: list
        description: >
          The ordered list of clause objects returned by retrieve_policy.
          Each object must contain clause_id, body, and binding_verb.
        required: true
      output_path:
        type: string
        description: >
          File path where the completed summary will be written.
          Example: uc-0b/summary_hr_leave.txt
        required: true
    output:
      type: string
      description: >
        A structured plain-text summary written to output_path. Format:
          - Each clause is represented as a numbered entry prefixed by its
            clause_id (e.g. "[2.3] ...").
          - Clauses that could not be safely paraphrased are prefixed with
            [VERBATIM] and contain the exact source text.
          - A trailing checklist confirms which of the 10 designated high-risk
            clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2)
            are present in the output.
    error_handling:
      - If the input clause list is empty, raise ValueError and abort; do not
        produce an empty summary file.
      - If any of the 10 designated high-risk clause IDs (2.3, 2.4, 2.5, 2.6,
        2.7, 3.2, 3.4, 5.2, 5.3, 7.2) are missing from the input list, raise
        a MissingClauseError listing the absent clause IDs before writing any
        output.
      - If the output path directory does not exist, raise FileNotFoundError;
        do not create directories silently.
      - If a generated clause summary is detected to contain scope-bleed phrases
        (e.g. "as is standard practice", "typically in government organisations",
        "employees are generally expected to"), raise ScopeBleedError and halt
        before writing the file.
      - If a multi-condition obligation (e.g. clause 5.2 requiring both
        Department Head and HR Director) produces output that references fewer
        approvers than the source, raise ConditionDropError identifying the
        clause and the dropped condition.

