import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FastAPI Tool Example")

FASTAPI_URL = "http://localhost:8000/ping"


@mcp.tool()
def call_fastapi_ping() -> str:
    """Call FastAPI /ping endpoint and return response"""
    resp = httpx.get(FASTAPI_URL)
    if resp.status_code != 200:
        return f"Error: {resp.text}"
    return resp.text
