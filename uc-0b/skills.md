# skills.md — UC-0B Summary That Changes Meaning

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns its content as a dict of clause_id → full clause text, preserving multi-line clauses.
    input: path (str) — absolute or relative path to the policy .txt file
    output: dict mapping clause IDs (e.g. "2.3", "5.2") to their full text as a single string
    error_handling: Exits with an error message if the file is not found; skips lines that are decorative separators (═══) and re-joins wrapped continuation lines

  - name: summarize_policy
    description: Takes the structured clause dict and produces a compliant summary text that lists every clause with its source reference and flags all 10 required clauses.
    input: sections (dict of clause_id → text), source_path (str) for attribution
    output: str — a formatted summary including section headers, all clauses with [REQUIRED] markers, and a compliance verification table at the end
    error_handling: Inserts a [COMPLIANCE WARNING] block listing any required clauses not found in sections; never silently omits required clauses
