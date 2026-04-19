import json
import argparse
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import RAG
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uc-rag"))
try:
    from rag_server import query as rag_query
    print("[mcp_server] Using participant rag_server.py")
except (ImportError, NotImplementedError):
    from stub_rag import query as rag_query
    print("[mcp_server] Using stub_rag.py (fallback)")

# Import LLM adapter
from llm_adapter import call_llm


# ── TOOL DEFINITION ──────────────────────────────────────────────────────────
TOOL_DEFINITION = {
    "name": "query_policy_documents",
    "description": (
        "Use this tool ONLY to answer questions about the following CMC policy documents: "
        "HR Leave Policy, IT Acceptable Use Policy, and Finance Reimbursement Policy. "
        "It returns grounded answers with cited sources strictly based on retrieved document content. "
        "Do NOT use this tool for any other topics such as forecasts, strategy, or unrelated company data. "
        "Questions outside these documents will return a refusal response."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "A non-empty question about CMC HR, IT, or Finance policy documents"
            }
        },
        "required": ["question"]
    }
}


# ── SKILL: query_policy_documents ────────────────────────────────────────────
def query_policy_documents(question: str) -> dict:
    """
    Strict MCP behavior:
    - Trust RAG for refusal decisions
    - Do NOT override RAG logic
    """
    try:
        result = rag_query(question, llm_call=call_llm)

        answer = result.get("answer", "")
        sources = result.get("sources", [])
        refused = result.get("refused", True)

        # ✅ If RAG says refused → propagate as error
        if refused:
            return {
                "content": [{
                    "type": "text",
                    "text": answer or "I can only answer questions about CMC HR, IT, and Finance policies."
                }],
                "isError": True
            }

        # ✅ Valid answer
        answer_text = answer
        if sources:
            answer_text += "\nSources: " + ", ".join(sources)

        return {
            "content": [{
                "type": "text",
                "text": answer_text
            }],
            "isError": False
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Internal error: {str(e)}"
            }],
            "isError": True
        }


# ── MCP SERVER ───────────────────────────────────────────────────────────────
class MCPHandler(BaseHTTPRequestHandler):

    def _send_json(self, response_obj):
        self.send_response(200)  # ALWAYS HTTP 200
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_obj).encode("utf-8"))

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            # Parse JSON
            try:
                request = json.loads(raw_body)
            except json.JSONDecodeError:
                return self._send_json({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                })

            jsonrpc = request.get("jsonrpc")
            method = request.get("method")
            request_id = request.get("id")

            # Validate JSON-RPC version
            if jsonrpc != "2.0":
                return self._send_json({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    }
                })

            # ── tools/list ──
            if method == "tools/list":
                return self._send_json({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [TOOL_DEFINITION]
                    }
                })

            # ── tools/call ──
            elif method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})

                if name != "query_policy_documents":
                    return self._send_json({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": "Method not found"
                        }
                    })

                question = arguments.get("question")

                # Input validation
                if not isinstance(question, str) or not question.strip():
                    return self._send_json({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": "Invalid input: 'question' must be a non-empty string."
                            }],
                            "isError": True
                        }
                    })

                result = query_policy_documents(question.strip())

                return self._send_json({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                })

            # ── Unknown method ──
            else:
                return self._send_json({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                })

        except Exception as e:
            return self._send_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })

    def log_message(self, format, *args):
        print(f"[mcp_server] {args[0]} {args[1]}")


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="UC-MCP Plain HTTP MCP Server")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = HTTPServer(("localhost", args.port), MCPHandler)

    print(f"[mcp_server] MCP server running on http://localhost:{args.port}")
    print(f"[mcp_server] Test with: python3 test_client.py --port {args.port}")
    print("[mcp_server] Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[mcp_server] Stopped.")


if __name__ == "__main__":
    main()