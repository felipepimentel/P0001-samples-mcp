import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("File Upload/Download Tool Example")

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTS = {".txt", ".csv", ".md"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB


@mcp.tool()
def upload_file(filename: str, content: bytes) -> str:
    """Upload a file securely (only .txt, .csv, .md, max 2MB)"""
    ext = Path(filename).suffix
    if ext not in ALLOWED_EXTS:
        return f"Extension {ext} not allowed."
    if len(content) > MAX_SIZE:
        return "File too large."
    safe_path = UPLOAD_DIR / os.path.basename(filename)
    with open(safe_path, "wb") as f:
        f.write(content)
    return f"Uploaded: {safe_path}"


@mcp.resource("file://download/{filename}")
def download_file(filename: str) -> bytes:
    """Download a file if allowed and exists"""
    safe_path = UPLOAD_DIR / os.path.basename(filename)
    if not safe_path.exists() or safe_path.suffix not in ALLOWED_EXTS:
        return b""
    with open(safe_path, "rb") as f:
        return f.read()
