skills:
  - name: retrieve_policy
    description: Loads a policy text file and converts it into structured numbered sections for downstream processing.
    input:
      type: string
      format: file path to a .txt document containing numbered policy clauses
    output:
      type: object
      format: structured representation of the document as ordered numbered sections with clause IDs and full text
    error_handling:
      - If the file path is invalid or the file cannot be read, return an explicit error indicating file access failure
      - If the document lacks clear numbered sections, return an error indicating unstructured input
      - If expected clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2) cannot be identified, flag missing clauses explicitly without fabricating them
      - Do not infer or create content not present in the source document

  - name: summarize_policy
    description: Generates a compliant summary of all structured policy sections while preserving all clause meanings and obligations.
    input:
      type: object
      format: structured numbered sections with clause IDs and full text
    output:
      type: string
      format: concise summary covering the full document with explicit clause references and preserved obligations
    error_handling:
      - If any required clause (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2) is missing, return an error listing missing clauses
      - If a clause contains multiple conditions and cannot be fully preserved in summarized form, quote it verbatim and flag it
      - If summarization introduces external assumptions, generalized phrasing, or scope bleed, reject output and return an error
      - If obligation strength (e.g., "must", "requires", "not permitted", "will") is weakened, altered, or omitted, reject output and flag obligation softening
      - If input format is ambiguous or incomplete, return an error requesting valid structured sections without attempting inference