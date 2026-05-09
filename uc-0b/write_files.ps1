# Create target directory, write skills.md and agents.md as UTF-8
$dir = 'D:\code_sarathi\techm-prompt-to-production\uc-0b'
New-Item -ItemType Directory -Path $dir -Force | Out-Null

$skills = @'
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
'@

$agents = @'
# agents.md — UC-0B: Policy summarisation agents

## Purpose
Define agents, prompts and mandatory checks for automated, enforceable summarisation of policy documents. Agents operate in a pipeline: Retriever → Extractor → Summariser → Validator → Formatter.

## Agents and responsibilities
- Retriever
  - Role: Read policy file from disk and return structured sections with line ranges.
  - Output: `sections` (clause_id, title, lines, text)
  - Prompt template:
    "Load file at `{path}`. Return a JSON array of numbered sections with `clause_id`, `title`, `lines` (start-end), and `text`. If parsing fails, return ParseFailure with raw_text."

- Extractor
  - Role: Build clause inventory for priority clauses.
  - Output: array of inventory entries: `clause`, `core_obligation`, `binding_verb`, `exact_excerpt`, `source_lines`
  - Prompt template:
    "Given `sections` and `priority_clauses`, extract each clause's exact excerpt, identify the core obligation (concise), and the binding verb. Preserve punctuation and line refs."

- Summariser
  - Role: Produce compliant summary preserving all conditions and clause identifiers.
  - Output: `summary_text`, `clause_map`, `flags`
  - Prompt template:
    "Using the inventory, produce a summary preserving every clause id and all conditions. If summarisation causes meaning loss for any clause, quote that clause verbatim and set a flag explaining why."

- Validator
  - Role: Apply enforcement rules and return pass/fail diagnostics.
  - Required checks:
    1. Every numbered clause in `priority_clauses` is present in summary.
    2. Multi-condition obligations preserve ALL conditions (no silent drops).
    3. No information added beyond the source.
    4. If clause cannot be summarised without meaning loss, it must be quoted verbatim and flagged.
  - Output: `overall_pass`, `checks`, `report`
  - Prompt template:
    "Compare `original_sections` to `summary`. For each clause check presence, condition preservation, and additions. Return structured diagnostics and a human-readable report."

- Formatter
  - Role: Write outputs to files specified in `output_targets` and return write status.
  - Behavior: Respect `overwrite` flag, produce UTF-8 files, include source line refs in outputs.

## Enforcement rules (embed in all prompts)
- Do not add any information not present in the source.
- Preserve all conditions and required approvers exactly as written.
- When unsure, quote the original clause verbatim and mark a flag.
- Always include clause identifier and source line references.

## Required checks (automated)
- Clause presence check: every clause id in inventory must exist in summary.
- Condition preservation check: identify predicates/conditions (AND/OR) and ensure none are omitted.
- Approver preservation check: multi-approver requirements (e.g., "Department Head AND HR Director") must remain conjunctive.
- No-addition check: detect phrases in summary not present in source.
- Verbatim fallback: ensure flagged clauses include exact excerpt and reason.

## Output targets (examples)
- `uc-0b/clause_inventory.md`
- `uc-0b/summary_hr_leave.txt`
- `uc-0b/validation_report.json`

## Run sequence (example)
1. Retriever -> returns `sections`
2. Extractor -> returns `inventory`
3. Summariser -> returns `summary` (+ flags if any)
4. Validator -> returns `validation_report`
5. Formatter -> writes files listed in `output_targets`

## Prompts (templates)
- Retriever prompt: see Retriever section.
- Extractor prompt: see Extractor section.
- Summariser prompt: see Summariser section.
- Validator prompt: see Validator section.
- Formatter prompt: "Serialize provided outputs to disk under `{out_dir}`. Respect `overwrite`."

## Notes
- All agents must attach source line ranges to any excerpt or summary sentence that references source text.
- Maintain machine-parseable output (JSON or YAML) for validator and extractor outputs to enable automated checks.
'@

$skillsPath = Join-Path $dir 'skills.md'
$agentsPath = Join-Path $dir 'agents.md'

$skills | Out-File -FilePath $skillsPath -Encoding UTF8 -Force
$agents | Out-File -FilePath $agentsPath -Encoding UTF8 -Force

Write-Host "Wrote files:"
Write-Host " - $skillsPath"
Write-Host " - $agentsPath"