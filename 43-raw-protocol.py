import getpass
import json
import os
import sys
from typing import Any, Dict, Optional

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser


class RawMCPServer:
    """Minimal MCP server implementation using raw JSON-RPC"""

    def __init__(self, name: str = "RawMCPDemo"):
        """Initialize the server with name and basic capabilities"""
        self.name = name
        self.initialized = False
        self.tools = self._create_demo_tools()
        self.resources = self._create_demo_resources()
        self.protocol_version = "2023-08-01"

    def _create_demo_tools(self) -> Dict[str, Dict[str, Any]]:
        """Create demo tools for testing"""
        return {
            "echo": {
                "name": "echo",
                "description": "Echo a message back",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                    "required": ["message"],
                },
            },
            "add": {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["a", "b"],
                },
            },
        }

    def _create_demo_resources(self) -> Dict[str, str]:
        """Create demo resources for testing"""
        return {
            "raw://hello": "Hello from raw MCP implementation!",
            "raw://data.json": json.dumps(
                {
                    "name": "Raw MCP Demo",
                    "description": "Demonstration of MCP protocol without SDK abstraction",
                    "version": "1.0.0",
                }
            ),
        }

    def handle_request(self, request_str: str) -> Optional[str]:
        """Process an incoming JSON-RPC request and return a response"""
        try:
            # Log the raw request for debugging
            sys.stderr.write(f"\n>>> RECEIVED: {request_str}\n")

            # Parse the request
            request = json.loads(request_str)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            # Only respond to requests with ID (ignore notifications)
            if request_id is None:
                sys.stderr.write(">>> NOTIFICATION (no response required)\n")
                return None

            # Dispatch based on method
            if method == "initialize":
                response = self._handle_initialize(request_id, params)
            elif method == "initialized":
                # Notification, no response needed
                return None
            elif method == "shutdown":
                response = self._handle_shutdown(request_id)
            elif method == "tools/list":
                response = self._handle_tools_list(request_id)
            elif method == "tools/call":
                response = self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                response = self._handle_resources_list(request_id)
            elif method == "resources/read":
                response = self._handle_resources_read(request_id, params)
            else:
                response = self._create_error(
                    request_id, -32601, f"Method not found: {method}"
                )

            # Log the response
            sys.stderr.write(f"<<< SENDING: {response}\n")
            return response

        except json.JSONDecodeError as e:
            error = self._create_error(None, -32700, f"Invalid JSON: {str(e)}")
            sys.stderr.write(f"<<< ERROR: {error}\n")
            return error
        except Exception as e:
            error = self._create_error(
                request_id if "request_id" in locals() else None,
                -32000,
                f"Internal error: {str(e)}",
            )
            sys.stderr.write(f"<<< ERROR: {error}\n")
            return error

    def _handle_initialize(self, request_id: Any, params: Dict[str, Any]) -> str:
        """Handle initialization request with capability negotiation"""
        # Extract client capabilities
        client_caps = params.get("capabilities", {})
        client_name = client_caps.get("client", {}).get("name", "Unknown Client")

        sys.stderr.write(f">>> Initializing with client: {client_name}\n")
        self.initialized = True

        # Create server capabilities
        capabilities = {
            "protocolVersion": self.protocol_version,
            "server": {"name": self.name, "version": "1.0.0"},
            "features": {
                "tools": {"supported": True},
                "resources": {"supported": True},
                "prompts": {"supported": False},
                "sampling": {"supported": False},
            },
        }

        return self._create_response(request_id, {"capabilities": capabilities})

    def _handle_shutdown(self, request_id: Any) -> str:
        """Handle shutdown request"""
        sys.stderr.write(">>> Shutting down\n")
        self.initialized = False
        return self._create_response(request_id, {})

    def _handle_tools_list(self, request_id: Any) -> str:
        """Handle tools/list request"""
        if not self.initialized:
            return self._create_error(request_id, -32000, "Server not initialized")

        tool_list = list(self.tools.values())
        return self._create_response(request_id, {"tools": tool_list})

    def _handle_tools_call(self, request_id: Any, params: Dict[str, Any]) -> str:
        """Handle tools/call request"""
        if not self.initialized:
            return self._create_error(request_id, -32000, "Server not initialized")

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return self._create_error(
                request_id, -32601, f"Tool not found: {tool_name}"
            )

        # Execute the tool
        if tool_name == "echo":
            message = arguments.get("message", "")
            result = message
        elif tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            result = a + b
        else:
            return self._create_error(
                request_id, -32000, f"Tool implementation missing: {tool_name}"
            )

        return self._create_response(request_id, {"result": result})

    def _handle_resources_list(self, request_id: Any) -> str:
        """Handle resources/list request"""
        if not self.initialized:
            return self._create_error(request_id, -32000, "Server not initialized")

        resources = []
        for uri in self.resources.keys():
            resources.append(
                {
                    "uri": uri,
                    "mimeType": "application/json"
                    if uri.endswith(".json")
                    else "text/plain",
                }
            )

        return self._create_response(request_id, {"resources": resources})

    def _handle_resources_read(self, request_id: Any, params: Dict[str, Any]) -> str:
        """Handle resources/read request"""
        if not self.initialized:
            return self._create_error(request_id, -32000, "Server not initialized")

        uri = params.get("uri")
        if uri not in self.resources:
            return self._create_error(request_id, -32601, f"Resource not found: {uri}")

        content = self.resources[uri]
        mime_type = "application/json" if uri.endswith(".json") else "text/plain"

        return self._create_response(
            request_id,
            {"content": {"uri": uri, "mimeType": mime_type, "text": content}},
        )

    def _create_response(self, request_id: Any, result: Dict[str, Any]) -> str:
        """Create a JSON-RPC response"""
        return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

    def _create_error(self, request_id: Any, code: int, message: str) -> str:
        """Create a JSON-RPC error response"""
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )

    def run(self) -> None:
        """Run the server, processing input from stdin"""
        sys.stderr.write(f"Raw MCP Server '{self.name}' starting...\n")
        sys.stderr.write(
            "This demonstrates the JSON-RPC protocol without SDK abstractions\n"
        )

        buffer = ""
        content_length = None

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.rstrip()

                # Content-Length header format
                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":")[1].strip())
                elif line == "" and content_length is not None:
                    # Empty line after header, now read the JSON content
                    content = sys.stdin.read(content_length)
                    response = self.handle_request(content)

                    if response:
                        # Send the response with proper headers
                        sys.stdout.write(f"Content-Length: {len(response)}\r\n\r\n")
                        sys.stdout.write(response)
                        sys.stdout.flush()

                    # Reset for next message
                    content_length = None

            except Exception as e:
                sys.stderr.write(f"Error: {str(e)}\n")
                # Try to continue processing


# Example usage
if __name__ == "__main__":
    server = RawMCPServer()
    server.run()
else:
    # When imported through MCP CLI, explain what this example does
    sys.stderr.write("\n=== RAW MCP PROTOCOL IMPLEMENTATION ===\n")
    sys.stderr.write("This example demonstrates a minimal MCP server implementation\n")
    sys.stderr.write("using raw JSON-RPC without any SDK abstractions.\n\n")
    sys.stderr.write("IMPORTANT: This server cannot be run with the MCP CLI as it \n")
    sys.stderr.write("implements the protocol directly. To run manually:\n\n")
    sys.stderr.write("  python 43-raw-protocol.py\n\n")
    sys.stderr.write("This will demonstrate the raw JSON-RPC messages between\n")
    sys.stderr.write("client and server, with minimal abstraction layers.\n")
    sys.stderr.write("=== END RAW PROTOCOL INFO ===\n\n")

# This server demonstrates the raw MCP protocol using JSON-RPC
# To run manually: python 43-raw-protocol.py
