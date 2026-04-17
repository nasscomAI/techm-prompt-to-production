# skills.md — UC-MCP MCP Server

skills:
  - name: query_policy_documents
    description: Query the RAG server with a policy question and return MCP-formatted response with answer + sources or refusal.
    input: question (string, non-empty). The policy question to answer from CMC HR Leave, IT Acceptable Use, or Finance Reimbursement policies.
    output: dict with keys {content, isError}. content is array of text chunks with sources. isError is boolean — true if RAG refused or raised exception, false on success.
    error_handling: If RAG returns refused=True or raises exception, set isError=true and populate content with refusal message. Never return empty content array.

  - name: serve_mcp
    description: Start HTTP server listening for JSON-RPC 2.0 POST requests and dispatch to tools/list or tools/call.
    input: HTTP POST request with JSON-RPC 2.0 body. Methods: tools/list (no params), tools/call (params={name, arguments}).
    output: JSON-RPC 2.0 response with result or error object. Always HTTP 200 — errors are in JSON-RPC error field with code + message.
    error_handling: Unknown method → JSON-RPC error {code: -32601, message: "Method not found"}. Malformed JSON → {code: -32700, message: "Parse error"}. All responses HTTP 200.
