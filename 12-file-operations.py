import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("File Operations")

# Create a safe directory for file operations
SAFE_DIR = Path(os.path.expanduser("~")) / "mcp_files"
SAFE_DIR.mkdir(exist_ok=True)


@mcp.tool()
def list_files() -> str:
    """List all files in the safe directory"""
    files = [f.name for f in SAFE_DIR.iterdir() if f.is_file()]
    return "\n".join(files) if files else "No files found"


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read the contents of a file in the safe directory

    Args:
        filename: Name of the file to read
    """
    file_path = SAFE_DIR / filename

    # Security check - ensure the resolved path is within SAFE_DIR
    try:
        if not file_path.resolve().is_relative_to(SAFE_DIR.resolve()):
            raise ValueError(f"Access denied: {filename} is outside the safe directory")

        if not file_path.exists():
            return f"File not found: {filename}"

        return file_path.read_text()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    Write content to a file in the safe directory

    Args:
        filename: Name of the file to write
        content: Content to write to the file
    """
    # Prevent path traversal
    if "/" in filename or "\\" in filename:
        return "Invalid filename: Cannot contain path separators"

    file_path = SAFE_DIR / filename

    try:
        file_path.write_text(content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.resource("files://list")
def get_files_list() -> str:
    """Get a list of all files in the safe directory"""
    return list_files()
