# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_documents
    description: Loads the three policy documents and indexes them by document name and section number for later lookup.
    input: The file paths to policy_hr_leave.txt, policy_it_acceptable_use.txt, and policy_finance_reimbursement.txt.
    output: An in-memory index structure mapping each document name and section number to its text content, plus a flat list of all sections that can be searched for relevant answers.
    error_handling: If any file cannot be opened, raise a clear error and stop the system rather than answering from partial data. If a document does not have identifiable section markers, load it as a single catch-all section with a synthetic section label (e.g. 'section unknown') and still ensure that answers cite the document name. Never silently skip a document.

  - name: answer_question
    description: Searches the indexed policy documents for a relevant section and returns a single-source answer with citation or the refusal template.
    input: A natural-language question string and the in-memory index of policy documents created by retrieve_documents.
    output: Either (a) a concise answer string that quotes or paraphrases one specific policy section and includes an explicit citation of the document name and section number, or (b) the exact refusal template when the question is not covered.
    error_handling: If multiple documents appear relevant but with different conditions, do not blend them; either choose the single best document or refuse with the template if ambiguity remains. If no section clearly addresses the question, return only the refusal template. If the question is vague or multi-part, ask the user to clarify rather than guessing or making cross-document assumptions.
