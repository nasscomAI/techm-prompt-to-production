skills:
  - name: retrieve_policy
    description: Loads a policy text file and returns its content as structured, numbered sections.
    input: File path to policy document (e.g., .txt format)
    output: A structured object or collection of text blocks keyed by clause numbers (e.g., {"2.3": "text", "2.4": "text"})
    error_handling: Refuses to process if the file format is unreadable or if clause numbering cannot be identified.

  - name: summarize_policy
    description: Takes the structured sections from the policy and produces a compliant summary that retains all core obligations and multi-conditions, referencing original clause numbers.
    input: Structured object of numbered clauses from retrieve_policy
    output: A text summary containing clear obligations mapped to their original clause references
    error_handling: Quotes clauses verbatim and flags them if they cannot be summarized without altering their exact meaning or conditions.
