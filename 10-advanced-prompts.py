from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Advanced Prompts")


@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


@mcp.prompt()
def summarize(text: str) -> str:
    """Summarize the provided text."""
    return f"Summary: {text[:50]}..." if len(text) > 50 else f"Summary: {text}"
