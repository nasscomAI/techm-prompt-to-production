
skills:
  - name: retrieve_policy
    description: Loads .txt policy file, returns content as structured numbered sections
    input: File path to the .txt policy document
    output: Content parsed into a list of dictionaries representing structured numbered sections
    error_handling: Return an error if the file cannot be loaded. If it lacks numbered sections, return the raw text without restructuring.

  - name: summarize_policy
    description: Takes structured sections, produces compliant summary with clause references retaining all conditions of obligations
    input: A list of dictionaries representing structured numbered sections
    output: Compliant text summary with clause references
    error_handling: If a clause cannot be summarized without meaning loss, quote it verbatim and flag it as "[Flagged_Verbatim]"
