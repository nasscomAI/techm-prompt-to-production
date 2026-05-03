skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns the content as structured, numbered sections for precise mapping.
    input: File path to the policy document (string).
    output: Structured content mapped by clause numbers (dictionary/JSON).
    error_handling: Refuse if file is missing or contains unnumbered/ambiguous sections.

  - name: summarize_policy
    description: Processes structured policy sections into a compliant summary, ensuring all obligations and conditions are preserved.
    input: Structured sections from retrieve_policy (dictionary/JSON).
    output: Loss-less summary string with clause references.
    error_handling: Flag and quote verbatim any clause where summarization would result in condition loss or meaning drift.
