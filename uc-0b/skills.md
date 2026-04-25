skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as an ordered
      list of numbered sections, preserving all clause numbers and original wording.
    input: Absolute or relative file path to a plain-text policy document (string).
    output: Ordered list of sections, each as a dict with keys `section_number`
      (str, e.g. "2.3"), `heading` (str, parent section title), and `text`
      (str, verbatim clause text). Returns an empty list if the file is empty.
    error_handling: Raises FileNotFoundError if the path does not exist.
      Raises ValueError if the file is not plain text or cannot be parsed into
      numbered sections. Never returns partial content — caller must receive
      the full document or an explicit error.

  - name: summarize_policy
    description: Takes the structured section list from retrieve_policy and
      produces a compliant summary in which every clause is present, binding
      verbs are preserved, and no information outside the source is added.
    input: List of section dicts as returned by retrieve_policy (same schema —
      section_number, heading, text).
    output: Plain-text summary string. Each paragraph is prefixed with its
      clause number (e.g. "[2.3]"). Multi-condition clauses are written as
      a bulleted sub-list to make all conditions visually distinct. Clauses
      that cannot be safely paraphrased are quoted verbatim and tagged
      [VERBATIM — summarisation would alter meaning].
    error_handling: Raises ValueError if the input list is empty or missing
      any of the 10 tracked clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4,
      5.2, 5.3, 7.2). Never produces partial output — either the full
      compliant summary is returned or an error is raised with the list of
      missing clauses.
