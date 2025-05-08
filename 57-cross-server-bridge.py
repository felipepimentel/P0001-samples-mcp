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
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("MCPBridgeServer")

# Track remote MCP servers
remote_servers = {}
active_clients = {}


# MCP Client class to connect to remote servers
class RemoteMCPClient:
    def __init__(self, server_id, name, url):
        """Initialize remote MCP client"""
        self.server_id = server_id
        self.name = name
        self.url = url
        self.client = None
        self.tools = []
        self.resources = []
        self.connected = False

    async def connect(self):
        """Connect to the remote MCP server"""
        try:
            # Create and initialize client
            self.client = McpClient(self.url)
            await self.client.initialize()
            self.connected = True

            # Discover available tools
            tools_result = await self.client.list_tools()
            self.tools = tools_result.get("tools", [])

            return True
        except Exception as e:
            print(f"Error connecting to {self.name}: {str(e)}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from the remote MCP server"""
        if self.client and self.connected:
            try:
                await self.client.shutdown()
                self.connected = False
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
        tool_exists = any(tool["name"] == tool_name for tool in self.tools)
        if not tool_exists:
            raise ValueError(f"Tool '{tool_name}' not found on server: {self.name}")

        # Call the tool
        result = await self.client.call_tool(tool_name, params)
        return result

    async def get_resource(self, uri: str):
        """Get a resource from the remote server"""
        if not self.client or not self.connected:
            raise ValueError(f"Not connected to server: {self.name}")

        try:
            result = await self.client.get_resource(uri)
            return result
        except Exception as e:
            raise ValueError(
                f"Error getting resource '{uri}' from {self.name}: {str(e)}"
            )


# Initialize the remote server registry
async def connect_to_remote_server(name: str, url: str) -> Dict[str, Any]:
    """Attempt to connect to a remote MCP server and register it"""
    server_id = str(uuid4())

    # Create client
    client = RemoteMCPClient(server_id, name, url)

    # Try to connect
    success = await client.connect()
    if not success:
        return {"error": "Failed to connect to server", "name": name, "url": url}

    # Store client
    remote_servers[server_id] = client
    active_clients[server_id] = client

    return {
        "server_id": server_id,
        "name": name,
        "url": url,
        "tools_count": len(client.tools),
        "connected": client.connected,
    }


async def disconnect_from_server(server_id: str) -> Dict[str, Any]:
    """Disconnect from a remote MCP server"""
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}

    client = remote_servers[server_id]
    success = await client.disconnect()

    if success:
        if server_id in active_clients:
            del active_clients[server_id]

        return {"server_id": server_id, "name": client.name, "disconnected": True}
    else:
        return {
            "error": "Failed to disconnect",
            "server_id": server_id,
            "name": client.name,
        }


# Tools for bridging
@mcp.tool()
async def connect_server(name: str, url: str) -> Dict[str, Any]:
    """
    Connect to a remote MCP server

    Args:
        name: Name for this server connection
        url: URL of the remote MCP server

    Returns the server ID and connection status
    """
    return await connect_to_remote_server(name, url)


@mcp.tool()
async def disconnect_server(server_id: str) -> Dict[str, Any]:
    """
    Disconnect from a remote MCP server

    Args:
        server_id: ID of the server to disconnect from

    Returns the disconnection status
    """
    return await disconnect_from_server(server_id)


@mcp.tool()
def list_servers() -> Dict[str, Any]:
    """
    List all registered remote MCP servers

    Returns a list of all servers and their connection status
    """
    servers = []

    for server_id, client in remote_servers.items():
        servers.append(
            {
                "server_id": server_id,
                "name": client.name,
                "url": client.url,
                "connected": client.connected,
                "tools_count": len(client.tools),
                "active": server_id in active_clients,
            }
        )

    return {
        "total_servers": len(servers),
        "active_servers": len(active_clients),
        "servers": servers,
    }


@mcp.tool()
def get_server_details(server_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a remote MCP server

    Args:
        server_id: ID of the server to get details for

    Returns detailed information about the server and available tools
    """
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}

    client = remote_servers[server_id]

    return {
        "server_id": server_id,
        "name": client.name,
        "url": client.url,
        "connected": client.connected,
        "active": server_id in active_clients,
        "tools": client.tools,
    }


@mcp.tool()
async def remote_call(
    server_id: str, tool_name: str, params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Call a tool on a remote MCP server

    Args:
        server_id: ID of the server to call
        tool_name: Name of the tool to call
        params: Parameters to pass to the tool (optional)

    Returns the result from the remote tool call
    """
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}

    if server_id not in active_clients:
        return {"error": "Server not connected", "server_id": server_id}

    client = active_clients[server_id]

    # Default to empty dict if params not provided
    if params is None:
        params = {}

    try:
        result = await client.call_tool(tool_name, params)

        return {
            "server_id": server_id,
            "server_name": client.name,
            "tool": tool_name,
            "params": params,
            "result": result,
        }
    except Exception as e:
        return {
            "error": str(e),
            "server_id": server_id,
            "server_name": client.name,
            "tool": tool_name,
            "params": params,
        }


@mcp.tool()
async def remote_resource(server_id: str, uri: str) -> Dict[str, Any]:
    """
    Get a resource from a remote MCP server

    Args:
        server_id: ID of the server to get the resource from
        uri: URI of the resource to get

    Returns the resource from the remote server
    """
    if server_id not in remote_servers:
        return {"error": "Server not found", "server_id": server_id}

    if server_id not in active_clients:
        return {"error": "Server not connected", "server_id": server_id}

    client = active_clients[server_id]

    try:
        result = await client.get_resource(uri)

        return {
            "server_id": server_id,
            "server_name": client.name,
            "uri": uri,
            "resource": result,
        }
    except Exception as e:
        return {
            "error": str(e),
            "server_id": server_id,
            "server_name": client.name,
            "uri": uri,
        }


# Demo server tools
@mcp.tool()
def local_echo(message: str) -> Dict[str, Any]:
    """
    Echo a message from the bridge server

    Args:
        message: Message to echo

    Returns the echoed message
    """
    return {
        "message": message,
        "server": "bridge",
        "timestamp": datetime.now().isoformat(),
    }


# Demo cross-server tools
@mcp.tool()
async def cross_server_demo() -> Dict[str, Any]:
    """
    Demonstrate cross-server communication

    This tool sets up a demo showing how to bridge multiple MCP servers
    """
    results = []

    # Start a simple demo server on another port
    # In a real scenario, this would be a separate server process
    # Here we're just simulating with another MCP instance
    demo_port = 8199
    demo_url = f"http://localhost:{demo_port}"

    results.append({"step": "Setup", "message": f"Starting demo server at {demo_url}"})

    # Connect to the demo server
    try:
        connection = await connect_to_remote_server("DemoServer", demo_url)

        # Check if connection was successful
        if "error" in connection:
            return {
                "error": "Failed to connect to demo server",
                "message": "Make sure to run the demo server first with: python -m mcp dev 57-demo-server.py",
                "details": connection,
            }

        server_id = connection["server_id"]

        results.append(
            {
                "step": "Connection",
                "message": f"Connected to demo server with ID: {server_id}",
                "details": connection,
            }
        )

        # Call a tool on the demo server
        echo_result = await remote_call(
            server_id, "echo", {"message": "Hello from bridge server!"}
        )

        results.append(
            {
                "step": "Tool Call",
                "message": "Called 'echo' tool on remote server",
                "details": echo_result,
            }
        )

        # Get a resource from the demo server
        resource_result = await remote_resource(server_id, "demo://info")

        results.append(
            {
                "step": "Resource Access",
                "message": "Accessed 'demo://info' resource on remote server",
                "details": resource_result,
            }
        )

        # Disconnect from the demo server
        disconnect_result = await disconnect_from_server(server_id)

        results.append(
            {
                "step": "Disconnection",
                "message": "Disconnected from demo server",
                "details": disconnect_result,
            }
        )

        return {"success": True, "steps": results}
    except Exception as e:
        return {"error": str(e), "message": "Error during demo", "steps": results}


# Create a demo server file
@mcp.tool()
def create_demo_server() -> Dict[str, Any]:
    """
    Create a demo server file to use with this bridge

    This tool creates a Python file with a simple MCP server that can be used
    with the bridge for testing cross-server communication
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
os.getlogin = getpass.getuser

# Create an MCP server on a different port
mcp = FastMCP("DemoServer", port=8199)

# Simple echo tool
@mcp.tool()
def echo(message: str) -> Dict[str, Any]:
    \"\"\"
    Echo a message back
    
    Args:
        message: Message to echo
        
    Returns the message with server information
    \"\"\"
    return {
        "message": message,
        "server": "demo",
        "timestamp": datetime.now().isoformat()
    }

# Simple add tool
@mcp.tool()
def add(a: int, b: int) -> Dict[str, Any]:
    \"\"\"
    Add two numbers
    
    Args:
        a: First number
        b: Second number
        
    Returns the sum of the two numbers
    \"\"\"
    result = a + b
    return {
        "a": a,
        "b": b,
        "result": result,
        "operation": "addition"
    }

# Simple demo resource
@mcp.resource("demo://info")
def demo_info() -> str:
    \"\"\"Get information about this demo server\"\"\"
    return json.dumps({
        "name": "DemoServer",
        "port": 8199,
        "tools": ["echo", "add"],
        "resources": ["demo://info"],
        "timestamp": datetime.now().isoformat()
    }, indent=2)

# Explain what this demo server does
sys.stderr.write("\\n=== MCP DEMO SERVER ===\\n")
sys.stderr.write("This is a simple demo server for the MCP Bridge example.\\n")
sys.stderr.write("It provides basic tools and resources for testing cross-server communication.\\n")
sys.stderr.write("Run the bridge server with: python -m mcp dev 57-cross-server-bridge.py\\n")
sys.stderr.write("=== END DEMO SERVER INFO ===\\n\\n")

# Run with: python -m mcp dev 57-demo-server.py
"""

    # Write the demo server file
    filename = "57-demo-server.py"
    with open(filename, "w") as f:
        f.write(demo_code.strip())

    return {
        "created": True,
        "filename": filename,
        "instructions": "Run the demo server with: python -m mcp dev 57-demo-server.py",
    }


# Shutdown handler to disconnect from all servers
@mcp.shutdown
def handle_shutdown(params):
    """Handle server shutdown by disconnecting from all remote servers"""
    # We can't use asyncio directly in this handler, so we'll just log
    sys.stderr.write("Shutting down, disconnecting from all remote servers...\n")

    # In a production environment, you might want to implement a synchronous
    # disconnect method to clean up connections here


# Resources
@mcp.resource("bridge://servers")
def server_list_resource() -> str:
    """Get a list of all servers as a resource"""
    return json.dumps(list_servers(), indent=2)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP CROSS-SERVER BRIDGE ===\n")
sys.stderr.write("This example demonstrates bridging between multiple MCP servers:\n")
sys.stderr.write("1. Connect to remote MCP servers\n")
sys.stderr.write("2. Discover and call tools on remote servers\n")
sys.stderr.write("3. Access resources from remote servers\n")
sys.stderr.write("4. Manage connections to multiple servers\n\n")
sys.stderr.write("To try the cross-server demo:\n")
sys.stderr.write("1. First run 'create_demo_server' to generate the demo server file\n")
sys.stderr.write(
    "2. In another terminal, start the demo server: python -m mcp dev 57-demo-server.py\n"
)
sys.stderr.write(
    "3. Then run 'cross_server_demo' to see cross-server communication in action\n"
)
sys.stderr.write("=== END CROSS-SERVER BRIDGE INFO ===\n\n")

# This server demonstrates MCP cross-server bridging
# Run with: uv run mcp dev 57-cross-server-bridge.py
