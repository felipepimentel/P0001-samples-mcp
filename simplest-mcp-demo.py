import getpass
import os
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SimplestMCPDemo")


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
            "name": "SimplestMCPDemo",
            "tools": ["echo", "add"],
            "resources": ["demo://info"],
            "timestamp": datetime.datetime.now().isoformat(),
        },
        indent=2,
    )


if __name__ == "__main__":
    print("MCP Server is ready to run!")
    # The server will be run by MCP CLI

# Run with: uv run mcp dev simplest-mcp-demo.py
