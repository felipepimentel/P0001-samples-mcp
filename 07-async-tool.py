import asyncio

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Async Tool")


@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


@mcp.tool()
async def wait_and_add(a: int, b: int, seconds: int) -> int:
    await asyncio.sleep(seconds)
    return a + b
