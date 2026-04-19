skills:
  - name: query_policy_documents
    description: >
      Retrieves grounded answers strictly from CMC policy documents:
      HR Leave Policy, IT Acceptable Use Policy, and Finance Reimbursement Policy.
      This skill must only be used for questions within this defined scope and
      returns answers with supporting citations via the RAG system.
    input: >
      question (string): A non-empty question strictly related to the allowed
      CMC policy documents.
    output: >
      MCP-compliant response object containing:
      - content: an array with at least one item of type "text" containing the answer and cited sources
      - isError: boolean (false for valid answers, true for refusals or failures)
    error_handling: >
      If the RAG system returns refused = true (question is out of scope),
      return a response with content containing the refusal message and
      set isError: true. Never return an empty content array.
      If an internal exception occurs, return a safe error message in content
      with isError: true. The tool must not attempt to answer questions outside
      the defined document scope, preventing misuse caused by vague tool descriptions.

  - name: serve_mcp
    description: >
      Runs an MCP-compliant HTTP server that exposes tools via JSON-RPC 2.0.
      Supports method discovery (tools/list) and tool invocation (tools/call),
      enabling external agents to safely interact with the RAG-backed tool.
    input: >
      HTTP POST requests containing a JSON-RPC 2.0 body with fields:
      - jsonrpc: "2.0"
      - method: "tools/list" or "tools/call"
      - id: request identifier
      - params (for tools/call): tool name and arguments
    output: >
      JSON-RPC 2.0 response object with:
      - jsonrpc: "2.0"
      - id: matching request id
      - result OR error
      Always returned with HTTP 200 status for valid JSON-RPC handling.
    error_handling: >
      Unknown method must return JSON-RPC error with code -32601 (Method not found).
      Malformed JSON or invalid request must return JSON-RPC error with code -32700 (Parse error).
      Application-level failures must be returned in result with isError: true,
      not via HTTP status codes. Ensures strict protocol compliance and prevents
      ambiguity in agent-tool interactions.