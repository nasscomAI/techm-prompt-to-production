# skills.md — UC-X Ask My Documents

skills:
  - name: retrieve_documents
    description: Loads all 3 CMC policy files and indexes them by document name and section number, ready for single-source lookup.
    input: docs_dir (str) — path to the directory containing the three policy .txt files
    output: dict mapping filename → {section_id: text}, e.g. {"policy_hr_leave.txt": {"2.6": "Employees may carry forward..."}}
    error_handling: Prints a warning to stderr for any file not found and stores an empty dict for that document; does not abort if one file is missing

  - name: answer_question
    description: Searches the indexed documents for the best single-source answer to a question; returns the answer with citation, or the exact refusal template if not found.
    input: question (str), docs (dict from retrieve_documents)
    output: str — either "[Source: <filename>] Section <id>: <text>" or the exact refusal template
    error_handling: Returns the refusal template (never a partial or hedged answer) when no section matches with sufficient confidence; never blends content from two documents; routing table checked first to prevent cross-document synthesis on known trap questions
