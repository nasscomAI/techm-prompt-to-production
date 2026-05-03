# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_documents
    description: Retrieve relevant documents for a given query.
    input: loads all 3 policy files, indexes by document name and section number
    output: searches indexed documents
    error_handling: If document not found: return "No relevant documents found" and do not proceed.

  - name: answer_question
    description: For each question, extract the single most relevant document, then extract and format all specific claims from that document as sentences starting with "According to [policy_name], ...". Only use information that appears explicitly in the text.
    input:searches indexed documents
    output:returns single-source answer + citation OR refusal template 
    error_handling: If multiple documents equally relevant: pick first
