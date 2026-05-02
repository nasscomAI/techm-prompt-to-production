skills:
  - name: retrieve_policy
    description: Reads the policy text file and returns its content.
    input: File path to .txt policy document
    output: Full text content
    error_handling: Returns an error if file is missing or unreadable

  - name: summarize_policy
    description: Generates a clause-preserving summary without losing obligations or conditions.
    input: Policy text
    output: Clause-preserving summary text
    error_handling: If summarization risks meaning loss, returns original text