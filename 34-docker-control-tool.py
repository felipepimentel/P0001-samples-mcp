import docker
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Docker Control Tool Example")
client = docker.from_env()


@mcp.tool()
def list_containers() -> str:
    """List running Docker containers"""
    containers = client.containers.list()
    return "\n".join([f"{c.name} ({c.id[:12]})" for c in containers])


@mcp.tool()
def start_container(container_id: str) -> str:
    """Start a stopped Docker container by ID or name"""
    try:
        container = client.containers.get(container_id)
        container.start()
        return f"Started: {container.name}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def stop_container(container_id: str) -> str:
    """Stop a running Docker container by ID or name"""
    try:
        container = client.containers.get(container_id)
        container.stop()
        return f"Stopped: {container.name}"
    except Exception as e:
        return f"Error: {str(e)}"
