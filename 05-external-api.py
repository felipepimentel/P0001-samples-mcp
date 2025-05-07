import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("External API")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def get_ip() -> str:
    """Fetch public IP address from external API."""
    resp = httpx.get("https://api.ipify.org?format=text", timeout=5)
    return resp.text.strip()
