# agents.md — UC-MCP MCP Server

role: >
  MCP (Model Context Protocol) Tool Server for the City Municipal Corporation.
  Operates as the transport and tool-discovery layer between AI agents and the
  CMC policy RAG server. Exposes exactly one tool — query_policy_documents —
  via JSON-RPC 2.0 over plain HTTP. The server does not perform its own LLM
  calls or document retrieval; it delegates entirely to the RAG server.

intent: >
  To expose the CMC policy RAG server as a discoverable, scoped MCP tool that
  any JSON-RPC-compliant agent can call. A correctly implemented server returns:
  (1) a tools/list response with an unambiguous, scope-stating tool description,
  (2) a tools/call response with content array and isError flag on every call,
  and (3) a JSON-RPC error object for unknown methods — always with HTTP 200.

context: >
  The server has access only to the RAG server query function (stub_rag.query
  or rag_server.query). It must not perform its own document lookups, LLM calls,
  or knowledge synthesis. All answers originate from the RAG layer.

enforcement:
  - "The tool description for query_policy_documents must state the exact document scope: CMC HR Leave Policy (HR-POL-001), IT Acceptable Use Policy, and Finance Reimbursement Policy only. A description that omits the scope is a violation — the agent will call it for out-of-scope questions."
  - "The tool description must explicitly state what the tool refuses: questions outside the three named CMC policy documents will return a refusal, not an answer. This prevents wasted agent tool calls."
  - "The inputSchema for query_policy_documents must declare 'question' as the only required property of type string — an empty or missing question must return isError: true before reaching the RAG server."
  - "All failed tool calls — RAG refusals, exceptions, missing arguments — must return isError: true with a non-empty content array containing the error or refusal message. An empty content array on failure is a protocol violation."
  - "The server must return HTTP 200 for all JSON-RPC responses including application errors. HTTP 4xx/5xx is reserved for transport-level failures only. Unknown JSON-RPC methods must return error code -32601 with HTTP 200."
