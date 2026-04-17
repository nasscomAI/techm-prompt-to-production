# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_documents
    description: Loads and indexes all policy documents by document name and section number for structured retrieval.
    input: type: none
           format: No external input required; uses predefined file paths.
    output: type: dictionary
            format: Key-value structure where keys are document names and values are indexed sections with section numbers mapped to their text content.
    error_handling: 
    If any document file is missing or unreadable, return an error indicating which file could not be loaded and halt execution.
    If document structure cannot be parsed into sections, return an error specifying invalid document format.
    Do not attempt to infer or reconstruct missing sections or content.
    Ensure no merging or blending of content across documents during indexing.

  - name: answer_question
    description: Answers user questions using a single policy document source with exact citation or returns a refusal if not found.
    input: type: string
           format: Natural language question entered via CLI.
    output: type: string
            format: Either a single-source answer including document name and section number citations, or the exact refusal template string.
    error_handling:
    If the question does not match any content in the documents, return exactly: "This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance."
    If multiple documents contain partial or related answers, do not combine them; select one valid source or return the refusal template if ambiguity remains.
    If the query would require combining information from multiple documents, return the refusal template instead of blending.
    If input is empty, malformed, or not a valid question, return the refusal template.
    Do not include hedging phrases such as "while not explicitly covered", "typically", "generally understood", or "it is common practice".
    Ensure every factual claim in the answer includes document name and section number citation; otherwise return the refusal template. 



