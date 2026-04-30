# skills.md

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and parses it into a list of structured sections, preserving clause numbering.
    input: File path (string) to the policy document.
    output: List of dictionaries, each containing 'clause_id' and 'text'.
    error_handling: Raises FileNotFoundError if the file is missing; returns an empty list if no numbered clauses are found.

  - name: summarize_policy
    description: Generates a high-precision summary of policy sections while strictly enforcing RICE rules to prevent clause omission or obligation softening.
    input: List of structured sections from retrieve_policy.
    output: A single string containing the consolidated summary with original clause references.
    error_handling: Flags sections that cannot be summarized accurately with [PRECISION_REQUIRED] and includes them verbatim.
