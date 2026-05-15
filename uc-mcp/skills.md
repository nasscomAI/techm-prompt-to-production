# skills.md — UC-MCP MCP Server

skills:
  - name: query_policy_documents
    description: Accepts a natural-language question, forwards it to the CMC RAG server, and returns the answer with source citations formatted as an MCP content response. Covers CMC HR Leave Policy, IT Acceptable Use Policy, and Finance Reimbursement Policy only.
    input: String question — a non-empty natural-language policy question from an agent.
    output: Dict with keys 'content' (list of dicts with 'type' and 'text') and 'isError' (bool). On success, content[0].text contains the answer with citations. On refusal or error, isError is true and content[0].text contains the refusal or error message.
    error_handling: If the RAG server returns refused=True, return isError=true with the refusal message as content. If the RAG server raises any exception, catch it, return isError=true with the exception message — never let an exception propagate as an HTTP 500. If question is empty or missing, return isError=true without calling the RAG server.

  - name: serve_mcp
    description: Starts a plain HTTP server on the configured port that handles JSON-RPC 2.0 POST requests, dispatching tools/list and tools/call methods and returning compliant responses for all cases including errors.
    input: HTTP POST request with Content-Type application/json and a JSON-RPC 2.0 body (jsonrpc, method, id, optional params).
    output: HTTP 200 response with JSON-RPC 2.0 body — result for known methods, error object for unknown methods or malformed requests.
    error_handling: Unknown method → JSON-RPC error object with code -32601 and message 'Method not found', HTTP 200. Malformed JSON body → JSON-RPC error code -32700 'Parse error', HTTP 200. Missing or unknown tool name in tools/call → isError true content response, HTTP 200.
