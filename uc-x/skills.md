# skills.md

skills:
  - name: retrieve_documents
    description: Loads all 3 policy files and indexes them securely by document name and section number.
    input: List of paths to policy documents (.txt).
    output: A nested dictionary structure organizing text strictly by document and section identifiers.
    error_handling: Fail gracefully and report missing files.

  - name: answer_question
    description: Searches indexed documents and returns single-source answer + citation OR strictly the refusal template.
    input: Question string from the user, and the indexed documents structure.
    output: String mapping exactly to a single section reference or the verbatim refusal template.
    error_handling: If standard string matching implies ambiguity or absence, safely default exclusively to the refusal template rather than hallucinating an approximate answer.
