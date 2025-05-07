from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Multi Tool")


@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    return a - b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    return a * b


@mcp.tool()
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b
