from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Stateful Resource")

_counter = 0


@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


@mcp.resource("counter://value")
def get_counter() -> int:
    return _counter


@mcp.tool()
def increment_counter() -> int:
    global _counter
    _counter += 1
    return _counter
