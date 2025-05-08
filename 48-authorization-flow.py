import getpass
import json

# Workaround for os.getlogin issues in some environments
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("AuthorizationDemo")

# Simulate a database of resources with different sensitivity levels
files_db = {
    "public/readme.txt": {
        "content": "This is a public readme file that anyone can read.",
        "sensitivity": "public",
        "last_modified": "2025-01-01T12:00:00Z",
    },
    "internal/roadmap.txt": {
        "content": "Company roadmap for 2025-2026. Confidential information.",
        "sensitivity": "internal",
        "last_modified": "2025-02-15T09:30:00Z",
    },
    "confidential/passwords.txt": {
        "content": "System passwords and access codes. Highly confidential.",
        "sensitivity": "confidential",
        "last_modified": "2025-03-10T14:45:00Z",
    },
    "restricted/secrets.txt": {
        "content": "Top secret information. Access extremely restricted.",
        "sensitivity": "restricted",
        "last_modified": "2025-04-05T11:20:00Z",
    },
}

# Track operations that require authorization
pending_operations = {}
authorized_operations = {}
rejected_operations = {}

# Set up authorization metadata to control how tools are called
authorization_rules = {
    "read_file": {
        "public": {"requires_approval": False},
        "internal": {"requires_approval": False},
        "confidential": {"requires_approval": True},
        "restricted": {"requires_approval": True},
    },
    "write_file": {
        "public": {"requires_approval": False},
        "internal": {"requires_approval": True},
        "confidential": {"requires_approval": True},
        "restricted": {"requires_approval": True},
    },
    "delete_file": {
        "public": {"requires_approval": True},
        "internal": {"requires_approval": True},
        "confidential": {"requires_approval": True},
        "restricted": {"requires_approval": True},
    },
}


# MCP Server tools
@mcp.tool()
def list_files() -> Dict[str, Any]:
    """
    List all available files with their sensitivity levels

    This operation doesn't require authorization
    """
    files_list = []
    for path, info in files_db.items():
        files_list.append(
            {
                "path": path,
                "sensitivity": info["sensitivity"],
                "last_modified": info["last_modified"],
            }
        )

    return {"files": files_list}


@mcp.tool()
def read_file(path: str) -> Dict[str, Any]:
    """
    Read the contents of a file

    Authorization may be required depending on the file's sensitivity
    """
    # Check if file exists
    if path not in files_db:
        return {"error": "File not found"}

    file_info = files_db[path]
    sensitivity = file_info["sensitivity"]

    # Check if authorization is required
    if authorization_rules["read_file"][sensitivity]["requires_approval"]:
        # Create an operation that needs approval
        operation_id = str(uuid.uuid4())
        operation = {
            "id": operation_id,
            "type": "read_file",
            "path": path,
            "sensitivity": sensitivity,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "result": None,
        }

        # Record the pending operation
        pending_operations[operation_id] = operation

        # Ask for human approval
        sys.stderr.write("\n>>> AUTHORIZATION REQUIRED <<<\n")
        sys.stderr.write("Operation: read_file\n")
        sys.stderr.write(f"Path: {path}\n")
        sys.stderr.write(f"Sensitivity: {sensitivity}\n")
        sys.stderr.write(f"Operation ID: {operation_id}\n")
        sys.stderr.write(
            "Use 'approve_operation' or 'reject_operation' tool to respond\n\n"
        )

        # Return info about the pending operation
        return {
            "status": "authorization_required",
            "operation_id": operation_id,
            "message": f"Authorization required to read {sensitivity} file",
            "instructions": "Use approve_operation or reject_operation to complete this request",
        }
    else:
        # No authorization needed, return the file content directly
        return {
            "path": path,
            "content": file_info["content"],
            "sensitivity": sensitivity,
            "last_modified": file_info["last_modified"],
        }


@mcp.tool()
def write_file(path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file

    Authorization may be required depending on the file's sensitivity
    """
    # Check if path starts with a valid prefix
    valid_prefix = False
    sensitivity = "public"  # Default

    for existing_path in files_db:
        prefix = existing_path.split("/")[0]
        if path.startswith(f"{prefix}/"):
            valid_prefix = True
            sensitivity = files_db[existing_path]["sensitivity"]
            break

    if not valid_prefix:
        return {"error": "Invalid path or directory"}

    # Check if authorization is required
    if authorization_rules["write_file"][sensitivity]["requires_approval"]:
        # Create an operation that needs approval
        operation_id = str(uuid.uuid4())
        operation = {
            "id": operation_id,
            "type": "write_file",
            "path": path,
            "content": content,
            "sensitivity": sensitivity,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "result": None,
        }

        # Record the pending operation
        pending_operations[operation_id] = operation

        # Ask for human approval
        sys.stderr.write("\n>>> AUTHORIZATION REQUIRED <<<\n")
        sys.stderr.write("Operation: write_file\n")
        sys.stderr.write(f"Path: {path}\n")
        sys.stderr.write(f"Sensitivity: {sensitivity}\n")
        sys.stderr.write(f"Content length: {len(content)} characters\n")
        sys.stderr.write(f"Operation ID: {operation_id}\n")
        sys.stderr.write(
            "Use 'approve_operation' or 'reject_operation' tool to respond\n\n"
        )

        # Return info about the pending operation
        return {
            "status": "authorization_required",
            "operation_id": operation_id,
            "message": f"Authorization required to write to {sensitivity} file",
            "instructions": "Use approve_operation or reject_operation to complete this request",
        }
    else:
        # No authorization needed, write the file directly
        files_db[path] = {
            "content": content,
            "sensitivity": sensitivity,
            "last_modified": datetime.now().isoformat(),
        }

        return {
            "status": "success",
            "path": path,
            "message": "File written successfully",
        }


@mcp.tool()
def delete_file(path: str) -> Dict[str, Any]:
    """
    Delete a file

    Authorization is required for all file deletions
    """
    # Check if file exists
    if path not in files_db:
        return {"error": "File not found"}

    file_info = files_db[path]
    sensitivity = file_info["sensitivity"]

    # Create an operation that needs approval
    operation_id = str(uuid.uuid4())
    operation = {
        "id": operation_id,
        "type": "delete_file",
        "path": path,
        "sensitivity": sensitivity,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "result": None,
    }

    # Record the pending operation
    pending_operations[operation_id] = operation

    # Ask for human approval
    sys.stderr.write("\n>>> AUTHORIZATION REQUIRED <<<\n")
    sys.stderr.write("Operation: delete_file\n")
    sys.stderr.write(f"Path: {path}\n")
    sys.stderr.write(f"Sensitivity: {sensitivity}\n")
    sys.stderr.write(f"Operation ID: {operation_id}\n")
    sys.stderr.write(
        "Use 'approve_operation' or 'reject_operation' tool to respond\n\n"
    )

    # Return info about the pending operation
    return {
        "status": "authorization_required",
        "operation_id": operation_id,
        "message": f"Authorization required to delete {sensitivity} file",
        "instructions": "Use approve_operation or reject_operation to complete this request",
    }


@mcp.tool()
def approve_operation(operation_id: str) -> Dict[str, Any]:
    """
    Approve a pending operation

    This simulates a human approving a sensitive operation
    """
    # Check if operation exists and is pending
    if operation_id not in pending_operations:
        return {
            "status": "error",
            "message": "Operation not found or already processed",
        }

    # Get the operation details
    operation = pending_operations[operation_id]
    operation_type = operation["type"]

    # Process the operation based on its type
    result = None
    if operation_type == "read_file":
        path = operation["path"]
        file_info = files_db[path]
        result = {
            "path": path,
            "content": file_info["content"],
            "sensitivity": file_info["sensitivity"],
            "last_modified": file_info["last_modified"],
        }
    elif operation_type == "write_file":
        path = operation["path"]
        content = operation["content"]
        files_db[path] = {
            "content": content,
            "sensitivity": operation["sensitivity"],
            "last_modified": datetime.now().isoformat(),
        }
        result = {
            "status": "success",
            "path": path,
            "message": "File written successfully",
        }
    elif operation_type == "delete_file":
        path = operation["path"]
        del files_db[path]
        result = {
            "status": "success",
            "path": path,
            "message": "File deleted successfully",
        }

    # Update operation status
    operation["status"] = "approved"
    operation["result"] = result
    operation["approved_at"] = datetime.now().isoformat()

    # Move from pending to authorized
    authorized_operations[operation_id] = operation
    del pending_operations[operation_id]

    # Log the approval
    sys.stderr.write(f"Operation {operation_id} approved and executed\n")

    return {
        "status": "approved",
        "operation_id": operation_id,
        "operation_type": operation_type,
        "result": result,
    }


@mcp.tool()
def reject_operation(operation_id: str, reason: str = "Not approved") -> Dict[str, Any]:
    """
    Reject a pending operation

    This simulates a human rejecting a sensitive operation
    """
    # Check if operation exists and is pending
    if operation_id not in pending_operations:
        return {
            "status": "error",
            "message": "Operation not found or already processed",
        }

    # Get the operation details
    operation = pending_operations[operation_id]

    # Update operation status
    operation["status"] = "rejected"
    operation["rejection_reason"] = reason
    operation["rejected_at"] = datetime.now().isoformat()

    # Move from pending to rejected
    rejected_operations[operation_id] = operation
    del pending_operations[operation_id]

    # Log the rejection
    sys.stderr.write(f"Operation {operation_id} rejected: {reason}\n")

    return {
        "status": "rejected",
        "operation_id": operation_id,
        "operation_type": operation["type"],
        "reason": reason,
    }


@mcp.tool()
def list_operations(status: str = "all") -> Dict[str, Any]:
    """
    List operations by status

    Args:
        status: Filter by status: 'pending', 'approved', 'rejected', or 'all'
    """
    operations = []

    if status == "pending" or status == "all":
        for op_id, op in pending_operations.items():
            op_copy = op.copy()
            op_copy["status"] = "pending"
            operations.append(op_copy)

    if status == "approved" or status == "all":
        for op_id, op in authorized_operations.items():
            op_copy = op.copy()
            op_copy["status"] = "approved"
            operations.append(op_copy)

    if status == "rejected" or status == "all":
        for op_id, op in rejected_operations.items():
            op_copy = op.copy()
            op_copy["status"] = "rejected"
            operations.append(op_copy)

    return {"operations": operations, "count": len(operations), "filter": status}


# Resources for retrieving information
@mcp.resource("files://list")
def get_files_resource() -> str:
    """Get a list of all files as a resource"""
    files_list = []
    for path, info in files_db.items():
        files_list.append(
            {
                "path": path,
                "sensitivity": info["sensitivity"],
                "last_modified": info["last_modified"],
            }
        )

    return json.dumps({"files": files_list}, indent=2)


@mcp.resource("authorization://rules")
def get_authorization_rules() -> str:
    """Get the authorization rules as a resource"""
    return json.dumps(authorization_rules, indent=2)


@mcp.resource("operations://status")
def get_operations_status() -> str:
    """Get the status of all operations as a resource"""
    return json.dumps(
        {
            "pending": len(pending_operations),
            "approved": len(authorized_operations),
            "rejected": len(rejected_operations),
            "total": len(pending_operations)
            + len(authorized_operations)
            + len(rejected_operations),
        },
        indent=2,
    )


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP AUTHORIZATION FLOW DEMO ===\n")
sys.stderr.write(
    "This example demonstrates MCP's human-in-the-loop authorization flows:\n"
)
sys.stderr.write("1. Use list_files to see available files with sensitivity levels\n")
sys.stderr.write(
    "2. Try reading/writing/deleting files with different sensitivity levels\n"
)
sys.stderr.write("3. For sensitive operations, you'll see an authorization request\n")
sys.stderr.write(
    "4. Use approve_operation or reject_operation to handle pending requests\n"
)
sys.stderr.write(
    "5. Check the authorization//rules resource to see the authorization matrix\n\n"
)
sys.stderr.write(
    "MCP authorization flows allow for human oversight of AI-initiated actions,\n"
)
sys.stderr.write("providing crucial safety guardrails for sensitive operations.\n")
sys.stderr.write("=== END AUTHORIZATION FLOW INFO ===\n\n")

# This server demonstrates MCP authorization flows
# Run with: uv run mcp dev 48-authorization-flow.py
