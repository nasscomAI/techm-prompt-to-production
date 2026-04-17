# agents.md — UC-MCP MCP Server

role: >
  MCP server agent that exposes a policy document retrieval tool for agents. Operates at the tool-serving layer — receives JSON-RPC requests, dispatches to RAG server, returns formatted responses. Does not call LLM directly; delegates to rag_query.

intent: >
  Produce a JSON-RPC 2.0 compliant MCP server that exposes `query_policy_documents` as a callable tool with precise scope documentation. Each response must include MCP content format with isError flag set appropriately. Tool description must enforce scope boundaries so calling agents understand what questions are in/out of scope.

context: >
  Server has access to: RAG server query results (chunks, relevance scores, refusal flags). Does NOT have: direct LLM calls (uses llm_adapter as fallback), outside knowledge beyond policy documents, authority to modify tool scope.

enforcement:
  - "Tool description must explicitly state scope: 'Answers questions about CMC HR Leave Policy, IT Acceptable Use Policy, and Finance Reimbursement Policy only.'"
  - "Tool description must state refusal behavior: 'Returns a refusal message for questions outside these three documents.'"
  - "inputSchema must have required: ['question'] with question as type string (non-empty enforced by prompt)"
  - "All error responses must set isError: true; never return empty content array on failure"
  - "HTTP response code must be 200 for all JSON-RPC responses including error objects; only 4xx/5xx for transport errors"
