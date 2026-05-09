skills:
  - name: retrieve_policy
    description: Load a policy text file and return it as structured, numbered sections.
    input:
      type: string
      format: "filesystem path (e.g. ../data/policy-documents/policy_hr_leave.txt)"
    output:
      type: object
      schema:
        sections:
          - clause_id: string
            title: string
            lines: integer_range  # 1-based inclusive line numbers from source file
            text: string
    error_handling:
      FileNotFound:
        code: "file_not_found"
        message: "file not found"
        details: { path: "<input>" }
      ParseFailure:
        code: "parse_failure"
        message: "unable to detect numbered sections"
        details: { raw_text: "<file contents>" }
      PartialParse:
        code: "partial_parse"
        message: "some sections parsed, see diagnostics"
        details: { parsed_sections: "<sections>", diagnostics: "<details>" }

  - name: extract_clause_inventory
    description: Extract a prioritized clause inventory (clause id, core obligation, binding verb, exact excerpt).
    input:
      type: object
      schema:
        sections: as-returned-by-retrieve_policy
        priority_clauses: array[string]  # optional list like ["2.3","2.4",...]
    output:
      type: array
      items:
        clause: string
        core_obligation: string
        binding_verb: string
        exact_excerpt: string
        source_lines: integer_range
    error_handling:
      MissingClause:
        code: "missing_clause"
        message: "clause not found in source"
        example: { clause: "<id>", status: "missing", note: "not found in source" }
      AmbiguousMatch:
        code: "ambiguous_match"
        message: "multiple candidate excerpts"
        details: [{ excerpt: string, confidence: number }]

  - name: summarize_policy
    description: Produce a compliant summary that preserves clause semantics and multi-condition obligations; include clause ids and source references.
    input:
      type: object
      schema:
        inventory: as-returned-by-extract_clause_inventory
        style: enum["concise","detailed"]  # optional
    output:
      type: object
      schema:
        summary_text: string
        clause_map:
          - clause: string
            summary_excerpt: string
            source_lines: integer_range
        flags:
          - clause: string
            reason: string  # e.g., verbatim quote required
            verbatim_excerpt: string (optional)
    error_handling:
      LossySummaryDetected:
        code: "lossy_summary_detected"
        message: "some clauses cannot be summarised without meaning loss; verbatim excerpts provided"
        flags: [{ clause: string, reason: string, verbatim_excerpt: string }]
      InvalidInput:
        code: "invalid_input"
        message: "input does not match expected schema"

  - name: validate_summary
    description: Validate a generated summary against enforcement rules (presence, condition preservation, no additions).
    input:
      type: object
      schema:
        original_sections: as-returned-by-retrieve_policy
        summary: as-returned-by-summarize_policy
        enforcement_rules: optional array[string]
    output:
      type: object
      schema:
        overall_pass: boolean
        checks:
          clause_presence:
            - clause: string
              present: boolean
          condition_preservation:
            - clause: string
              preserved: boolean
              missing_conditions: array[string]
          no_additions:
            - clause: string
              added_info: array[string]
        report: string  # human-readable diagnostics
    error_handling:
      UnableToValidate:
        code: "unable_to_validate"
        message: "missing inputs or mismatches"
        diagnostics: "<details>"

  - name: generate_agents
    description: Produce `agents.md` describing agent roles, prompts, enforcement rules and required checks for automated summarisation.
    input:
      type: object
      schema:
        inventory: as-returned-by-extract_clause_inventory
        validation_policy: object  # rules to embed
        output_targets: array[string]  # e.g., ["uc-0b/summary_hr_leave.txt","uc-0b/clause_inventory.md"]
    output:
      type: object
      schema:
        agents_md: string
        prompts:
          - agent_name: string
            prompt_template: string
        required_checks: array[string]
    error_handling:
      MissingInventory:
        code: "missing_inventory"
        message: "inventory required"
        fallback: "generate template agents.md with TODO markers"

  - name: format_output
    description: Serialize outputs to disk in required formats and return file paths and success status.
    input:
      type: object
      schema:
        outputs: object  # map<filename, content>
        out_dir: string
        overwrite: boolean
    output:
      type: object
      schema:
        written:
          - path: string
            bytes: integer
        failed:
          - path: string
            reason: string
    error_handling:
      PermissionDenied:
        code: "permission_denied"
        message: "check file permissions or run with elevated rights"
      Conflict:
        code: "conflict"
        message: "file exists and overwrite=false"

notes:
  - Preserve verbatim excerpts when a clause cannot be summarised without meaning loss.
  - Include clause identifiers and source line references for every extracted excerpt.
  - Use plain UTF-8 text for all outputs.
  - Ensure outputs are machine-parseable (consistent keys: clause, core_obligation, binding_verb, exact_excerpt, source_lines).
