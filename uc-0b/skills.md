# skills.md

skills:
  - name: retrieve_policy
    description: Loads a policy text file and parses it into structured numbered sections for analysis.
    input: Path to the .txt policy file (String).
    output: A collection of structured sections containing clause numbers and their full text (List of Objects).
    error_handling: Return a FileNotFoundError if the path is invalid or a ParsingError if the document structure is unreadable.

  - name: summarize_policy
    description: Condenses structured policy sections into a compliant summary while preserving all clauses and conditions.
    input: Structured sections from retrieve_policy (List of Objects).
    output: A high-fidelity summary string with clause references, ensuring no condition drops or scope bleed (String).
    error_handling: Flags sections that cannot be summarized without meaning loss and returns a verbatim quote for those specific clauses.
