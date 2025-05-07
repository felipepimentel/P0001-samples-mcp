from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math Tools")


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract b from a"""
    return a - b
