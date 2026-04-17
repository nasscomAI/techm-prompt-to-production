# skills.md

skills:
  - name: retrieve_policy
    description: Load and parse a plain text policy document into structured numbered clauses with binding verbs and obligations extracted.
    input: |
      Parameters:
      - policy_file: path to .txt policy file (string)
      Returns: structured policy object with:
      - filename: name of policy file
      - clauses: list of clause objects, each containing:
        - clause_num: clause identifier (e.g., "2.3", "5.2")
        - full_text: complete text of the clause verbatim
        - binding_verb: the obligation verb (must, will, requires, may, are forfeited, not permitted)
        - conditions: list of conditions extracted from clause (e.g., ["Department Head approval", "HR Director approval"])
    output: |
      Structured policy object (dict/JSON) with:
      - filename: string
      - total_clauses: integer count
      - clauses: list of clause objects as defined above
      - parse_errors: list of any clauses that failed to parse with clause numbers and reason
    error_handling: |
      If policy file not found: log error with file path and halt.
      If file is empty: return empty clauses list with warning.
      If numbered clause structure not found (missing clause numbers): log warning that document may not be a numbered policy;
        attempt to parse anyway by identifying lines with binding verbs (must, will, requires, may, not permitted).
      If clause number formatting is inconsistent (e.g., "2.3" vs "2-3"): normalize to decimal format and log normalization action.
      If conditions within a clause cannot be clearly extracted: include the full clause text and mark as requiring manual review.

  - name: summarize_policy
    description: Convert structured policy clauses into a compliant summary that preserves all obligations, conditions, and binding verbs with clause references.
    input: |
      Structured policy object (output of retrieve_policy) containing:
      - clauses: list of clause objects with clause_num, full_text, binding_verb, and conditions
      Parameters (optional):
      - format: "text" or "json" (default: "text")
      - include_flags: boolean to include compliance flags (default: true)
    output: |
      Summary document (string if format="text", or dict/JSON if format="json") with:
      - header: title line including policy name and summary date
      - summary_clauses: list of summarized clauses, each containing:
        - clause_ref: clause number (e.g., "[Clause 2.3]")
        - obligation: one-sentence summary citing binding verb and all conditions
        - binding_verb: exact verb from source (must, will, requires, etc.)
        - flags: compliance flags if any (e.g., "#FLAG: Verbatim quote required", "#FLAG: Multi-condition preservation")
      - clause_count: total clauses included
      - missing_clauses: list of any clauses from input not included in summary (must be empty if compliance achieved)
      - flags_summary: list of all compliance flags raised
    error_handling: |
      If any clause from input is omitted from summary: add its clause_num to missing_clauses list and raise flag "#FLAG: Clause omission detected".
      If multi-condition clause detected (conditions joined by AND): ensure ALL conditions preserved in summary; if any dropped, raise flag "#FLAG: Condition drop detected in [Clause X.Y]".
      If clause meaning would be lost in summarization (e.g., complex nested conditions): output clause verbatim in quotes with clause reference and raise flag "#FLAG: Verbatim quote required for compliance — Clause X.Y may lose meaning if summarized".
      If binding_verb cannot be preserved (e.g., summary simplification): raise flag "#FLAG: Binding verb softening detected in [Clause X.Y]".
      If extra-document language detected in summary (phrases like "typically", "as is standard", "generally expected"): remove it, log warning, and raise flag "#FLAG: Scope bleed detected and removed".
      After summarization complete: validate that all input clauses appear in output; if any missing, halt and return error with list of missing clause numbers.
