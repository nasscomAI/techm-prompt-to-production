skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as structured numbered sections.
    input: >
      File path (string) pointing to a .txt policy document.
      Expected: ../data/policy-documents/policy_hr_leave.txt
    output: >
      Structured text with each top-level section heading and its numbered clauses
      preserved exactly as written in the source — no paraphrasing at this stage.
    error_handling: >
      If the file path is invalid, the file is unreadable, or the document reference
      does not match HR-POL-001, return a FileNotFoundError with a clear message and
      refuse to proceed. Do not fabricate or substitute content.

  - name: summarize_policy
    description: >
      Takes structured sections from retrieve_policy and produces a clause-complete,
      compliant summary written to summary_hr_leave.txt.
    input: >
      Structured policy sections (string) as returned by retrieve_policy.
    output: >
      Plain-text file (summary_hr_leave.txt) where:
        - Every numbered clause is represented with its source reference (e.g. §2.3)
        - Binding verbs (must, will, requires, not permitted) are preserved verbatim
        - All multi-condition obligations state ALL conditions (e.g. §5.2 names both approvers)
        - No content is added beyond what appears in the source document
    error_handling: >
      If any of the 10 ground-truth clauses (§2.3, §2.4, §2.5, §2.6, §2.7, §3.2, §3.4,
      §5.2, §5.3, §7.2) cannot be summarised without dropping a condition or softening a
      binding verb, quote the clause verbatim and append [VERBATIM — meaning loss risk].
      If scope bleed phrases are detected in the draft output, remove them before writing.
      Never silently omit or paraphrase a clause in a way that changes its obligation.
