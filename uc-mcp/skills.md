# skills.md — UC-MCP MCP Server
# INSTRUCTIONS:
# 1. Open your AI tool
# 2. Paste the full contents of uc-mcp/README.md
# 3. Use this prompt:
#    "Read this UC README. Generate a skills.md YAML defining the two
#     skills: query_policy_documents and serve_mcp. Each skill needs:
#     name, description, input, output, error_handling.
#     error_handling must address the failure mode in the README.
#     Output only valid YAML."
# 4. Paste the output below, replacing this placeholder

skills:
  - name: query_policy_documents
    description: >
    Answers natural-language questions strictly using the CMC HR Leave Policy,
    CMC IT Acceptable Use Policy, and CMC Finance Reimbursement Policy. This skill
    MUST NOT be used for questions outside these three documents.
    input: question: string (required, non-empty)
    output: >
    A text answer derived from the relevant policy document(s), including
    cited sources. Successful responses summarize only what is stated in
    the policies.
    error_handling: >
    If the underlying RAG system determines the question is out of scope or
    returns refused=true, the skill MUST return an application-level error
    with isError: true and a refusal message stating that the question is
    outside the supported policy documents. Empty responses are forbidden.

  - name: serve_mcp
    description: >
    Runs a plain HTTP MCP server that exposes available tools and executes
    tool calls using JSON-RPC 2.0. Handles tool discovery and invocation for
    query_policy_documents.
    input: port: integer (optional, default 8765)
    output: >
    JSON-RPC compliant responses over HTTP, including tools/list results
    and tools/call execution outputs.
    error_handling: >
    Unknown JSON-RPC methods MUST return a JSON-RPC error with code -32601
    (Method not found). All application-level errors MUST be encoded in
    JSON-RPC responses with HTTP 200 status. Transport or server failures
    may use HTTP 4xx/5xx. The server MUST never return an empty content array
    on failure.