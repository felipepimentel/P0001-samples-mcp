from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Dynamic Resource")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("square://{number}")
def get_square(number: int) -> int:
    """Return the square of the number"""
    return number * number
