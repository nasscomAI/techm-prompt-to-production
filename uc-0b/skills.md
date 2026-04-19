skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as structured numbered sections.
    input: File path to the .txt policy document (String).
    output: Structured text containing mapped numbered sections and clauses (JSON or structured String).
    error_handling: Return an explicit error if the file cannot be located, is inaccessible, or if the content cannot be parsed into numbered sections.

  - name: summarize_policy
    description: Takes structured sections and produces a compliant summary with clause references.
    input: Structured text or JSON containing numbered sections of the policy document.(example ..\data\policydocs\leave-policy.txt)
    output: A compliant summary text preserving all obligations, conditions, and clause references.(example uc-0b\leave-policy-summary.txt)
    error_handling: Quote verbatim and flag any clauses that cannot be summarized without meaning loss. Return an error if required input sections are missing or malformed.
