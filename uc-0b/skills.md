# skills.md

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as structured numbered sections.
    input: File path (str) to a plain-text policy document
      (e.g. ../data/policy-documents/policy_hr_leave.txt).
    output: A dict with two keys —
        - raw_text (str): full file content
        - sections (list of dicts): each dict has clause_number (str) and clause_text (str),
          parsed by numbered heading (e.g. "2.3", "3.2")
    error_handling: If the file does not exist, raise FileNotFoundError with the path.
      If the file is empty, raise ValueError("Policy file is empty").
      Never proceed with an empty or missing document.

  - name: summarize_policy
    description: Takes structured policy sections and produces a compliant summary with clause
      references, preserving all binding verbs and multi-condition obligations per agents.md.
    input: A dict from retrieve_policy — raw_text (str) and sections (list of clause dicts).
    output: A plain-text summary string where each clause appears as a labelled entry
      (e.g. "Clause 2.3: Employees must provide 14 days advance notice."). Clauses that
      cannot be summarised without meaning loss are quoted verbatim and marked [VERBATIM].
      All 10 required clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2) must
      be present in the output.
    error_handling: If raw_text is blank or sections is empty, raise
      ValueError("No policy content to summarise"). If the model response omits any
      required clause, re-prompt once listing the missing clause numbers explicitly.
      If still incomplete after one retry, raise RuntimeError listing the missing clauses.
