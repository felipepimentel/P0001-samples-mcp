import getpass
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server with debug mode enabled
mcp = FastMCP("ProtocolInspector", debug=True)

# Set up a message log to record protocol messages
protocol_messages = []


# Custom logging middleware to capture all JSON-RPC messages
@mcp.middleware
async def protocol_logger(message, next_handler):
    """Log all protocol messages before processing them"""
    # Record the incoming message
    timestamp = datetime.now().isoformat()
    direction = "INCOMING"
    protocol_messages.append(
        {
            "timestamp": timestamp,
            "direction": direction,
            "message": message,
        }
    )

    # Log to stderr for immediate visibility
    sys.stderr.write(f"\n>>> {direction} MESSAGE [{timestamp}] <<<\n")
    sys.stderr.write(f"{json.dumps(message, indent=2)}\n")

    # Process the message normally
    response = await next_handler(message)

    # Record the outgoing response
    timestamp = datetime.now().isoformat()
    direction = "OUTGOING"
    protocol_messages.append(
        {
            "timestamp": timestamp,
            "direction": direction,
            "message": response,
        }
    )

    # Log to stderr for immediate visibility
    sys.stderr.write(f"\n>>> {direction} MESSAGE [{timestamp}] <<<\n")
    sys.stderr.write(f"{json.dumps(response, indent=2)}\n")

    return response


# Simple echo tool for demonstrating protocol
@mcp.tool()
def echo(message: str) -> str:
    """
    Echo the input message back to the client

    This simple tool helps demonstrate the protocol message flow
    """
    return f"ECHO: {message}"


# Tool that shows information about a specific message
@mcp.tool()
def inspect_message(index: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific protocol message

    Args:
        index: The index of the message to inspect (0 is the earliest message)
    """
    if not protocol_messages or index < 0 or index >= len(protocol_messages):
        return {"error": "Message index out of range"}

    message = protocol_messages[index]

    # Analyze the message type
    msg_content = message["message"]
    msg_type = "Unknown"
    msg_method = msg_content.get("method", "N/A")
    msg_id = msg_content.get("id", "N/A")

    if "method" in msg_content:
        if "result" in msg_content:
            msg_type = "Notification"
        else:
            msg_type = "Request"
    elif "result" in msg_content:
        msg_type = "Success Response"
    elif "error" in msg_content:
        msg_type = "Error Response"

    return {
        "index": index,
        "timestamp": message["timestamp"],
        "direction": message["direction"],
        "type": msg_type,
        "id": msg_id,
        "method": msg_method,
        "raw_message": message["message"],
    }


# Tool to view message history
@mcp.tool()
def get_message_history() -> Dict[str, Any]:
    """
    Get a summary of all recorded protocol messages
    """
    summary = []

    for i, message in enumerate(protocol_messages):
        msg_content = message["message"]
        msg_type = "Unknown"
        description = ""

        # Determine message type
        if "method" in msg_content:
            method = msg_content.get("method", "")
            if method == "initialize":
                msg_type = "Initialize Request"
                description = "Client initializing session"
            elif method.startswith("resources/"):
                msg_type = "Resource Operation"
                description = f"Resource {method}"
            elif method.startswith("tools/"):
                msg_type = "Tool Operation"
                if method == "tools/list":
                    description = "List available tools"
                elif method == "tools/call":
                    tool_name = msg_content.get("params", {}).get("name", "unknown")
                    description = f"Call tool '{tool_name}'"
            elif "result" in msg_content:
                msg_type = "Notification"
                description = f"Notification: {method}"
            else:
                msg_type = "Request"
                description = f"Method: {method}"
        elif "result" in msg_content:
            msg_type = "Response"
            description = "Success response"
        elif "error" in msg_content:
            msg_type = "Error"
            error = msg_content.get("error", {})
            code = error.get("code", "?")
            msg = error.get("message", "Unknown error")
            description = f"Error {code}: {msg}"

        summary.append(
            {
                "index": i,
                "timestamp": message["timestamp"],
                "direction": message["direction"],
                "type": msg_type,
                "description": description,
            }
        )

    return {
        "message_count": len(summary),
        "messages": summary,
    }


# Tool to analyze the protocol session
@mcp.tool()
def analyze_session() -> Dict[str, Any]:
    """
    Analyze the current protocol session for key metrics and statistics
    """
    if not protocol_messages:
        return {"error": "No messages recorded yet"}

    # Count different types of messages
    request_count = 0
    response_count = 0
    error_count = 0
    notification_count = 0

    # Count by method
    methods = {}

    # Track session lifecycle events
    initialize_time = None
    latest_time = None

    for message in protocol_messages:
        msg_content = message["message"]
        timestamp = message["timestamp"]
        latest_time = timestamp

        if "method" in msg_content:
            method = msg_content.get("method", "")

            if method == "initialize" and message["direction"] == "INCOMING":
                initialize_time = timestamp

            if method not in methods:
                methods[method] = 0
            methods[method] += 1

            if "result" in msg_content:
                notification_count += 1
            else:
                request_count += 1
        elif "result" in msg_content:
            response_count += 1
        elif "error" in msg_content:
            error_count += 1

    # Prepare metrics
    session_duration = "N/A"
    if initialize_time and latest_time:
        init_dt = datetime.fromisoformat(initialize_time)
        latest_dt = datetime.fromisoformat(latest_time)
        duration_seconds = (latest_dt - init_dt).total_seconds()
        session_duration = f"{duration_seconds:.2f} seconds"

    return {
        "total_messages": len(protocol_messages),
        "requests": request_count,
        "responses": response_count,
        "notifications": notification_count,
        "errors": error_count,
        "method_counts": methods,
        "session_duration": session_duration,
    }


# Resource to expose message logs
@mcp.resource("protocol://messages")
def get_protocol_messages() -> str:
    """Get all recorded protocol messages as a resource"""
    return json.dumps(
        {"count": len(protocol_messages), "messages": protocol_messages}, indent=2
    )


# Resource to expose session analysis
@mcp.resource("protocol://analysis")
def get_protocol_analysis() -> str:
    """Get protocol session analysis as a resource"""
    return json.dumps(analyze_session(), indent=2)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP RAW PROTOCOL INSPECTOR ===\n")
sys.stderr.write("This example demonstrates the JSON-RPC protocol used by MCP:\n")
sys.stderr.write("1. All protocol messages are logged and available for inspection\n")
sys.stderr.write("2. Use the echo tool to see a simple request/response flow\n")
sys.stderr.write("3. Use get_message_history to see all recorded messages\n")
sys.stderr.write("4. Use inspect_message to analyze a specific message in detail\n")
sys.stderr.write("5. Use analyze_session to get statistics about the session\n\n")
sys.stderr.write("This inspector reveals the 'under the hood' protocol exchanges\n")
sys.stderr.write(
    "between MCP clients and servers, which are normally abstracted away.\n"
)
sys.stderr.write("=== END PROTOCOL INSPECTOR INFO ===\n\n")

# This server demonstrates the raw MCP protocol
# Run with: uv run mcp dev 39-raw-protocol-inspector.py
