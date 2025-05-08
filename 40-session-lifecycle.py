import getpass
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SessionLifecycleDemo")

# Store session lifecycle events
session_events = []
session_state = {
    "session_id": None,
    "started_at": None,
    "client_info": None,
    "tool_calls": 0,
    "resource_accesses": 0,
    "last_activity": None,
    "shutdown": False,
}


# Track session lifecycle events
def record_event(event_type: str, details: Optional[Dict] = None):
    """Record a session lifecycle event"""
    timestamp = datetime.now().isoformat()

    event = {
        "event_type": event_type,
        "timestamp": timestamp,
        "details": details or {},
    }

    session_events.append(event)
    session_state["last_activity"] = timestamp

    # Log event to stderr
    sys.stderr.write(f"EVENT [{timestamp}]: {event_type}")
    if details:
        sys.stderr.write(f" - {json.dumps(details)}")
    sys.stderr.write("\n")


# Lifecycle hooks
@mcp.on_initialize
def handle_initialize(params):
    """Handle session initialization"""
    session_state["session_id"] = params.get("session_id", "unknown")
    session_state["started_at"] = datetime.now().isoformat()
    session_state["client_info"] = {
        "name": params.get("client_info", {}).get("name", "unknown"),
        "version": params.get("client_info", {}).get("version", "unknown"),
    }

    record_event(
        "session_initialized",
        {
            "session_id": session_state["session_id"],
            "client_info": session_state["client_info"],
            "client_capabilities": params.get("capabilities"),
        },
    )

    # Return the server capabilities
    return {"capabilities": mcp.server_capabilities}


@mcp.on_shutdown
def handle_shutdown(params):
    """Handle session shutdown"""
    session_state["shutdown"] = True

    record_event(
        "session_shutdown",
        {
            "session_duration": get_session_duration(),
            "total_events": len(session_events),
        },
    )


# Middleware to track all requests
@mcp.middleware
async def session_tracker(message, next_handler):
    """Track all messages in the session"""
    # Record incoming message
    if "method" in message:
        method = message.get("method", "unknown")

        # Track specific types of requests
        if method.startswith("tools/"):
            if method == "tools/call":
                tool_name = message.get("params", {}).get("name", "unknown")
                record_event(
                    "tool_called",
                    {
                        "tool": tool_name,
                        "params": message.get("params", {}).get("params", {}),
                    },
                )
                session_state["tool_calls"] += 1
            elif method == "tools/list":
                record_event("tools_listed")

        elif method.startswith("resources/"):
            if method == "resources/get":
                uri = message.get("params", {}).get("uri", "unknown")
                record_event(
                    "resource_accessed",
                    {
                        "uri": uri,
                    },
                )
                session_state["resource_accesses"] += 1

    # Process the message normally
    response = await next_handler(message)

    # Return the response
    return response


# Helper functions
def get_session_duration():
    """Calculate the session duration"""
    if not session_state["started_at"]:
        return "Not started"

    end_time = session_state["last_activity"] or datetime.now().isoformat()

    try:
        start_dt = datetime.fromisoformat(session_state["started_at"])
        end_dt = datetime.fromisoformat(end_time)
        duration_seconds = (end_dt - start_dt).total_seconds()
        return f"{duration_seconds:.2f} seconds"
    except:
        return "Unknown"


# Basic tools to demonstrate lifecycle
@mcp.tool()
def get_session_info() -> Dict[str, Any]:
    """
    Get information about the current session

    Returns details about session ID, duration, and activity counts
    """
    return {
        "session_id": session_state["session_id"],
        "started_at": session_state["started_at"],
        "client_info": session_state["client_info"],
        "duration": get_session_duration(),
        "tool_calls": session_state["tool_calls"],
        "resource_accesses": session_state["resource_accesses"],
        "last_activity": session_state["last_activity"],
        "is_active": not session_state["shutdown"],
    }


@mcp.tool()
def get_lifecycle_events(
    event_type: Optional[str] = None, limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get session lifecycle events

    Args:
        event_type: Filter events by type (optional)
        limit: Maximum number of events to return (optional)

    Returns a list of session events in chronological order
    """
    filtered_events = session_events

    # Apply event type filter if specified
    if event_type:
        filtered_events = [e for e in filtered_events if e["event_type"] == event_type]

    # Apply limit if specified
    if limit and limit > 0:
        filtered_events = filtered_events[-limit:]

    return {
        "total_events": len(session_events),
        "filtered_count": len(filtered_events),
        "events": filtered_events,
    }


@mcp.tool()
def simulate_activity(
    num_actions: int = 5, delay_seconds: float = 0.5
) -> Dict[str, Any]:
    """
    Simulate a series of session activities

    Args:
        num_actions: Number of actions to simulate
        delay_seconds: Delay between actions in seconds

    Returns a summary of the simulated activities
    """
    activities = []

    for i in range(num_actions):
        activity_type = "custom_activity"
        details = {
            "sequence": i + 1,
            "description": f"Simulated activity #{i + 1}",
        }

        record_event(activity_type, details)
        activities.append(
            {
                "type": activity_type,
                "details": details,
            }
        )

        if i < num_actions - 1:  # No need to sleep after the last activity
            time.sleep(delay_seconds)

    return {
        "activities_simulated": num_actions,
        "total_duration": num_actions * delay_seconds,
        "activities": activities,
    }


# Resources to expose session information
@mcp.resource("session://info")
def get_session_resource() -> str:
    """Get current session information as a resource"""
    return json.dumps(get_session_info(), indent=2)


@mcp.resource("session://events")
def get_events_resource() -> str:
    """Get session events as a resource"""
    return json.dumps(
        {
            "total_events": len(session_events),
            "events": session_events,
        },
        indent=2,
    )


@mcp.resource("session://summary")
def get_summary_resource() -> str:
    """Get a summary of the session as a resource"""
    # Count events by type
    event_counts = {}
    for event in session_events:
        event_type = event["event_type"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    return json.dumps(
        {
            "session_id": session_state["session_id"],
            "started_at": session_state["started_at"],
            "duration": get_session_duration(),
            "client_info": session_state["client_info"],
            "total_events": len(session_events),
            "event_counts": event_counts,
            "tool_calls": session_state["tool_calls"],
            "resource_accesses": session_state["resource_accesses"],
            "is_active": not session_state["shutdown"],
        },
        indent=2,
    )


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP SESSION LIFECYCLE DEMO ===\n")
sys.stderr.write("This example demonstrates the MCP session lifecycle:\n")
sys.stderr.write("1. Session initialization with capability negotiation\n")
sys.stderr.write("2. Tracking of tool calls and resource accesses\n")
sys.stderr.write("3. Monitoring session activity and duration\n")
sys.stderr.write("4. Session shutdown and cleanup\n\n")
sys.stderr.write(
    "Use get_session_info and get_lifecycle_events to see session details.\n"
)
sys.stderr.write("Try simulate_activity to generate session events.\n")
sys.stderr.write(
    "Check the session:// resources to see session information as resources.\n"
)
sys.stderr.write("=== END SESSION LIFECYCLE INFO ===\n\n")

# This server demonstrates the MCP session lifecycle
# Run with: uv run mcp dev 40-session-lifecycle.py
