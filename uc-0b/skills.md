# skills.md

skills:
  - name: retrieve_policy
    description: Loads a .txt policy file and returns the content as structured numbered sections.
    input: The file path to the policy document (string).
    output: A string or structured list representing the verbatim text of the policy document.
    error_handling: Raises an error if the document is missing or unreadable.

  - name: summarize_policy
    description: Takes structured sections of a policy document and produces a compliant summary adhering strictly to the clause preservation rules.
    input: The parsed policy text (string).
    output: A summarized text document preserving every numbered clause, multi-condition obligation, and avoiding hallucinations.
    error_handling: If the input text is not numbered or cannot be mapped accurately without dropping meaning, it quotes the text verbatim and flags it for review.
