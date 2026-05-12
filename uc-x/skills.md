skills:
  - name: retrieve_documents
    description: Loads and indexes the three policy documents by document name and section number for retrieval.Loads and indexes the three policy documents by document name and section number for retrieval.
    input:
      type: none
      format: no user input required; reads files from predefined paths
    output:
      type: structured_data
      format: dictionary keyed by document name with nested section-number mappings to text content
    error_handling:
      - If any document file is missing or unreadable, return an error indicating which file failed and halt further processing
      - If documents cannot be indexed by section, return an error indicating malformed structure
      - Do not infer or fabricate missing sections or content

  - name: answer_question
    description: Searches indexed policy documents and returns a single-source answer with citation or the refusal template.
    input:
      type: string
      format: natural language question
    output:
      type: string
      format: either a single-source answer including document name and section number citations for every claim, or the exact refusal template text
    error_handling:
      - If the question is not explicitly answered in any single document, return exactly: "This question is not covered in the available policy documents\n(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).\nPlease contact [relevant team] for guidance."
      - If answering would require combining information from multiple documents, either select a valid single-document answer or return the refusal template
      - If the query is ambiguous across documents and cannot be resolved without blending, return the refusal template
      - Never use hedging phrases such as "while not explicitly covered", "typically", "generally understood", or "it is common practice"
      - If input is empty or invalid, return the refusal template without modification