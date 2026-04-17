# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_policy
    description: Loads the policy text file and converts it into structured numbered sections for downstream processing.
    input: type: string
           format: file path to a .txt policy document (e.g., ../data/policy-documents/policy_hr_leave.txt)
    output: type: list
            format: ordered list of objects with clause_number and clause_text fields representing structured sections
    error_handling: If the file path is invalid or file cannot be read, return an explicit file access error
                    If the file is empty or lacks numbered clauses, return a structured format error
                    If clause numbering is inconsistent or ambiguous, flag the issue and halt processing
                    Do not infer or fabricate missing clauses; return only what is explicitly present in the document

  - name: summarize_policy
    description: Generates a clause-complete summary from structured policy sections while preserving all obligations and references.
    input: type: list
           format: ordered list of objects with clause_number and clause_text fields
    output: type: string
            format: structured summary text including all clause references with preserved obligations and conditions
    error_handling: If any of the required clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2) are missing, return a clause omission error
    If a clause contains multi-condition obligations and any condition cannot be preserved, quote the clause verbatim and flag it
    If summarization introduces information not present in the input, remove it and flag a scope bleed error
    If binding verbs are altered or softened, revert to original phrasing and flag an obligation softening error
    If input structure is invalid or incomplete, return an input validation error and halt processing


