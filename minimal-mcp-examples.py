#!/usr/bin/env python3
"""
Minimal MCP Examples
This file demonstrates several MCP concepts in a single file
"""

import getpass
import json
import os
from datetime import datetime
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("MinimalMCPExamples")


# 1. SQLite Persistence example
@mcp.tool()
def sqlite_demo() -> Dict[str, Any]:
    """
    Demonstrate SQLite persistence

    Creates a temporary SQLite database and performs basic operations
    """
    import sqlite3
    import tempfile

    # Create a temporary database
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create a table
    cursor.execute("""
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        timestamp TEXT
    )
    """)

    # Insert some data
    events = [
        ("initialization", datetime.now().isoformat()),
        ("processing", datetime.now().isoformat()),
        ("completion", datetime.now().isoformat()),
    ]

    cursor.executemany(
        "INSERT INTO events (event_type, timestamp) VALUES (?, ?)", events
    )
    conn.commit()

    # Query the data
    cursor.execute("SELECT * FROM events")
    results = cursor.fetchall()

    # Clean up
    conn.close()
    os.unlink(db_file)

    return {
        "database_file": db_file,
        "records_created": len(events),
        "query_results": [
            {"id": row[0], "event_type": row[1], "timestamp": row[2]} for row in results
        ],
    }


# 2. Memory Cache example
_cache = {}  # Simple in-memory cache


@mcp.tool()
def cache_set(key: str, value: str, ttl_seconds: int = 60) -> Dict[str, Any]:
    """
    Store a value in the cache

    Args:
        key: Cache key
        value: Value to store
        ttl_seconds: Time to live in seconds (default: 60)
    """
    expiry = datetime.now().timestamp() + ttl_seconds
    _cache[key] = {"value": value, "expiry": expiry}

    return {
        "key": key,
        "value": value,
        "ttl_seconds": ttl_seconds,
        "expires_at": datetime.fromtimestamp(expiry).isoformat(),
    }


@mcp.tool()
def cache_get(key: str) -> Dict[str, Any]:
    """
    Retrieve a value from the cache

    Args:
        key: Cache key
    """
    if key not in _cache:
        return {"key": key, "found": False}

    item = _cache[key]
    now = datetime.now().timestamp()

    # Check if expired
    if now > item["expiry"]:
        del _cache[key]
        return {"key": key, "found": False, "reason": "expired"}

    return {
        "key": key,
        "found": True,
        "value": item["value"],
        "expires_at": datetime.fromtimestamp(item["expiry"]).isoformat(),
    }


# 3. JSON Schema Validation example
@mcp.tool()
def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate user data against a schema

    Args:
        data: User data to validate
    """
    try:
        import jsonschema

        # User schema
        user_schema = {
            "type": "object",
            "required": ["name", "email", "age"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 18},
                "address": {"type": "string"},
            },
        }

        # Validate
        jsonschema.validate(data, user_schema)

        return {"valid": True, "data": data}
    except ImportError:
        return {"error": "jsonschema module not installed", "valid": False}
    except jsonschema.exceptions.ValidationError as e:
        return {
            "valid": False,
            "error": str(e),
            "path": "/".join([str(p) for p in e.path]) if e.path else "root",
        }


# 4. LLM Sampling Proxy example - simulated
@mcp.tool()
def llm_generate(
    prompt: str, model: str = "simulated-model", max_tokens: int = 100
) -> Dict[str, Any]:
    """
    Simulate LLM text generation

    Args:
        prompt: Text prompt
        model: Model to use (simulated)
        max_tokens: Maximum tokens to generate
    """
    # Simulate thinking time
    import time

    time.sleep(0.5)

    # Generate a response based on the prompt
    if "weather" in prompt.lower():
        response = "The weather is currently sunny with a temperature of 72°F."
    elif "help" in prompt.lower():
        response = "I'm a simulated AI. How can I assist you today?"
    elif "code" in prompt.lower() or "python" in prompt.lower():
        response = "```python\ndef hello_world():\n    print('Hello, world!')\n```"
    else:
        response = f"You asked: '{prompt}'. This is a simulated response."

    # Simulate token counts
    prompt_tokens = len(prompt) // 4
    completion_tokens = len(response) // 4

    return {
        "model": model,
        "prompt": prompt,
        "response": response,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "finished_at": datetime.now().isoformat(),
    }


# 5. Cross-Server Bridge example - simulated
@mcp.tool()
def bridge_call_remote_tool(
    server_id: str, tool_name: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulate calling a tool on a remote MCP server

    Args:
        server_id: ID of the remote server
        tool_name: Name of the tool to call
        params: Tool parameters
    """
    # Simulate remote servers
    servers = {
        "server1": {
            "name": "RemoteServer1",
            "url": "http://localhost:8001",
            "tools": ["echo", "add", "subtract"],
        },
        "server2": {
            "name": "RemoteServer2",
            "url": "http://localhost:8002",
            "tools": ["weather", "news", "search"],
        },
    }

    # Check if server exists
    if server_id not in servers:
        return {
            "error": f"Server '{server_id}' not found",
            "available_servers": list(servers.keys()),
        }

    server = servers[server_id]

    # Check if tool exists on server
    if tool_name not in server["tools"]:
        return {
            "error": f"Tool '{tool_name}' not found on server '{server_id}'",
            "available_tools": server["tools"],
        }

    # Simulate tool call
    if tool_name == "echo":
        result = {"message": params.get("message", "")}
    elif tool_name == "add":
        result = {"result": params.get("a", 0) + params.get("b", 0)}
    elif tool_name == "subtract":
        result = {"result": params.get("a", 0) - params.get("b", 0)}
    elif tool_name == "weather":
        result = {"forecast": "Sunny, 72°F"}
    elif tool_name == "news":
        result = {"headlines": ["Example headline 1", "Example headline 2"]}
    elif tool_name == "search":
        result = {
            "results": [f"Result for '{params.get('query', '')}'", "Another result"]
        }
    else:
        result = {"message": "Tool called with unknown implementation"}

    return {
        "server_id": server_id,
        "server_name": server["name"],
        "tool": tool_name,
        "params": params,
        "result": result,
        "timestamp": datetime.now().isoformat(),
    }


# Resources
@mcp.resource("example://info")
def example_info() -> str:
    """Provide information about this MCP example server"""
    tools = [
        {"name": "sqlite_demo", "description": "Demonstrate SQLite persistence"},
        {"name": "cache_set", "description": "Store a value in the cache"},
        {"name": "cache_get", "description": "Retrieve a value from the cache"},
        {
            "name": "validate_user_data",
            "description": "Validate user data against a schema",
        },
        {"name": "llm_generate", "description": "Simulate LLM text generation"},
        {
            "name": "bridge_call_remote_tool",
            "description": "Simulate calling a tool on a remote MCP server",
        },
    ]

    resources = [
        {
            "uri": "example://info",
            "description": "Information about this MCP example server",
        }
    ]

    return json.dumps(
        {
            "name": "MinimalMCPExamples",
            "description": "Demonstrates several MCP concepts in a single file",
            "tools": tools,
            "resources": resources,
            "timestamp": datetime.now().isoformat(),
        },
        indent=2,
    )


# Run with: uv run mcp dev minimal-mcp-examples.py
