skills:

- name: retrieve_documents
  description: Load all three policy documents and index by document name, section number, and keyword for rapid lookup.
  input: Directory path containing policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt.
  output: Dict with structure: {document_name: {section_num: section_text, ...}, ...}. Example: {'policy_hr_leave.txt': {'2.3': 'Employees must submit...', ...}, ...}
  error_handling: If any required file is missing, raise FileNotFoundError with list of missing files. If file is empty or unreadable, raise ValueError. Preserve original text verbatim.

- name: answer_question
  description: Search indexed documents for a direct answer to the question, return single-source answer with citation or refusal template.
  input: Question (string); indexed documents dict from retrieve_documents; refusal_template (string).
  output: Dict with keys: {'answer': string, 'source_document': string, 'section': string, 'is_refusal': bool}. If found: answer text + source+section. If not found: refusal template (verbatim) + is_refusal=True.
  error_handling: If question is ambiguous or could be answered from multiple documents, search in this order (priority): HR > IT > Finance. Return from first matching document only. Never combine sources. If no match found, return refusal template verbatim.
