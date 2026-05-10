skills:
  - name: retrieve_policy
    description: >
      Loads a .txt policy document from the given file path and returns its
      content parsed as structured numbered sections, indexed by section number
      for downstream clause-level access.
    input: >
      A file path string pointing to the .txt policy document
      (e.g. ../data/policy-documents/policy_hr_leave.txt).
    output: >
      A structured representation of the document as an ordered list of sections,
      each with a section number (e.g. "2.3"), a title (if present), and the
      full clause text. Binding verbs (must, will, requires, not permitted) are
      preserved verbatim.
    error_handling: >
      If the file is not found or is empty, raise an error and halt — do not
      produce a partial summary from incomplete input. If a section boundary
      cannot be parsed, include the unparsed block as-is and flag it for review.

  - name: summarize_policy
    description: >
      Takes the structured sections produced by retrieve_policy and generates
      a clause-accurate, meaning-preserving summary that includes every numbered
      clause with all binding conditions, approvers, thresholds, and deadlines
      intact.
    input: >
      The structured section list produced by retrieve_policy — an ordered list
      of sections each containing a section number and full clause text.
    output: >
      A plain-text summary file written to uc-0b/summary_hr_leave.txt. Each
      clause in the summary must reference its source section number, preserve
      all binding verbs and numeric thresholds, and retain all named approvers
      and multi-party conditions. Any clause that cannot be summarised without
      meaning loss must be quoted verbatim from the source and flagged as a
      direct quote.
    error_handling: >
      If a clause is ambiguous or cannot be reduced without risking meaning loss,
      quote it verbatim from the source document and explicitly mark it as
      [DIRECT QUOTE — not summarised]. Never omit a clause. Never infer, assume,
      or introduce information not present in the source document.
