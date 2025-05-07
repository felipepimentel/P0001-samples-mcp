from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Tool Composition")

# Store calculation history
calculation_history = []


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    result = a + b
    calculation_history.append(f"{a} + {b} = {result}")
    return result


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    result = a * b
    calculation_history.append(f"{a} * {b} = {result}")
    return result


@mcp.tool()
def calculate_area(length: int, width: int) -> int:
    """Calculate the area of a rectangle by multiplying length and width"""
    return multiply(length, width)


@mcp.tool()
def calculate_perimeter(length: int, width: int) -> int:
    """Calculate the perimeter of a rectangle: 2*(length+width)"""
    return multiply(2, add(length, width))


@mcp.resource("history://calculations")
def get_calculation_history() -> str:
    """Get the history of calculations performed"""
    return "\n".join(calculation_history)
