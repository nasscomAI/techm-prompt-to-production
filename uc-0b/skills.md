# skills.md — UC-0B Summary That Changes Meaning

skills:
  - name: retrieve_policy
    description: >
      Loads a .txt policy file from disk and parses it into a structured list of
      numbered sections, returning each section with its heading, clause numbers,
      and raw text content ready for summarisation.
    input: >
      file_path (str): absolute or relative path to the policy .txt file
      (e.g. ../data/policy-documents/policy_hr_leave.txt).
    output: >
      list of dicts, each representing one top-level section:
        - section_number (str): e.g. "2", "3", "5"
        - section_title (str): e.g. "ANNUAL LEAVE"
        - clauses (list of dicts):
            - clause_id (str): e.g. "2.3", "5.2"
            - text (str): full raw clause text from the document
      Returns sections in document order. No content is altered, filtered, or added.
    error_handling: >
      - If file_path does not exist: raise FileNotFoundError with a clear message;
        do not return partial results.
      - If the file is empty: raise ValueError("Policy file is empty").
      - If no numbered clauses are found: raise ValueError with a message indicating
        the file may not be a valid policy document.
      - Never silently skip sections — all content must be passed through intact.

  - name: summarize_policy
    description: >
      Takes the structured sections from retrieve_policy and produces a compliant
      clause-by-clause summary that preserves all 10 mandatory clauses, all binding
      verbs, all multi-condition obligations, and contains no information outside the
      source document.
    input: >
      sections (list of dicts): output of retrieve_policy — structured sections with
      clause IDs and raw text.
      mandatory_clauses (list of str): clause IDs that MUST appear in the output
      (e.g. ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]).
    output: >
      str — a formatted plain-text summary with:
        - One entry per clause, prefixed with its clause number (e.g. "[2.3]")
        - Binding verbs preserved (must, will, requires, not permitted, are forfeited)
        - Multi-condition clauses showing ALL conditions
        - A [VERBATIM] flag appended to any clause quoted word-for-word due to
          risk of meaning loss on paraphrase
        - A MISSING CLAUSES section at the end listing any mandatory clause IDs
          not found in the source — never silently drop them
    error_handling: >
      - If a mandatory clause ID is not found in the sections input: include it in
        a "MISSING CLAUSES" section at the end of the summary — never silently omit.
      - If a clause contains a multi-condition obligation (identified by "and", "both",
        "as well as"): include a [MULTI-CONDITION] marker and verify all conditions
        are present before writing the summary line.
      - If a clause text is so complex that paraphrasing risks meaning loss: quote
        it verbatim and append [VERBATIM — risk of meaning loss if paraphrased].
      - Never add scope bleed phrases ("as is standard practice", "typically",
        "generally expected") — if tempted, refuse and flag the clause instead.
