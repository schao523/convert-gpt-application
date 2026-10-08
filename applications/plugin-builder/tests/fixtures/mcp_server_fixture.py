from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import time


def result(identifier, payload):
    return {"jsonrpc": "2.0", "id": identifier, "result": payload}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        return

    def do_POST(self):
        length = int(self.headers.get("content-length", "0"))
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        mode = self.server.mode
        if mode == "hang":
            time.sleep(10)
            return
        if mode == "malformed":
            body = b"not-json"
        else:
            method = request.get("method")
            if method == "initialize":
                payload = result(request.get("id"), {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fixture", "version": "1"},
                })
            elif method == "tools/list":
                name = "wrong-tool" if mode == "wrong-tool" else "normalize-input"
                payload = result(request.get("id"), {"tools": [{
                    "name": name,
                    "inputSchema": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                }]})
            elif method == "tools/call":
                arguments = ((request.get("params") or {}).get("arguments") or {})
                if not isinstance(arguments.get("text"), str):
                    payload = result(request.get("id"), {
                        "content": [{"type": "text", "text": "invalid input"}],
                        "isError": True,
                    })
                else:
                    output = {"normalized": arguments["text"].strip()}
                    payload = result(request.get("id"), {
                        "content": [{"type": "text", "text": json.dumps(output, sort_keys=True)}],
                        "structuredContent": output,
                        "isError": False,
                    })
            else:
                payload = {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32601, "message": "unknown"}}
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()
        self.wfile.write(f"{len(body):x}\r\n".encode("ascii") + body + b"\r\n0\r\n\r\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--mode", default="normal")
    args = parser.parse_args()
    if args.mode == "startup-fail":
        raise SystemExit(9)
    if args.mode == "premature-exit":
        return
    if os.environ.get("PYTHONUTF8") != "1" or os.environ.get("PYTHONIOENCODING") != "utf-8":
        raise SystemExit(11)
    if os.environ.get("MCP_TEST_LEAK") is not None:
        raise SystemExit(12)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.mode = args.mode
    server.serve_forever()


if __name__ == "__main__":
    main()
