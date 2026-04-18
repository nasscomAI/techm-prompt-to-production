skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as structured numbered sections, preserving the original clause hierarchy and numbering exactly as written.
    input: File path (string) pointing to a plain-text policy document (e.g. policy_hr_leave.txt).
    output: Structured object containing numbered sections and clauses (e.g. 2.3, 2.4, 5.2) extracted from the source file, with original text preserved verbatim.
    error_handling: If the file is not found or is not a .txt file, return an error and halt — do not attempt to infer or substitute content. If a clause number is malformed or missing, flag it and return the raw surrounding text without restructuring.

  - name: summarize_policy
    description: Takes the structured numbered sections from retrieve_policy and produces a clause-faithful plain-language summary with explicit clause ID references, without omitting clauses, dropping conditions, or softening binding verbs.
    input: Structured section object from retrieve_policy, containing clause IDs and their verbatim source text.
    output: Plain-language summary (string) where every clause (2.3–2.7, 3.2, 3.4, 5.2, 5.3, 7.2) is present, all multi-condition obligations list ALL conditions, and binding verbs (must, will, requires, not permitted) are preserved exactly.
    error_handling: If a clause cannot be summarised without dropping a condition or softening an obligation, quote that clause verbatim in the output and append the flag [VERBATIM — meaning loss risk]. Never silently omit a clause or condition.
