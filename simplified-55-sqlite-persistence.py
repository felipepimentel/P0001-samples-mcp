import getpass
import os
from typing import Dict, Any
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("simplified-55-sqlite-persistence")

# Copy of tools and resources from 55-sqlite-persistence.py
# with lifecycle hooks and middleware removed
import getpass
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
# Workaround for os.getlogin issues in some environments
# Create an MCP server
# SQLite database setup
# Create necessary tables if they don't exist
def init_database():
    """Initialize SQLite database with required tables"""
    # Sessions table - stores session information
    cursor.execute("""
    """)
    # Events table - stores all session events
    cursor.execute("""
    """)
    # Tool calls table - stores tool invocation history
    cursor.execute("""
    """)
    # Resource access table - stores resource access history
    cursor.execute("""
    """)
    print(f"Database initialized: {DB_FILE}")
# Initialize database on startup
# Session state
    "session_id": None,
    "started_at": None,
    "client_info": None,
# Database operations
def store_event(session_id: str, event_type: str, details: Optional[Dict] = None):
    """Store an event in the database"""
    # Convert details to JSON if provided
    # Update session's last active timestamp
    return timestamp
def store_tool_call(
    session_id: str, tool_name: str, params: Dict, result: Any, duration_ms: int
    """Store a tool call in the database"""
    return timestamp
def store_resource_access(session_id: str, uri: str):
    """Store a resource access in the database"""
    return timestamp
def get_session_events(
    session_id: str, event_type: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict]:
    """Get events for a session from the database"""
    if event_type:
    if limit:
    for row in cursor.fetchall():
            {"event_type": row[0], "timestamp": row[1], "details": json.loads(row[2])}
    return events
def get_tool_calls(
    session_id: str, tool_name: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict]:
    """Get tool calls for a session from the database"""
    if tool_name:
    if limit:
    for row in cursor.fetchall():
                "tool_name": row[0],
                "params": json.loads(row[1]),
                "result": json.loads(row[2]),
                "timestamp": row[3],
                "duration_ms": row[4],
    return tool_calls
def get_session_stats(session_id: str) -> Dict:
    """Get statistics for a session"""
    # Get session info
    if not session_row:
        return {"error": "Session not found"}
    # Count events by type
    event_counts = {row[0]: row[1] for row in cursor.fetchall()}
    # Count total tool calls
    # Count resource accesses
    # Calculate session duration
    return {
        "session_id": session_id,
        "client_info": {"name": session_row[0], "version": session_row[1]},
        "started_at": session_row[2],
        "last_active_at": session_row[3],
        "is_active": bool(session_row[4]),
        "duration": f"{duration_seconds:.2f} seconds",
        "event_counts": event_counts,
        "tool_call_count": tool_call_count,
        "resource_access_count": resource_access_count,
# Lifecycle hooks
def handle_initialize(params):
    """Handle session initialization"""
        "name": client_info.get("name", "unknown"),
        "version": client_info.get("version", "unknown"),
    # Store session in database
        """
        """,
    # Store initialization event
            "client_info": current_session["client_info"],
            "client_capabilities": params.get("capabilities"),
    # Return the server capabilities
    return {"capabilities": mcp.server_capabilities}
def handle_shutdown(params):
    """Handle session shutdown"""
    # Mark session as inactive
    # Store shutdown event
        session_id, "session_shutdown", {"stats": get_session_stats(session_id)}
# Middleware for tracking requests
async def db_tracker(message, next_handler):
    """Track all messages in the database"""
    # Process specific types of requests
    if "method" in message:
        # Track tool calls
        if method == "tools/call":
            # Record the event before processing
                session_id, "tool_called", {"tool": tool_name, "params": params}
            # Process the request normally
            # Calculate duration
            # Store the tool call with result
            return response
        # Track resource access
        elif method == "resources/get":
            # Store the resource access
            store_event(session_id, "resource_accessed", {"uri": uri})
    # For other message types, process normally
    return response
# Basic tools to demonstrate persistence
@mcp.tool()
def get_session_history(
    event_type: Optional[str] = None, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Args:
        event_type: Filter events by type (optional)
        limit: Maximum number of events to return (optional)
    """
    return {"session_id": session_id, "filtered_count": len(events), "events": events}
@mcp.tool()
def get_tool_history(
    tool_name: Optional[str] = None, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Args:
        tool_name: Filter by specific tool name (optional)
        limit: Maximum number of calls to return (optional)
    """
    return {
        "session_id": session_id,
        "filtered_count": len(tool_calls),
        "tool_calls": tool_calls,
@mcp.tool()
def get_current_stats() -> Dict[str, Any]:
    """
    """
    return get_session_stats(session_id)
@mcp.tool()
def list_all_sessions() -> Dict[str, Any]:
    """
    """
        """
        """
    for row in cursor.fetchall():
                "session_id": row[0],
                "client_name": row[1],
                "client_version": row[2],
                "started_at": row[3],
                "last_active_at": row[4],
                "is_active": bool(row[5]),
    return {"total_sessions": len(sessions), "sessions": sessions}
# Resources
@mcp.resource("persistence://current-session")
def get_current_session_resource() -> str:
    """Get current session stats as a resource"""
    return json.dumps(get_session_stats(session_id), indent=2)
@mcp.resource("persistence://sessions")
def get_sessions_resource() -> str:
    """Get all sessions as a resource"""
    return json.dumps(list_all_sessions(), indent=2)
# Ensure database connection is closed at exit
def cleanup():
    """Clean up database connection"""
    if connection:
        print(f"Database connection closed: {DB_FILE}")
import atexit
# Explain what this demo does when run with MCP CLI
sys.stderr.write("This example demonstrates MCP with SQLite persistence:\n")
# This server demonstrates MCP with SQLite persistence
# Run with: uv run mcp dev 55-sqlite-persistence.py

if __name__ == "__main__":
    print("MCP Server ready to run!")
    # The server will be run by MCP CLI
    
# Run with: uv run mcp dev simplified-55-sqlite-persistence.py
