import getpass
import os
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SimpleMCPDemo")


# Add a middleware to handle initializing and shutdown
@mcp.middleware
async def session_handler(message, next_handler):
    """Handle session initialization and shutdown"""
    if "method" in message:
        method = message.get("method")

        # Handle initialization
        if method == "initialize":
            print("Session initializing...")
            # Process normally but track initialization
            response = await next_handler(message)
            print("Session initialized!")
            return response

        # Handle shutdown
        elif method == "shutdown":
            print("Session shutting down...")
            # Process normally but track shutdown
            response = await next_handler(message)
            print("Session shut down!")
            return response

    # Handle all other messages normally
    return await next_handler(message)


# Simple echo tool
@mcp.tool()
def echo(message: str) -> Dict[str, Any]:
    """
    Echo a message back

    Args:
        message: The message to echo

    Returns the message with timestamp
    """
    import datetime

    return {"message": message, "timestamp": datetime.datetime.now().isoformat()}


# Simple add tool
@mcp.tool()
def add(a: int, b: int) -> Dict[str, Any]:
    """
    Add two numbers

    Args:
        a: First number
        b: Second number

    Returns the sum of the numbers
    """
    result = a + b

    return {"a": a, "b": b, "result": result}


# Simple resource
@mcp.resource("demo://info")
def demo_info() -> str:
    """Simple demo information resource"""
    import datetime
    import json

    return json.dumps(
        {
            "name": "SimpleMCPDemo",
            "tools": ["echo", "add"],
            "resources": ["demo://info"],
            "timestamp": datetime.datetime.now().isoformat(),
        },
        indent=2,
    )


# Run with: uv run mcp dev simple-mcp-demo.py
