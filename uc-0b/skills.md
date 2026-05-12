skills:
  - name: retrieve_policy
    description: >
      Loads a plain-text policy file from disk and returns its content parsed
      into an ordered list of structured numbered sections, preserving every
      clause number, heading, and body text exactly as written.
    input:
      type: string
      format: >
        Absolute or relative file path pointing to a .txt policy document
        (e.g. ../data/policy-documents/policy_hr_leave.txt).
    output:
      type: list
      format: >
        Ordered list of objects, one per top-level section and sub-clause,
        each containing:
          - clause_id: string  (e.g. "2.3", "5.2")
          - heading: string    (section heading if present, else null)
          - body: string       (verbatim clause text as it appears in the file)
    error_handling:
      file_not_found: >
        Raise a FileNotFoundError with the attempted path; do not proceed to
        summarisation. Surface the error to the caller immediately.
      unreadable_or_empty: >
        If the file exists but is empty or cannot be decoded, raise an
        IOError with a message stating the file is empty or unreadable; do
        not return a partial result.
      no_numbered_sections_detected: >
        If the parsed content contains no recognisable clause numbers (pattern
        d+\\.d+), raise a StructureError stating that no numbered clauses were
        found and that the file may not be a structured policy document; do not
        pass unparsed text to summarize_policy.
      wrong_file_type: >
        If the path does not end in .txt, emit a warning and attempt to read
        the file as plain text; if decoding fails, raise an IOError.

  - name: summarize_policy
    description: >
      Accepts the structured numbered sections produced by retrieve_policy and
      generates a clause-complete, obligation-faithful summary that references
      every clause by its original clause number and preserves all binding
      conditions verbatim where meaning loss would otherwise occur.
    input:
      type: list
      format: >
        Ordered list of clause objects as returned by retrieve_policy, each
        containing clause_id (string), heading (string or null), and body
        (string). The required clause IDs for a valid run of policy_hr_leave
        are: 2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2.
    output:
      type: string
      format: >
        Plain-text summary written to the configured output file
        (uc-0b/summary_hr_leave.txt). Each clause is summarised in a labelled
        paragraph starting with its clause_id. Clauses that cannot be
        summarised without meaning loss are quoted verbatim from the source
        body and appended with the flag [VERBATIM — meaning-loss risk].
    error_handling:
      missing_required_clause: >
        If any of the 10 required clause IDs (2.3, 2.4, 2.5, 2.6, 2.7, 3.2,
        3.4, 5.2, 5.3, 7.2) is absent from the input list, raise a
        ClauseOmissionError naming every missing clause ID; do not write a
        partial summary to disk.
      condition_drop_detected: >
        Before writing output, run a self-check: for clause 5.2 verify that
        both "Department Head" and "HR Director" are named; for clause 2.4
        verify the negation "verbal" or "not valid" is present; for clause 7.2
        verify "any circumstances" or equivalent absolute language is present.
        If any check fails, raise a ConditionDropError identifying the clause
        and the missing condition; do not write the summary.
      scope_bleed_detected: >
        Scan the draft output for the literal phrases "as is standard
        practice", "typically in government organisations", and "employees are
        generally expected to", plus any sentence that cannot be traced to a
        clause body in the input list. If found, raise a ScopeBleedError
        quoting the offending phrase and its location; do not write the summary.
      obligation_softening_detected: >
        If a binding verb in the source (must, will, requires, not permitted,
        are forfeited) has been replaced with a weaker synonym (should, may
        wish to, is recommended, generally not permitted) in the draft output,
        raise an ObligationSofteningError identifying the clause and the
        substituted verb; do not write the summary.
      empty_input: >
        If the input list is empty, raise a ValueError stating that no clause
        sections were provided; do not produce any output file.
