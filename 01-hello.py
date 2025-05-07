import getpass
import os

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Hello World")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
