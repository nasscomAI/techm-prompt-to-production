# skills.md — UC-0B Policy Summariser

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content parsed as an ordered list of numbered sections and their clause text.
    input: String file_path — absolute or relative path to the .txt policy document.
    output: List of dicts, each with keys 'section' (e.g. "2.3"), 'heading' (parent section title), and 'text' (the clause text verbatim).
    error_handling: If the file is missing or unreadable, raise FileNotFoundError with the path. If no numbered clauses are detected, return the raw text as a single entry and log a warning.

  - name: summarize_policy
    description: Takes the structured list of numbered sections and produces a clause-complete, compliant plain-language summary with every clause reference preserved.
    input: List of dicts as returned by retrieve_policy (keys 'section', 'heading', 'text').
    output: String — a formatted summary where each clause appears under its section heading with its clause number, binding obligation, and a flag if verbatim quoting was required to avoid meaning loss.
    error_handling: If any of the mandatory clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2) are absent from the input, raise a MissingClauseError listing which clauses could not be found before returning a partial summary.
