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
  An MCP (Model Context Protocol) server that acts as a standardized communication layer, 
  exposing municipal policy retrieval capabilities as discoverable tools for AI agents.

intent: >
  Provide a JSON-RPC 2.0 compliant interface that correctly describes the 
  'query_policy_documents' tool, its exact scope, and its input schema, while 
  ensuring all tool calls return structured responses or standardized error codes.

context: >
  The server operates within the uc-mcp directory and has access to the 
  rag_server.py (UC-RAG) logic. It does not have access to general knowledge 
  and must rely solely on the output of the RAG pipeline.

enforcement:
  - "The tool description must explicitly state the document scope: CMC HR Leave Policy, IT Acceptable Use Policy, and Finance Reimbursement Policy."
  - "The description must explicitly state that questions outside these three documents will return a refusal template."
  - "The inputSchema must strictly require 'question' as a non-empty string."
  - "Standard JSON-RPC 2.0 error objects must be used for unknown methods (-32601) or malformed requests."
  - "Application-level refusals must use 'isError: true' in the tool response content, but the HTTP transport layer must still return 200 OK."
