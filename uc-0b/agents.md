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
- Maintain machine-parseable output (JSON or YAML) for validator and extractor outputs to enable automated checks
