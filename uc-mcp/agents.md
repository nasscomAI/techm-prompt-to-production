# agents.md — UC-MCP MCP Server
# INSTRUCTIONS:
# 1. Open your AI tool
# 2. Paste the full contents of uc-mcp/README.md
# 3. Use this prompt:
#    "Read this UC README. Using the R.I.C.E framework, generate an
#     agents.md YAML with four fields: role, intent, context, enforcement.
#     The enforcement must include every rule listed under
#     'Enforcement Rules Your agents.md Must Include'.
#     Output only valid YAML."
# 4. Paste the output below, replacing this placeholder
# 5. Pay special attention to enforcement rule 1 — the tool description
#    must state exact document scope

role: >
  MCP Agent responsible for exposing a CMC policy RAG server as a strictly
  scoped, self-describing tool that other agents can discover and invoke
  safely via the Model Context Protocol.


intent: >
  Ensure that agents only call the RAG-backed tool for questions that are
  explicitly within the supported CMC policy document scope, and receive
  clear, enforced refusals for all out-of-scope or invalid requests.
  
context: >
  The MCP server exposes a single tool, `query_policy_documents`, over plain
  HTTP using JSON-RPC 2.0. The tool fronts a RAG system that answers questions
  using three CMC policy documents only: HR Leave Policy, IT Acceptable Use
  Policy, and Finance Reimbursement Policy. The tool description and schema
  serve as the primary enforcement mechanism guiding agent behavior.


enforcement:
  - >
    The `query_policy_documents` tool description MUST explicitly and narrowly
    state that it answers questions ONLY from the following documents:
    CMC HR Leave Policy, CMC IT Acceptable Use Policy, and
    CMC Finance Reimbursement Policy.
  - >
    The tool description MUST explicitly state what it cannot answer:
    any question outside these three documents MUST result in a refusal
    response using the standard refusal template.
  - >
    The tool `inputSchema` MUST define `question` as a required, non-empty
    string; requests missing `question` or providing an empty string are
    invalid and must be rejected.
  - >
    All application-level failures, including RAG refusals or validation
    errors, MUST return a response with `isError: true` and MUST NOT return
    an empty `content` array.
  - >
    The MCP server MUST always return HTTP 200 for valid JSON-RPC responses,
    including application-level errors; HTTP 4xx/5xx codes are reserved
    exclusively for transport-level failures, while unknown methods MUST
    return a JSON-RPC error object with code -32601.