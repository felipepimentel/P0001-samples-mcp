import getpass
import os
from typing import Dict, Any
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("simplified-57-cross-server-bridge")

# Copy of tools and resources from 57-cross-server-bridge.py
# with lifecycle hooks and middleware removed
import getpass
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4
from mcp.client import McpClient
from mcp.server.fastmcp import FastMCP
# Workaround for os.getlogin issues in some environments
# Create an MCP server
# Track remote MCP servers
# MCP Client class to connect to remote servers
class RemoteMCPClient:
    def __init__(self, server_id, name, url):
        """Initialize remote MCP client"""
    async def connect(self):
        """Connect to the remote MCP server"""
        try:
            # Create and initialize client
            # Discover available tools
            return True
        except Exception as e:
            print(f"Error connecting to {self.name}: {str(e)}")
            return False
    async def disconnect(self):
        """Disconnect from the remote MCP server"""
        if self.client and self.connected:
            try:
                return True
            except Exception as e:
                print(f"Error disconnecting from {self.name}: {str(e)}")
                return False
        return True
    async def call_tool(self, tool_name: str, params: Dict):
        """Call a tool on the remote server"""
        if not self.client or not self.connected:
            raise ValueError(f"Not connected to server: {self.name}")
        # Check if the tool exists
        if not tool_exists:
            raise ValueError(f"Tool '{tool_name}' not found on server: {self.name}")
        # Call the tool
        return result
    async def get_resource(self, uri: str):
        """Get a resource from the remote server"""
        if not self.client or not self.connected:
            raise ValueError(f"Not connected to server: {self.name}")
        try:
            return result
        except Exception as e:
                f"Error getting resource '{uri}' from {self.name}: {str(e)}"
# Initialize the remote server registry
async def connect_to_remote_server(name: str, url: str) -> Dict[str, Any]:
    """Attempt to connect to a remote MCP server and register it"""
    # Create client
    # Try to connect
    if not success:
        return {"error": "Failed to connect to server", "name": name, "url": url}
    # Store client
    return {
        "server_id": server_id,
        "name": name,
        "url": url,
        "tools_count": len(client.tools),
        "connected": client.connected,
async def disconnect_from_server(server_id: str) -> Dict[str, Any]:
    """Disconnect from a remote MCP server"""
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}
    if success:
        if server_id in active_clients:
        return {"server_id": server_id, "name": client.name, "disconnected": True}
    else:
        return {
            "error": "Failed to disconnect",
            "server_id": server_id,
            "name": client.name,
# Tools for bridging
@mcp.tool()
async def connect_server(name: str, url: str) -> Dict[str, Any]:
    """
    Args:
        name: Name for this server connection
        url: URL of the remote MCP server
    """
    return await connect_to_remote_server(name, url)
@mcp.tool()
async def disconnect_server(server_id: str) -> Dict[str, Any]:
    """
    Args:
        server_id: ID of the server to disconnect from
    """
    return await disconnect_from_server(server_id)
@mcp.tool()
def list_servers() -> Dict[str, Any]:
    """
    """
    for server_id, client in remote_servers.items():
                "server_id": server_id,
                "name": client.name,
                "url": client.url,
                "connected": client.connected,
                "tools_count": len(client.tools),
                "active": server_id in active_clients,
    return {
        "total_servers": len(servers),
        "active_servers": len(active_clients),
        "servers": servers,
@mcp.tool()
def get_server_details(server_id: str) -> Dict[str, Any]:
    """
    Args:
        server_id: ID of the server to get details for
    """
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}
    return {
        "server_id": server_id,
        "name": client.name,
        "url": client.url,
        "connected": client.connected,
        "active": server_id in active_clients,
        "tools": client.tools,
@mcp.tool()
async def remote_call(
    server_id: str, tool_name: str, params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Args:
        server_id: ID of the server to call
        tool_name: Name of the tool to call
        params: Parameters to pass to the tool (optional)
    """
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}
    if server_id not in active_clients:
        return {"error": "Server not connected", "server_id": server_id}
    # Default to empty dict if params not provided
    if params is None:
    try:
        return {
            "server_id": server_id,
            "server_name": client.name,
            "tool": tool_name,
            "params": params,
            "result": result,
    except Exception as e:
        return {
            "error": str(e),
            "server_id": server_id,
            "server_name": client.name,
            "tool": tool_name,
            "params": params,
@mcp.tool()
async def remote_resource(server_id: str, uri: str) -> Dict[str, Any]:
    """
    Args:
        server_id: ID of the server to get the resource from
        uri: URI of the resource to get
    """
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}
    if server_id not in active_clients:
        return {"error": "Server not connected", "server_id": server_id}
    try:
        return {
            "server_id": server_id,
            "server_name": client.name,
            "uri": uri,
            "resource": result,
    except Exception as e:
        return {
            "error": str(e),
            "server_id": server_id,
            "server_name": client.name,
            "uri": uri,
# Demo server tools
@mcp.tool()
def local_echo(message: str) -> Dict[str, Any]:
    """
    Args:
        message: Message to echo
    """
    return {
        "message": message,
        "server": "bridge",
        "timestamp": datetime.now().isoformat(),
# Demo cross-server tools
@mcp.tool()
async def cross_server_demo() -> Dict[str, Any]:
    """
    """
    # Start a simple demo server on another port
    # In a real scenario, this would be a separate server process
    # Here we're just simulating with another MCP instance
    demo_url = f"http://localhost:{demo_port}"
    results.append({"step": "Setup", "message": f"Starting demo server at {demo_url}"})
    # Connect to the demo server
    try:
        # Check if connection was successful
        if "error" in connection:
            return {
                "error": "Failed to connect to demo server",
                "message": "Make sure to run the demo server first with: python -m mcp dev 57-demo-server.py",
                "details": connection,
                "step": "Connection",
                "message": f"Connected to demo server with ID: {server_id}",
                "details": connection,
        # Call a tool on the demo server
            server_id, "echo", {"message": "Hello from bridge server!"}
                "step": "Tool Call",
                "message": "Called 'echo' tool on remote server",
                "details": echo_result,
        # Get a resource from the demo server
        resource_result = await remote_resource(server_id, "demo://info")
                "step": "Resource Access",
                "message": "Accessed 'demo://info' resource on remote server",
                "details": resource_result,
        # Disconnect from the demo server
                "step": "Disconnection",
                "message": "Disconnected from demo server",
                "details": disconnect_result,
        return {"success": True, "steps": results}
    except Exception as e:
        return {"error": str(e), "message": "Error during demo", "steps": results}
# Create a demo server file
@mcp.tool()
def create_demo_server() -> Dict[str, Any]:
    """
    """
    demo_code = """
import getpass
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
# Workaround for os.getlogin issues in some environments
# Create an MCP server on a different port
# Simple echo tool
@mcp.tool()
def echo(message: str) -> Dict[str, Any]:
    Args:
        message: Message to echo
    return {
        "message": message,
        "server": "demo",
        "timestamp": datetime.now().isoformat()
# Simple add tool
@mcp.tool()
def add(a: int, b: int) -> Dict[str, Any]:
    Args:
        a: First number
        b: Second number
    return {
        "a": a,
        "b": b,
        "result": result,
        "operation": "addition"
# Simple demo resource
@mcp.resource("demo://info")
def demo_info() -> str:
    return json.dumps({
        "name": "DemoServer",
        "port": 8199,
        "tools": ["echo", "add"],
        "resources": ["demo://info"],
        "timestamp": datetime.now().isoformat()
# Explain what this demo server does
sys.stderr.write("Run the bridge server with: python -m mcp dev 57-cross-server-bridge.py\\n")
# Run with: python -m mcp dev 57-demo-server.py
"""
    # Write the demo server file
    with open(filename, "w") as f:
    return {
        "created": True,
        "filename": filename,
        "instructions": "Run the demo server with: python -m mcp dev 57-demo-server.py",
# Shutdown handler to disconnect from all servers
def handle_shutdown(params):
    """Handle server shutdown by disconnecting from all remote servers"""
    # We can't use asyncio directly in this handler, so we'll just log
    # In a production environment, you might want to implement a synchronous
    # disconnect method to clean up connections here
# Resources
@mcp.resource("bridge://servers")
def server_list_resource() -> str:
    """Get a list of all servers as a resource"""
    return json.dumps(list_servers(), indent=2)
# Explain what this demo does when run with MCP CLI
sys.stderr.write("This example demonstrates bridging between multiple MCP servers:\n")
sys.stderr.write("To try the cross-server demo:\n")
    "2. In another terminal, start the demo server: python -m mcp dev 57-demo-server.py\n"
# This server demonstrates MCP cross-server bridging
# Run with: uv run mcp dev 57-cross-server-bridge.py

if __name__ == "__main__":
    print("MCP Server ready to run!")
    # The server will be run by MCP CLI
    
# Run with: uv run mcp dev simplified-57-cross-server-bridge.py
