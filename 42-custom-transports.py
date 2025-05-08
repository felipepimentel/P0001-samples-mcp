import asyncio
import getpass
import json
import logging
import os
import sys
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("custom-transports")

# Create the MCP server
mcp = FastMCP("CustomTransportDemo")

# Create the FastAPI application
app = FastAPI(title="MCP Custom Transports Demo")

# Store active WebSocket connections
websocket_connections = {}


# Basic MCP tools and resources for testing transports
@mcp.tool()
def echo(message: str) -> str:
    """Simple echo tool for testing"""
    logger.info(f"Echo tool called with message: {message}")
    return f"ECHO: {message}"


@mcp.tool()
def get_transport_info() -> Dict[str, Any]:
    """Get information about the current transport"""
    return {
        "available_transports": ["http", "websocket", "stdio"],
        "description": "This server demonstrates custom MCP transports using HTTP and WebSockets",
    }


@mcp.resource("demo://transport")
def get_transport_resource() -> str:
    """Resource providing transport information"""
    return json.dumps(
        {
            "name": "Custom Transport Demo",
            "description": "Demonstrates MCP over HTTP and WebSockets",
            "transports": [
                {
                    "name": "HTTP",
                    "endpoint": "/mcp/http",
                    "method": "POST",
                    "description": "JSON-RPC over HTTP POST requests",
                },
                {
                    "name": "WebSocket",
                    "endpoint": "/mcp/ws",
                    "description": "JSON-RPC over WebSocket connection",
                },
                {
                    "name": "STDIO",
                    "description": "Standard MCP transport over STDIO (built-in)",
                },
            ],
        },
        indent=2,
    )


# HTTP Transport Implementation


@app.post("/mcp/http")
async def mcp_http_endpoint(request_data: Dict):
    """HTTP endpoint for MCP requests"""
    try:
        logger.info(f"Received HTTP request: {json.dumps(request_data)}")

        # Process the MCP request
        response = await process_mcp_message(request_data)
        logger.info(f"Sending HTTP response: {json.dumps(response)}")

        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error processing HTTP request: {str(e)}")
        return JSONResponse(
            content={"error": {"code": -32603, "message": f"Internal error: {str(e)}"}},
            status_code=500,
        )


# WebSocket Transport Implementation


@app.websocket("/mcp/ws")
async def mcp_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for MCP connections"""
    await websocket.accept()

    # Generate a unique connection ID
    connection_id = f"ws_{id(websocket)}"
    websocket_connections[connection_id] = websocket

    logger.info(f"WebSocket connection established: {connection_id}")

    try:
        while True:
            # Receive message from client
            message_text = await websocket.receive_text()
            try:
                message = json.loads(message_text)
                logger.info(f"Received WebSocket message: {json.dumps(message)}")

                # Process the message
                response = await process_mcp_message(message)

                # Send response back to client
                logger.info(f"Sending WebSocket response: {json.dumps(response)}")
                await websocket.send_json(response)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message_text}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }
                await websocket.send_json(error_response)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]


# MCP message processing


async def process_mcp_message(message: Dict) -> Dict:
    """Process an MCP message and return the response"""
    # Create custom session handling for persistent sessions
    # In a real implementation, you would maintain session state

    # Special handling for initialize
    if message.get("method") == "initialize":
        # Create new session
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "capabilities": mcp.server_capabilities,
                "serverInfo": {"name": "MCP Custom Transport Demo", "version": "1.0.0"},
            },
        }

    # Handle other MCP methods
    if "method" in message:
        method = message.get("method")
        params = message.get("params", {})

        # Handle resource requests
        if method == "resources/get":
            uri = params.get("uri")
            if uri == "demo://transport":
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "content": get_transport_resource(),
                        "contentType": "application/json",
                    },
                }

        # Handle tool operations
        elif method == "tools/list":
            # Return list of available tools
            tools = [
                {
                    "name": "echo",
                    "description": "Simple echo tool for testing",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                },
                {
                    "name": "get_transport_info",
                    "description": "Get information about the current transport",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {"tools": tools},
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_params = params.get("params", {})

            if tool_name == "echo":
                result = echo(tool_params.get("message", ""))
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {"result": result},
                }
            elif tool_name == "get_transport_info":
                result = get_transport_info()
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {"result": result},
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}",
                    },
                }

    # Handle unknown methods
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "error": {
            "code": -32601,
            "message": f"Method not found: {message.get('method')}",
        },
    }


# Server info endpoint


@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "MCP Custom Transports Demo",
        "description": "Demonstrates how to implement MCP over HTTP and WebSockets",
        "endpoints": {"http": "/mcp/http", "websocket": "/mcp/ws"},
        "usage": {
            "http": "Send POST requests with JSON-RPC formatted MCP messages",
            "websocket": "Connect to the WebSocket endpoint and exchange JSON-RPC messages",
        },
    }


# Server startup


@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup"""
    logger.info("Starting MCP Custom Transports Demo Server")
    logger.info("Available endpoints:")
    logger.info("  - HTTP: POST /mcp/http")
    logger.info("  - WebSocket: /mcp/ws")


# Implement a class for the STDIO transport (already handled by FastMCP)
# This is just for demonstration purposes


class StdioTransport:
    """Standard IO transport for MCP (this is built into FastMCP)"""

    def __init__(self):
        self.reader = None
        self.writer = None

    async def start(self):
        """Start the STDIO transport"""
        self.reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(self.reader)

        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

        self.writer_transport, _ = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        self.writer = asyncio.StreamWriter(
            self.writer_transport, protocol=None, reader=None, loop=loop
        )

    async def receive(self):
        """Receive a message from STDIO"""
        if not self.reader:
            return None

        line = await self.reader.readline()
        if not line:
            return None

        return line.decode("utf-8").strip()

    async def send(self, message):
        """Send a message to STDIO"""
        if not self.writer:
            return

        self.writer.write(f"{message}\n".encode("utf-8"))
        await self.writer.drain()


def run_fastapi_server():
    """Run the FastAPI server for HTTP and WebSocket transports"""
    port = 8000
    logger.info(f"Starting FastAPI server on port {port}")
    sys.stderr.write("\n=== MCP CUSTOM TRANSPORTS DEMO ===\n")
    sys.stderr.write(f"HTTP endpoint: http://localhost:{port}/mcp/http\n")
    sys.stderr.write(f"WebSocket endpoint: ws://localhost:{port}/mcp/ws\n")
    sys.stderr.write(f"Visit http://localhost:{port}/ for more information\n")
    sys.stderr.write("=== END CUSTOM TRANSPORTS INFO ===\n\n")

    # Start server with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Run the FastAPI server
    run_fastapi_server()

    # You can still use the standard MCP CLI with:
    # uv run mcp dev 42-custom-transports.py
