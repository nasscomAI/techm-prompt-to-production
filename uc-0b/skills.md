# skills.md
# INSTRUCTIONS: Generate a draft by prompting AI, then manually refine this file.
# Delete these comments before committing.

skills:
  - name: retrieve_policy
    description: Load the HR leave policy text file and return its contents as structured, numbered sections.
    input: 
      type: file_path
      format: relative or absolute path to a .txt file (e.g., ../data/policy-documents/policy_hr_leave.txt)
    output: 
      type: policy_sections
      format: list of objects with fields {clause_number, heading, body_text}
    error_handling: If the file path is missing, invalid, or unreadable, return an explicit error message and do not attempt to summarise. If the loaded text does not   contain the expected numbered clauses (such as 2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2), flag this as a structural error and stop instead of inferring or inventing missing content.

  - name: summarize_policy
    description: Generate a compliant summary of the HR leave policy that preserves all binding obligations and clause conditions.
    input: 
      type: policy_sections
      format: list of objects with fields {clause_number, heading, body_text} as returned by retrieve_policy
    output: 
      type: text
      format: multi-line plain-text summary, grouped by topic, with explicit clause references (e.g., “(Clause 2.3)”)
    error_handling: If required clauses (2.3, 2.4, 2.5, 2.6, 2.7, 3.2, 3.4, 5.2, 5.3, 7.2) are missing from the input sections, or if any multi-condition obligation would lose a condition in summarisation (e.g., only one approver mentioned for clause 5.2), the skill must either: (a) include the full clause verbatim and flag it as quoted, or (b) return an explicit error instead of producing a misleading partial summary. The skill must never add scope-bleed language or invented obligations not present in the source text.
-+
