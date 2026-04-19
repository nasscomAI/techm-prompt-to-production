skills:

  - name: retrieve_documents
    description: >
      Loads and retrieves relevant sections from the allowed policy documents, preserving document name and section boundaries.
    input: >
      {
        "query": "string"
      }
    output: >
      {
        "results": [
          {
            "doc_name": "string",
            "section": "string",
            "content": "string"
          }
        ]
      }
    error_handling: >
      - If query is empty or null → return {"results": []}
      - If no relevant sections found → return {"results": []}
      - Must preserve exact section boundaries; partial sections or merged sections are not allowed
      - Must NOT rank, infer, or prioritize content beyond direct textual matching
      - Must NOT fabricate or infer content; only return exact matches from indexed documents


  - name: answer_question
    description: >
      Determines whether a question can be answered using exactly one section from one document and returns either a strictly grounded answer with citation or the refusal template.
    input: >
      {
        "query": "string",
        "retrieved_chunks": [
          {
            "doc_name": "string",
            "section": "string",
            "content": "string"
          }
        ]
      }
    output: >
      EITHER:
      {
        "answer": "string",
        "source": {
          "doc_name": "string",
          "section": "string"
        }
      }

      OR (refusal):
      {
        "answer": "This question is not covered in the available policy documents
        (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).
        Please contact [relevant team] for guidance."
      }
    error_handling: >
      - If query is empty or invalid → return refusal template
      - If retrieved_chunks is empty → return refusal template
      - If multiple documents or multiple sections are required → return refusal template
      - If answer is partial, ambiguous, or not explicitly stated in one section → return refusal template
      - Must NOT combine, infer, or complete missing information under any condition