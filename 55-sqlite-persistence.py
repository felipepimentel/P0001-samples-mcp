import getpass
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SQLitePersistedMCP")

# SQLite database setup
DB_FILE = "mcp_session_store.db"
connection = sqlite3.connect(DB_FILE)


# Create necessary tables if they don't exist
def init_database():
    """Initialize SQLite database with required tables"""
    cursor = connection.cursor()

    # Sessions table - stores session information
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        client_name TEXT,
        client_version TEXT,
        started_at TEXT,
        last_active_at TEXT,
        is_active INTEGER
    )
    """)

    # Events table - stores all session events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        event_type TEXT,
        timestamp TEXT,
        details TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
    )
    """)

    # Tool calls table - stores tool invocation history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tool_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        tool_name TEXT,
        params TEXT,
        result TEXT,
        timestamp TEXT,
        duration_ms INTEGER,
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
    )
    """)

    # Resource access table - stores resource access history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_accesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        uri TEXT,
        timestamp TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
    )
    """)

    connection.commit()
    print(f"Database initialized: {DB_FILE}")


# Initialize database on startup
init_database()

# Session state
current_session = {
    "session_id": None,
    "started_at": None,
    "client_info": None,
}


# Database operations
def store_event(session_id: str, event_type: str, details: Optional[Dict] = None):
    """Store an event in the database"""
    cursor = connection.cursor()
    timestamp = datetime.now().isoformat()

    # Convert details to JSON if provided
    details_json = json.dumps(details) if details else "{}"

    cursor.execute(
        "INSERT INTO events (session_id, event_type, timestamp, details) VALUES (?, ?, ?, ?)",
        (session_id, event_type, timestamp, details_json),
    )

    # Update session's last active timestamp
    cursor.execute(
        "UPDATE sessions SET last_active_at = ? WHERE session_id = ?",
        (timestamp, session_id),
    )

    connection.commit()
    return timestamp


def store_tool_call(
    session_id: str, tool_name: str, params: Dict, result: Any, duration_ms: int
):
    """Store a tool call in the database"""
    cursor = connection.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO tool_calls (session_id, tool_name, params, result, timestamp, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
        (
            session_id,
            tool_name,
            json.dumps(params),
            json.dumps(result),
            timestamp,
            duration_ms,
        ),
    )

    connection.commit()
    return timestamp


def store_resource_access(session_id: str, uri: str):
    """Store a resource access in the database"""
    cursor = connection.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO resource_accesses (session_id, uri, timestamp) VALUES (?, ?, ?)",
        (session_id, uri, timestamp),
    )

    connection.commit()
    return timestamp


def get_session_events(
    session_id: str, event_type: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict]:
    """Get events for a session from the database"""
    cursor = connection.cursor()

    query = "SELECT event_type, timestamp, details FROM events WHERE session_id = ?"
    params = [session_id]

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    query += " ORDER BY timestamp DESC"

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, params)

    events = []
    for row in cursor.fetchall():
        events.append(
            {"event_type": row[0], "timestamp": row[1], "details": json.loads(row[2])}
        )

    return events


def get_tool_calls(
    session_id: str, tool_name: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict]:
    """Get tool calls for a session from the database"""
    cursor = connection.cursor()

    query = "SELECT tool_name, params, result, timestamp, duration_ms FROM tool_calls WHERE session_id = ?"
    params = [session_id]

    if tool_name:
        query += " AND tool_name = ?"
        params.append(tool_name)

    query += " ORDER BY timestamp DESC"

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, params)

    tool_calls = []
    for row in cursor.fetchall():
        tool_calls.append(
            {
                "tool_name": row[0],
                "params": json.loads(row[1]),
                "result": json.loads(row[2]),
                "timestamp": row[3],
                "duration_ms": row[4],
            }
        )

    return tool_calls


def get_session_stats(session_id: str) -> Dict:
    """Get statistics for a session"""
    cursor = connection.cursor()

    # Get session info
    cursor.execute(
        "SELECT client_name, client_version, started_at, last_active_at, is_active FROM sessions WHERE session_id = ?",
        (session_id,),
    )
    session_row = cursor.fetchone()

    if not session_row:
        return {"error": "Session not found"}

    # Count events by type
    cursor.execute(
        "SELECT event_type, COUNT(*) FROM events WHERE session_id = ? GROUP BY event_type",
        (session_id,),
    )
    event_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Count total tool calls
    cursor.execute(
        "SELECT COUNT(*) FROM tool_calls WHERE session_id = ?", (session_id,)
    )
    tool_call_count = cursor.fetchone()[0]

    # Count resource accesses
    cursor.execute(
        "SELECT COUNT(*) FROM resource_accesses WHERE session_id = ?", (session_id,)
    )
    resource_access_count = cursor.fetchone()[0]

    # Calculate session duration
    started_at = datetime.fromisoformat(session_row[2])
    last_active_at = datetime.fromisoformat(session_row[3])
    duration_seconds = (last_active_at - started_at).total_seconds()

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
    }


# Lifecycle hooks
@mcp.initialize
def handle_initialize(params):
    """Handle session initialization"""
    session_id = params.get("session_id", "unknown")
    current_session["session_id"] = session_id
    current_session["started_at"] = datetime.now().isoformat()

    client_info = params.get("client_info", {})
    current_session["client_info"] = {
        "name": client_info.get("name", "unknown"),
        "version": client_info.get("version", "unknown"),
    }

    # Store session in database
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO sessions 
        (session_id, client_name, client_version, started_at, last_active_at, is_active) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            current_session["client_info"]["name"],
            current_session["client_info"]["version"],
            current_session["started_at"],
            current_session["started_at"],
            1,
        ),
    )
    connection.commit()

    # Store initialization event
    store_event(
        session_id,
        "session_initialized",
        {
            "client_info": current_session["client_info"],
            "client_capabilities": params.get("capabilities"),
        },
    )

    # Return the server capabilities
    return {"capabilities": mcp.server_capabilities}


@mcp.shutdown
def handle_shutdown(params):
    """Handle session shutdown"""
    session_id = current_session["session_id"]

    # Mark session as inactive
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,)
    )
    connection.commit()

    # Store shutdown event
    store_event(
        session_id, "session_shutdown", {"stats": get_session_stats(session_id)}
    )


# Middleware for tracking requests
@mcp.middleware
async def db_tracker(message, next_handler):
    """Track all messages in the database"""
    session_id = current_session["session_id"]

    # Process specific types of requests
    if "method" in message:
        method = message.get("method", "unknown")

        # Track tool calls
        if method == "tools/call":
            tool_name = message.get("params", {}).get("name", "unknown")
            params = message.get("params", {}).get("params", {})

            # Record the event before processing
            start_time = datetime.now()
            store_event(
                session_id, "tool_called", {"tool": tool_name, "params": params}
            )

            # Process the request normally
            response = await next_handler(message)

            # Calculate duration
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Store the tool call with result
            result = response.get("result", {})
            store_tool_call(session_id, tool_name, params, result, duration_ms)

            return response

        # Track resource access
        elif method == "resources/get":
            uri = message.get("params", {}).get("uri", "unknown")

            # Store the resource access
            store_resource_access(session_id, uri)
            store_event(session_id, "resource_accessed", {"uri": uri})

    # For other message types, process normally
    response = await next_handler(message)
    return response


# Basic tools to demonstrate persistence
@mcp.tool()
def get_session_history(
    event_type: Optional[str] = None, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get events from the current session

    Args:
        event_type: Filter events by type (optional)
        limit: Maximum number of events to return (optional)

    Returns a list of session events from persistent storage
    """
    session_id = current_session["session_id"]
    events = get_session_events(session_id, event_type, limit)

    return {"session_id": session_id, "filtered_count": len(events), "events": events}


@mcp.tool()
def get_tool_history(
    tool_name: Optional[str] = None, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get tool call history from the current session

    Args:
        tool_name: Filter by specific tool name (optional)
        limit: Maximum number of calls to return (optional)

    Returns a list of tool calls from persistent storage
    """
    session_id = current_session["session_id"]
    tool_calls = get_tool_calls(session_id, tool_name, limit)

    return {
        "session_id": session_id,
        "filtered_count": len(tool_calls),
        "tool_calls": tool_calls,
    }


@mcp.tool()
def get_current_stats() -> Dict[str, Any]:
    """
    Get statistics for the current session

    Returns detailed statistics about the current session from persistent storage
    """
    session_id = current_session["session_id"]
    return get_session_stats(session_id)


@mcp.tool()
def list_all_sessions() -> Dict[str, Any]:
    """
    List all sessions in the database

    Returns a list of all MCP sessions in the persistent storage
    """
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT session_id, client_name, client_version, started_at, last_active_at, is_active 
        FROM sessions ORDER BY started_at DESC
        """
    )

    sessions = []
    for row in cursor.fetchall():
        sessions.append(
            {
                "session_id": row[0],
                "client_name": row[1],
                "client_version": row[2],
                "started_at": row[3],
                "last_active_at": row[4],
                "is_active": bool(row[5]),
            }
        )

    return {"total_sessions": len(sessions), "sessions": sessions}


# Resources
@mcp.resource("persistence://current-session")
def get_current_session_resource() -> str:
    """Get current session stats as a resource"""
    session_id = current_session["session_id"]
    return json.dumps(get_session_stats(session_id), indent=2)


@mcp.resource("persistence://sessions")
def get_sessions_resource() -> str:
    """Get all sessions as a resource"""
    return json.dumps(list_all_sessions(), indent=2)


# Ensure database connection is closed at exit
def cleanup():
    """Clean up database connection"""
    if connection:
        connection.close()
        print(f"Database connection closed: {DB_FILE}")


import atexit

atexit.register(cleanup)

# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP WITH SQLITE PERSISTENCE ===\n")
sys.stderr.write("This example demonstrates MCP with SQLite persistence:\n")
sys.stderr.write(
    "1. All session data is stored in an SQLite database (mcp_session_store.db)\n"
)
sys.stderr.write("2. Sessions, events, tool calls, and resource accesses are tracked\n")
sys.stderr.write("3. Historical data persists between sessions\n")
sys.stderr.write("4. Use get_session_history and get_tool_history to explore data\n")
sys.stderr.write("5. Use list_all_sessions to see all previous sessions\n\n")
sys.stderr.write(
    "This example shows how to add persistence to MCP without external dependencies\n"
)
sys.stderr.write("=== END SQLITE PERSISTENCE INFO ===\n\n")

# This server demonstrates MCP with SQLite persistence
# Run with: uv run mcp dev 55-sqlite-persistence.py
