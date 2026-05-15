"""
UC-MCP — mcp_server.py
Plain HTTP MCP Server implementing JSON-RPC 2.0.

Protocol: JSON-RPC 2.0 over HTTP POST
No external dependencies beyond Python stdlib.

Run:  python3 mcp_server.py --port 8765
Test: python3 test_client.py --port 8765
"""

import json
import argparse
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import RAG — uses stub by default, swap to rag_server once yours works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uc-rag"))
try:
    from rag_server import query as rag_query
    print("[mcp_server] Using rag_server.py")
except (ImportError, NotImplementedError):
    from stub_rag import query as rag_query
    print("[mcp_server] Using stub_rag.py (fallback)")

from llm_adapter import call_llm


# ── TOOL DEFINITION ───────────────────────────────────────────────────────────
# The description IS the enforcement — precisely scoped to prevent out-of-scope calls.
TOOL_DEFINITION = {
    "name": "query_policy_documents",
    "description": (
        "Answers questions about CMC (City Municipal Corporation) policy documents only. "
        "Covers three documents: HR Leave Policy (HR-POL-001), IT Acceptable Use Policy, "
        "and Finance Reimbursement Policy. Returns answers grounded in retrieved document "
        "chunks with citations (source document name and chunk index). "
        "Returns a refusal for questions outside these three documents — do NOT call this "
        "tool for budget forecasts, ward data, complaint classification, or any topic not "
        "covered by the three named CMC policy documents."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": (
                    "A natural-language question about CMC HR, IT, or Finance policy. "
                    "Must be a non-empty string."
                ),
            }
        },
        "required": ["question"],
    },
}


# ── SKILL: query_policy_documents ─────────────────────────────────────────────
def query_policy_documents(question: str) -> dict:
    """
    Call the RAG server with the provided question to query policy documents.
    
    Args:
        question (str): The user's question about CMC policy documents.
        
    Returns:
        dict: A dictionary conforming to the MCP content format, containing 
              a 'content' array and an 'isError' boolean flag.
              
    Enforcement:
    - Empty/missing question → isError: True (never reach RAG)
    - RAG refused (no chunks above threshold) → isError: True
    - RAG exception → isError: True with error message
    """
    # Validate input
    if not question or not question.strip():
        return {
            "content": [{"type": "text", "text": "ERROR: question must be a non-empty string."}],
            "isError": True,
        }

    try:
        result = rag_query(question, llm_call=call_llm)
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"RAG server error: {e}"}],
            "isError": True,
        }

    if result.get("refused"):
        return {
            "content": [{"type": "text", "text": result["answer"]}],
            "isError": True,
        }

    # Build citation footer
    cited = result.get("cited_chunks", [])
    citations = ""
    if cited:
        citations = "\n\nSources: " + ", ".join(
            f"[{c['doc_name']}, chunk {c['chunk_index']}, score={c['score']}]"
            for c in cited
        )

    return {
        "content": [{"type": "text", "text": result["answer"] + citations}],
        "isError": False,
    }


# ── JSON-RPC HELPERS ──────────────────────────────────────────────────────────
def _jsonrpc_result(req_id, result: dict) -> dict:
    """
    Construct a successful JSON-RPC 2.0 result response.
    
    Args:
        req_id: The ID of the original request.
        result (dict): The result data to include in the response.
        
    Returns:
        dict: A properly formatted JSON-RPC success response dictionary.
    """
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _jsonrpc_error(req_id, code: int, message: str) -> dict:
    """
    Construct a JSON-RPC 2.0 error response.
    
    Args:
        req_id: The ID of the original request.
        code (int): The JSON-RPC error code.
        message (str): The error message.
        
    Returns:
        dict: A properly formatted JSON-RPC error response dictionary.
    """
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


# ── SKILL: serve_mcp (MCPHandler) ─────────────────────────────────────────────
class MCPHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler implementing JSON-RPC 2.0.
    Always returns HTTP 200 — JSON-RPC errors are in the response body.
    """

    def do_POST(self):
        """
        Handle incoming HTTP POST requests containing JSON-RPC payloads.
        
        Parses the JSON payload, dispatches to the requested method, and 
        returns the appropriate JSON-RPC response via HTTP 200.
        """
        # Read body
        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length)

        # Parse JSON
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            response = _jsonrpc_error(None, -32700, f"Parse error: {e}")
            self._send(response)
            return

        req_id = body.get("id")
        method = body.get("method", "")

        # Dispatch
        if method == "tools/list":
            response = _jsonrpc_result(req_id, {"tools": [TOOL_DEFINITION]})

        elif method == "tools/call":
            params    = body.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            if tool_name != "query_policy_documents":
                # Unknown tool — treat as application-level error content
                response = _jsonrpc_result(req_id, {
                    "content": [{"type": "text",
                                 "text": f"Unknown tool: '{tool_name}'. "
                                         f"Available tools: query_policy_documents"}],
                    "isError": True,
                })
            else:
                question = arguments.get("question", "")
                content_response = query_policy_documents(question)
                response = _jsonrpc_result(req_id, content_response)

        else:
            # Unknown JSON-RPC method → error -32601
            response = _jsonrpc_error(req_id, -32601, f"Method not found: '{method}'")

        self._send(response)

    def _send(self, response: dict):
        """
        Send the finalized JSON-RPC response with an HTTP 200 status code.
        
        Args:
            response (dict): The complete JSON-RPC response dictionary to serialize and send.
        """
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """
        Override the default HTTP server logging to use a custom prefix format.
        
        Args:
            format: The log message format string.
            *args: Additional arguments to format.
        """
        print(f"[mcp_server] {args[0]} {args[1]}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    """
    Main entry point for the MCP server.
    
    Parses command-line arguments, checks for a valid RAG index, and 
    starts the HTTP server on the specified port to listen for requests.
    """
    parser = argparse.ArgumentParser(description="UC-MCP Plain HTTP MCP Server")
    parser.add_argument("--port", type=int, default=8765,
                        help="Port to listen on (default: 8765)")
    args = parser.parse_args()

    # Warn if RAG index not found
    stub_db  = os.path.join(os.path.dirname(__file__), "../uc-rag/stub_chroma_db")
    own_db   = os.path.join(os.path.dirname(__file__), "../uc-rag/chroma_db")
    if not os.path.exists(stub_db) and not os.path.exists(own_db):
        print("[mcp_server] WARNING: No RAG index found.")
        print("[mcp_server] Build stub index: python3 ../uc-rag/stub_rag.py --build-index")
        print("[mcp_server] Starting anyway — queries will fail until index is built.")

    server = HTTPServer(("localhost", args.port), MCPHandler)
    print(f"[mcp_server] MCP server running on http://localhost:{args.port}")
    print(f"[mcp_server] Test with: python3 test_client.py --port {args.port}")
    print(f"[mcp_server] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[mcp_server] Stopped.")


if __name__ == "__main__":
    main()
