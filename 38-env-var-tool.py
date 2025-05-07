import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Environment Variable Tool Example")


@mcp.tool()
def get_env_var(name: str) -> str:
    """Get the value of an environment variable"""
    return os.environ.get(name, "Not set")


@mcp.tool()
def set_env_var(name: str, value: str) -> str:
    """Set the value of an environment variable"""
    os.environ[name] = value
    return f"Set {name}={value}"
