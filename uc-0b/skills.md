skills:
  - name: retrieve_policy
    description: Loads a plain-text policy file and returns its content as structured, numbered sections keyed by clause number.
    input: |
      A file path (string) pointing to a plain-text policy document. Example:
        retrieve_policy(path="../data/policy-documents/policy_hr_leave.txt")
    output: |
      A dict/JSON object where each key is a clause number and the value is the
      verbatim clause text. Example:
        {
          "2.3": "Employees must provide at least 14 days advance notice ...",
          "2.4": "Written approval is required before leave commences ...",
          ...
        }
    error_handling: |
      - If the file path is missing or the file is unreadable, raise
        FileNotFoundError with the full path in the message and halt — do not
        return partial content.
      - If the file is empty or contains no parseable clause structure, return
        an empty dict and flag the result with a warning:
        {"warning": "No structured clauses found in the source document."}.
      - Never infer, add, or paraphrase clause content — return only verbatim
        text from the file.

  - name: summarize_policy
    description: Accepts structured policy sections produced by retrieve_policy and returns a clause-by-clause compliant summary that preserves all obligations, conditions, and binding verbs without omission or softening.
    input: |
      A dict/JSON object of numbered policy sections (output of retrieve_policy).
      Example:
        summarize_policy(sections={"2.3": "...", "2.4": "...", ...})
    output: |
      A structured plain-text summary where every input clause is represented,
      each referenced by its clause number, and all multi-condition obligations
      are preserved in full. Example format:
        Clause 2.3: Employees must provide 14 days advance notice before leave.
        Clause 2.4: Written approval must be obtained before leave commences;
                    verbal approval is not valid.
        ...
      If a clause cannot be summarised without loss of meaning, it is quoted
      verbatim and marked [VERBATIM].
    error_handling: |
      - If the input sections dict is empty, return an empty string and flag:
        "No clauses provided — summary cannot be generated."
      - If any clause is missing from the output, the skill must raise a
        ClauseOmissionError listing the missing clause numbers — do not produce
        a partial summary silently.
      - Never introduce information not present in the source sections (no scope
        bleed such as "as is standard practice" or "typically in government
        organisations").
      - If a multi-condition obligation is detected (e.g., Clause 5.2 requiring
        BOTH Department Head AND HR Director approval), all conditions must
        appear in the output — dropping any one condition is treated as an error.
