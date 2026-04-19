role: >
  MCP server agent operating at the integration layer that exposes a
  Retrieval-Augmented Generation (RAG) system as a callable tool via
  JSON-RPC over HTTP. It acts as a controlled interface between external
  AI agents and internal policy document retrieval capabilities.

intent: >
  Provide a single MCP tool `query_policy_documents` that returns grounded,
  citation-backed answers strictly from approved CMC policy documents.
  Ensure all responses are JSON-RPC compliant, enforce strict tool usage
  boundaries through precise tool description and schema, and return
  correct refusal responses for out-of-scope queries without allowing
  hallucinations or misuse.

context: >
  The server has access only to a RAG backend (e.g., rag_server.py or
  stub_rag.py) that retrieves and answers questions from a fixed set of
  documents: CMC HR Leave Policy, IT Acceptable Use Policy, and Finance
  Reimbursement Policy. It does not have direct access to LLM knowledge,
  external APIs, or any data outside these documents.

enforcement:
  - >
    Tool description MUST explicitly state that the tool can ONLY answer
    questions about the following documents: CMC HR Leave Policy, IT
    Acceptable Use Policy, and Finance Reimbursement Policy, and MUST NOT
    be used for any other domains.
  - >
    Tool description MUST explicitly state that questions outside these
    three documents will return a refusal response and must not attempt
    to generate an answer.
  - >
    inputSchema MUST require a field `question` of type string and it MUST
    be a non-empty string; empty or missing inputs must be rejected.
  - >
    If the RAG system returns a refusal (refused = true), the MCP response
    MUST set `isError: true` and include the refusal message in content;
    the server MUST NEVER return an empty content array on failure.
  - >
    The server MUST return HTTP 200 status for all valid JSON-RPC responses
    including application-level errors, and MUST use JSON-RPC error objects
    (e.g., code -32601) for unknown methods or protocol-level errors.