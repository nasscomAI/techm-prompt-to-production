# skills.md — UC-0B Policy Summarizer

skills:
  - name: retrieve_policy
    description: Load a .txt policy file and return its content as structured numbered sections.
    input: String path to the policy .txt file.
    output: String of the structured policy content.
    error_handling: Return an error string if the file is not found or cannot be read.

  - name: summarize_policy
    description: Pass the structured policy content to an LLM with strict RICE enforcement rules to produce a compliant summary with clause references.
    input: String of structured sections.
    output: String of the final compliant summary.
    error_handling: Return an error string if the LLM call fails or returns invalid formatting.
