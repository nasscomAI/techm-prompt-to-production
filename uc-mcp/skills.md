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
      Queries the CMC policy documents (HR Leave, IT Acceptable Use, Finance Reimbursement). 
      Returns a grounded answer with citations or a standard refusal if out of scope.
    input: "question (non-empty string)"
    output: "A content array containing the answer text and an 'isError' boolean flag."
    error_handling: >
      If the RAG server returns a refusal/not-covered response, return the refusal 
      message with 'isError: true'. Catch and wrap any internal exceptions as JSON-RPC errors.

  - name: serve_mcp
    description: >
      Starts a plain HTTP server (default port 8765) that handles MCP-compliant 
      JSON-RPC 2.0 requests for tool listing and tool invocation.
    input: "HTTP POST request with a JSON-RPC 2.0 body (tools/list or tools/call)."
    output: "JSON-RPC 2.0 response object with 'result' or 'error' fields."
    error_handling: >
      Unknown methods must return JSON-RPC error code -32601. 
      Invalid JSON must return -32700. All responses must be sent with HTTP 200 OK.
