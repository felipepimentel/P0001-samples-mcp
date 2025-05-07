from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Prompt Review")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.prompt()
def review_code(code: str) -> str:
    """Review the provided code and return feedback."""
    return f"Please review this code:\n\n{code}"
