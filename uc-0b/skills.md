# skills.md
skills:

  - name: retrieve_policy
    description: Loads a .txt policy file from disk and returns its content parsed
      into structured numbered sections keyed by clause number.
    input:
      type: file
      format:
        mime_type: text/plain
        path: ../data/policy-documents/policy_hr_leave.txt
        notes: Must be a plain-text policy document containing numbered clauses.
          The file must be readable and non-empty.
    output:
      type: object
      format:
        fields:
          - name: sections
            type: list
            notes: Ordered list of clause objects. Each object contains clause_number
              (string, e.g. "2.3"), heading (string or null), and body (string —
              the full verbatim text of that clause as it appears in the source file).
          - name: raw_text
            type: string
            notes: Full verbatim content of the source file, preserved for
              fallback verbatim quoting by summarize_policy.
    error_handling:
      - trigger: file path does not exist or cannot be read
        action: Halt immediately and raise a file-not-found error with the
          attempted path. Do not return partial output.
      - trigger: file is empty or contains no parseable numbered sections
        action: Raise a parse error stating the file yielded no clause sections.
          Do not return an empty sections list silently.
      - trigger: clause numbering is non-standard or inconsistent
        action: Log a warning identifying the anomalous lines, include them as
          unnumbered sections with clause_number set to null, and continue
          parsing remaining clauses.

  - name: summarize_policy
    description: Takes the structured sections produced by retrieve_policy and
      produces a clause-accurate summary that preserves every obligation, all
      conditions within multi-condition clauses, and all binding verbs exactly
      as they appear in the source.
    input:
      type: object
      format:
        fields:
          - name: sections
            type: list
            required: true
            notes: Output of retrieve_policy. Must contain at least one clause
              object with clause_number and body fields. Must not be empty or null.
          - name: raw_text
            type: string
            required: true
            notes: Full verbatim source text from retrieve_policy, used for
              verbatim quoting when a clause cannot be paraphrased without
              meaning loss.
    output:
      type: file
      format:
        mime_type: text/plain
        path: uc-0b/summary_hr_leave.txt
        notes: One summary entry per clause in source order. Each entry must
          begin with the clause number in brackets (e.g. [2.3]), followed by
          a single-sentence or verbatim summary. Clauses quoted verbatim must
          be marked with [VERBATIM — meaning loss risk]. The output file must
          contain an entry for every clause present in the input sections list
          with no additions, omissions, or reordering.
    error_handling:
      - trigger: sections list is empty or null
        action: Halt and raise an error stating no clause sections were provided.
          Do not produce an empty or partial output file.
      - trigger: a clause body is empty or whitespace only
        action: Write the entry as [CLAUSE_NUMBER] [VERBATIM — meaning loss risk]
          followed by a note that the clause body was absent in the source.
          Continue processing remaining clauses.
      - trigger: a clause contains a multi-condition obligation and paraphrasing
          would require dropping any condition (e.g. clause 5.2 requiring both
          Department Head AND HR Director approval)
        action: Quote the clause body verbatim and mark the entry with
          [VERBATIM — meaning loss risk]. Never drop a condition silently.
      - trigger: summarised text would require replacing a binding verb — must,
          will, requires, not permitted, are forfeited — with a weaker equivalent
        action: Retain the original binding verb exactly as it appears in the
          source. If retention is not possible without meaning loss, quote verbatim
          and flag with [VERBATIM — meaning loss risk].
      - trigger: scope bleed detected — summary contains phrases not present in
          the source such as "as is standard practice", "typically in government
          organisations", or "employees are generally expected to"
        action: Remove the offending phrase, re-derive the sentence strictly from
          source clause text, and log a scope bleed warning identifying the clause
          number and the removed phrase.
      - trigger: output directory does not exist
        action: Create the directory path before writing. If creation fails,
          raise a permission error and halt without writing partial output.