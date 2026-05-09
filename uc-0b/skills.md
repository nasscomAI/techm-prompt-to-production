skills:

- name: retrieve_policy
  description: Load HR leave policy document and parse into structured numbered sections with clause references.
  input: File path to policy_hr_leave.txt (TXT format).
  output: Dict with sections as keys and list of (clause_number, clause_text) tuples as values. Example: {"2. ANNUAL LEAVE": [("2.3", "Employees must submit..."), ("2.4", "Leave applications must...")], ...}
  error_handling: If file not found, raise FileNotFoundError. If file is empty, raise ValueError. Parse robustly; skip malformed clause numbers. Preserve original binding verbs verbatim.

- name: summarize_policy
  description: Take structured policy sections and produce a clause-preserving summary that includes all obligations, all multi-part conditions, and verbatim quotes for ambiguous clauses.
  input: Dict from retrieve_policy (sections and clauses); list of critical clause numbers to verify (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2).
  output: String containing summary with clause references, flagged ambiguities, and verification that all 10 critical clauses are present with original binding verbs intact. Format: line per clause, e.g., "2.3: Employees must submit leave request 14 days in advance."
  error_handling: If any critical clause is missing from source, output [FLAG: CLAUSE N.M NOT FOUND] at end. If multi-condition clause detected (e.g., 'and' appears), preserve both conditions or flag as [FLAG: CLAUSE N.M CONDITION DROP RISK]. Never drop a condition silently.
