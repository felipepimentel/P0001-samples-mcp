import getpass
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Set

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("ResourceRootsDemo")

# Define some example resource roots
DEFAULT_ROOTS = ["public://", "temp://"]

# Store active roots and the authorization state
active_roots = set(DEFAULT_ROOTS)
root_requests = {}  # Store pending root access requests
root_analytics = {
    root: {"access_count": 0, "last_accessed": None} for root in DEFAULT_ROOTS
}

# Sample data repositories for different resource roots
public_data = {
    "welcome.txt": "Welcome to the public data repository! This data is accessible by default.",
    "about.json": json.dumps(
        {
            "name": "Public Repository",
            "description": "Contains publicly accessible data",
            "created_at": "2025-01-01T00:00:00Z",
        }
    ),
    "readme.md": "# Public Data\nThis repository contains non-sensitive information available to all clients.",
}

user_data = {
    "profile.json": json.dumps(
        {
            "name": "Sample User",
            "email": "user@example.com",
            "preferences": {"theme": "dark", "notifications": True},
            "created_at": "2025-02-15T14:30:00Z",
        }
    ),
    "notes.txt": "These are my personal notes. This information requires explicit authorization.",
    "todos.json": json.dumps(
        [
            {"id": 1, "title": "Review MCP specification", "completed": True},
            {"id": 2, "title": "Implement custom MCP server", "completed": False},
            {
                "id": 3,
                "title": "Test resource roots and authorization",
                "completed": False,
            },
        ]
    ),
}

system_data = {
    "config.json": json.dumps(
        {
            "api_keys": {"service_a": "sk_a_12345", "service_b": "sk_b_67890"},
            "server_settings": {
                "max_connections": 100,
                "timeout_seconds": 30,
                "debug_mode": False,
            },
        }
    ),
    "logs.txt": "2025-04-01 12:00:00 INFO Server started\n2025-04-01 12:05:23 WARN High CPU usage detected\n2025-04-01 12:10:45 INFO Backend synced",
    "users.json": json.dumps(
        [
            {"id": 1, "username": "admin", "role": "administrator"},
            {"id": 2, "username": "user1", "role": "standard"},
            {"id": 3, "username": "user2", "role": "standard"},
        ]
    ),
}

temp_data = {}  # Empty repository for temporary data

# Map roots to their data repositories
root_repositories = {
    "public://": public_data,
    "user://": user_data,
    "system://": system_data,
    "temp://": temp_data,
}

# Information about available roots
root_info = {
    "public://": {
        "name": "Public Data",
        "description": "Non-sensitive public information",
        "requires_authorization": False,
        "available_by_default": True,
    },
    "user://": {
        "name": "User Data",
        "description": "Personal user information and settings",
        "requires_authorization": True,
        "available_by_default": False,
    },
    "system://": {
        "name": "System Data",
        "description": "Sensitive system configuration and logs",
        "requires_authorization": True,
        "available_by_default": False,
    },
    "temp://": {
        "name": "Temporary Storage",
        "description": "Ephemeral storage for session data",
        "requires_authorization": False,
        "available_by_default": True,
    },
}


# Tools for interacting with resources and roots
@mcp.tool()
def list_available_roots() -> Dict[str, Any]:
    """
    List all available resource roots

    This shows which roots are currently active and which require authorization
    """
    all_roots = []
    for root, info in root_info.items():
        all_roots.append(
            {
                "root": root,
                "name": info["name"],
                "description": info["description"],
                "requires_authorization": info["requires_authorization"],
                "is_active": root in active_roots,
                "analytics": root_analytics.get(
                    root, {"access_count": 0, "last_accessed": None}
                ),
            }
        )

    return {"active_roots": list(active_roots), "all_roots": all_roots}


@mcp.tool()
def request_root_access(root: str, reason: str) -> Dict[str, Any]:
    """
    Request access to a resource root that requires authorization

    This simulates the client requesting access to a protected resource root
    """
    # Check if the root exists
    if root not in root_info:
        return {"status": "error", "message": f"Root '{root}' does not exist"}

    # Check if root is already active
    if root in active_roots:
        return {"status": "success", "message": f"Root '{root}' is already accessible"}

    # Check if authorization is required
    if not root_info[root]["requires_authorization"]:
        # Automatically grant access to non-protected roots
        active_roots.add(root)
        return {
            "status": "success",
            "message": f"Access granted to '{root}' (no authorization required)",
        }

    # Create a root access request
    request_id = str(uuid.uuid4())
    request = {
        "id": request_id,
        "root": root,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
    }

    # Store the request
    root_requests[request_id] = request

    # Notify about the pending request
    sys.stderr.write("\n>>> ROOT ACCESS REQUEST <<<\n")
    sys.stderr.write(f"Root: {root}\n")
    sys.stderr.write(f"Reason: {reason}\n")
    sys.stderr.write(f"Request ID: {request_id}\n")
    sys.stderr.write("Use 'approve_root_access' or 'reject_root_access' to respond\n\n")

    return {
        "status": "pending",
        "request_id": request_id,
        "message": f"Access request for '{root}' is pending approval",
        "instructions": "Use approve_root_access or reject_root_access to complete this request",
    }


@mcp.tool()
def approve_root_access(request_id: str) -> Dict[str, Any]:
    """
    Approve a pending root access request

    This simulates a human approving root access
    """
    # Check if the request exists
    if request_id not in root_requests:
        return {"status": "error", "message": "Request not found or already processed"}

    # Get the request details
    request = root_requests[request_id]
    root = request["root"]

    # Grant access by adding to active roots
    active_roots.add(root)

    # Update request status
    request["status"] = "approved"
    request["approved_at"] = datetime.now().isoformat()

    # Log the approval
    sys.stderr.write(f"Root access request {request_id} for {root} approved\n")

    return {
        "status": "approved",
        "root": root,
        "message": f"Access granted to '{root}'",
        "active_roots": list(active_roots),
    }


@mcp.tool()
def reject_root_access(request_id: str, reason: str = "Not approved") -> Dict[str, Any]:
    """
    Reject a pending root access request

    This simulates a human rejecting root access
    """
    # Check if the request exists
    if request_id not in root_requests:
        return {"status": "error", "message": "Request not found or already processed"}

    # Get the request details
    request = root_requests[request_id]
    root = request["root"]

    # Update request status
    request["status"] = "rejected"
    request["rejection_reason"] = reason
    request["rejected_at"] = datetime.now().isoformat()

    # Log the rejection
    sys.stderr.write(
        f"Root access request {request_id} for {root} rejected: {reason}\n"
    )

    return {
        "status": "rejected",
        "root": root,
        "reason": reason,
        "message": f"Access denied to '{root}': {reason}",
    }


@mcp.tool()
def revoke_root_access(root: str) -> Dict[str, Any]:
    """
    Revoke access to a previously authorized root

    This allows revoking access to sensitive roots when no longer needed
    """
    # Check if the root exists
    if root not in root_info:
        return {"status": "error", "message": f"Root '{root}' does not exist"}

    # Check if the root is active
    if root not in active_roots:
        return {"status": "error", "message": f"Root '{root}' is not currently active"}

    # Revoke access by removing from active roots
    active_roots.remove(root)

    # Log the revocation
    sys.stderr.write(f"Access to root {root} revoked\n")

    return {
        "status": "success",
        "message": f"Access to '{root}' has been revoked",
        "active_roots": list(active_roots),
    }


@mcp.tool()
def list_files(root: str) -> Dict[str, Any]:
    """
    List files available in a specific root

    Args:
        root: The resource root to list files from (e.g., "public://")
    """
    # Check if the root exists
    if root not in root_info:
        return {"status": "error", "message": f"Root '{root}' does not exist"}

    # Check if the root is active
    if root not in active_roots:
        return {
            "status": "error",
            "message": f"No access to '{root}'. Request access first.",
            "instructions": "Use request_root_access to request access to this root",
        }

    # Get the repository for this root
    repository = root_repositories[root]

    # Update analytics
    root_analytics[root] = {
        "access_count": root_analytics.get(root, {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    # Return the list of files
    files = []
    for filename, content in repository.items():
        # Determine content type based on file extension
        content_type = "text/plain"
        if filename.endswith(".json"):
            content_type = "application/json"
        elif filename.endswith(".md"):
            content_type = "text/markdown"

        files.append(
            {"filename": filename, "content_type": content_type, "size": len(content)}
        )

    return {"root": root, "files": files, "count": len(files)}


@mcp.tool()
def read_file(root: str, filename: str) -> Dict[str, Any]:
    """
    Read a file from a specific root

    Args:
        root: The resource root containing the file (e.g., "public://")
        filename: The name of the file to read
    """
    # Check if the root exists
    if root not in root_info:
        return {"status": "error", "message": f"Root '{root}' does not exist"}

    # Check if the root is active
    if root not in active_roots:
        return {
            "status": "error",
            "message": f"No access to '{root}'. Request access first.",
            "instructions": "Use request_root_access to request access to this root",
        }

    # Get the repository for this root
    repository = root_repositories[root]

    # Check if the file exists
    if filename not in repository:
        return {
            "status": "error",
            "message": f"File '{filename}' not found in root '{root}'",
        }

    # Update analytics
    root_analytics[root] = {
        "access_count": root_analytics.get(root, {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    # Get the content
    content = repository[filename]

    # Determine content type based on file extension
    content_type = "text/plain"
    if filename.endswith(".json"):
        content_type = "application/json"
    elif filename.endswith(".md"):
        content_type = "text/markdown"

    return {
        "root": root,
        "filename": filename,
        "content_type": content_type,
        "content": content,
    }


@mcp.tool()
def write_file(root: str, filename: str, content: str) -> Dict[str, Any]:
    """
    Write a file to a specific root

    Args:
        root: The resource root to write to (e.g., "temp://")
        filename: The name of the file to write
        content: The content to write to the file
    """
    # Check if the root exists
    if root not in root_info:
        return {"status": "error", "message": f"Root '{root}' does not exist"}

    # Check if the root is active
    if root not in active_roots:
        return {
            "status": "error",
            "message": f"No access to '{root}'. Request access first.",
            "instructions": "Use request_root_access to request access to this root",
        }

    # Get the repository for this root
    repository = root_repositories[root]

    # Write the file
    repository[filename] = content

    # Update analytics
    root_analytics[root] = {
        "access_count": root_analytics.get(root, {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    return {
        "status": "success",
        "root": root,
        "filename": filename,
        "message": f"File {filename} written to {root}",
    }


@mcp.tool()
def delete_file(root: str, filename: str) -> Dict[str, Any]:
    """
    Delete a file from a specific root

    Args:
        root: The resource root containing the file (e.g., "temp://")
        filename: The name of the file to delete
    """
    # Check if the root exists
    if root not in root_info:
        return {"status": "error", "message": f"Root '{root}' does not exist"}

    # Check if the root is active
    if root not in active_roots:
        return {
            "status": "error",
            "message": f"No access to '{root}'. Request access first.",
            "instructions": "Use request_root_access to request access to this root",
        }

    # Get the repository for this root
    repository = root_repositories[root]

    # Check if the file exists
    if filename not in repository:
        return {
            "status": "error",
            "message": f"File '{filename}' not found in root '{root}'",
        }

    # Delete the file
    del repository[filename]

    # Update analytics
    root_analytics[root] = {
        "access_count": root_analytics.get(root, {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    return {
        "status": "success",
        "root": root,
        "filename": filename,
        "message": f"File {filename} deleted from {root}",
    }


# Define resources using our root system
@mcp.resource("public://{filename}")
def get_public_resource(filename: str) -> str:
    """Get a file from the public root"""
    # Public resources are always available without authorization
    if filename not in public_data:
        return json.dumps({"error": "File not found"})

    # Update analytics
    root_analytics["public://"] = {
        "access_count": root_analytics.get("public://", {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    return public_data[filename]


@mcp.resource("user://{filename}")
def get_user_resource(filename: str) -> str:
    """Get a file from the user root"""
    # Check if the user root is active (authorized)
    if "user://" not in active_roots:
        return json.dumps(
            {
                "error": "Authorization required",
                "message": "The user:// root requires explicit authorization. Use request_root_access to request access.",
            }
        )

    if filename not in user_data:
        return json.dumps({"error": "File not found"})

    # Update analytics
    root_analytics["user://"] = {
        "access_count": root_analytics.get("user://", {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    return user_data[filename]


@mcp.resource("system://{filename}")
def get_system_resource(filename: str) -> str:
    """Get a file from the system root"""
    # Check if the system root is active (authorized)
    if "system://" not in active_roots:
        return json.dumps(
            {
                "error": "Authorization required",
                "message": "The system:// root requires explicit authorization. Use request_root_access to request access.",
            }
        )

    if filename not in system_data:
        return json.dumps({"error": "File not found"})

    # Update analytics
    root_analytics["system://"] = {
        "access_count": root_analytics.get("system://", {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    return system_data[filename]


@mcp.resource("temp://{filename}")
def get_temp_resource(filename: str) -> str:
    """Get a file from the temporary root"""
    # Temp resources are always available without authorization
    if filename not in temp_data:
        return json.dumps({"error": "File not found"})

    # Update analytics
    root_analytics["temp://"] = {
        "access_count": root_analytics.get("temp://", {}).get("access_count", 0) + 1,
        "last_accessed": datetime.now().isoformat(),
    }

    return temp_data[filename]


@mcp.resource("roots://info")
def get_roots_info() -> str:
    """Get information about all available roots"""
    return json.dumps(
        {
            "roots": root_info,
            "active_roots": list(active_roots),
            "analytics": root_analytics,
        },
        indent=2,
    )


# Hook into MCP's built-in roots management
@mcp.on_roots_request
def handle_roots_request(roots: List[str]) -> Set[str]:
    """
    Handle client requests for specific roots

    This hook lets us manage which roots the client can use
    """
    approved_roots = set()

    for root in roots:
        # Normalize root format (ensure it ends with "://")
        if not root.endswith("://"):
            root = f"{root}://"

        # Check if the root is already active
        if root in active_roots:
            approved_roots.add(root)
            sys.stderr.write(f"Auto-approved root access: {root} (already active)\n")

        # Check if the root doesn't require authorization
        elif root in root_info and not root_info[root]["requires_authorization"]:
            active_roots.add(root)
            approved_roots.add(root)
            sys.stderr.write(
                f"Auto-approved root access: {root} (no authorization required)\n"
            )

        # Otherwise, the root needs explicit authorization
        else:
            sys.stderr.write(
                f"Denied root access: {root} (requires explicit authorization)\n"
            )

    return approved_roots


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP RESOURCE ROOTS DEMO ===\n")
sys.stderr.write("This example demonstrates MCP's resource roots mechanism:\n")
sys.stderr.write(
    "1. Resource roots provide security boundaries for accessing resources\n"
)
sys.stderr.write("2. Some roots (public://, temp://) are available by default\n")
sys.stderr.write("3. Other roots (user://, system://) require explicit authorization\n")
sys.stderr.write("4. Use list_available_roots to see available roots\n")
sys.stderr.write("5. Use request_root_access to request access to protected roots\n")
sys.stderr.write(
    "6. Try accessing resources in different roots to see authorization in action\n\n"
)
sys.stderr.write(
    "Resource roots are a fundamental MCP security mechanism that allows\n"
)
sys.stderr.write("controlled access to different categories of resources.\n")
sys.stderr.write("=== END RESOURCE ROOTS INFO ===\n\n")

# This server demonstrates MCP resource roots
# Run with: uv run mcp dev 49-resource-roots.py
