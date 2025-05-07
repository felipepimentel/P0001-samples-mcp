import json
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional

from mcp.client.session import ClientSession
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MCP Client Usage")

# This example shows how an MCP server can also act as a client
# to connect to other MCP servers, enabling server-to-server communication


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Function to start an external MCP server process
async def start_external_server() -> subprocess.Popen:
    """Start an external MCP server as a separate process"""
    # Get path to 01-hello.py (assumed to be in same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "01-hello.py")

    # Create a temporary file to capture server output (for debugging)
    temp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
    temp_log.close()

    # Start the server process
    process = subprocess.Popen(
        ["python", server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=open(temp_log.name, "w"),
        universal_newlines=False,
        bufsize=0,
    )

    return process


# Client to connect to an MCP server
class McpServerClient:
    def __init__(self, process: subprocess.Popen = None):
        self.process = process
        self.client: Optional[ClientSession] = None
        self.tools: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize the MCP client connection to the server"""
        if self.process:
            # Connect to the server process via stdio
            self.client = ClientSession(
                input_stream=self.process.stdout,
                output_stream=self.process.stdin,
            )
        else:
            # This would be used for connecting to an existing server
            # Could be an SSE server or another transport mechanism
            raise ValueError("Process must be provided for stdio transport")

        # Initialize the client
        await self.client.initialize()

        # Discover and register available tools
        self.tools = {}
        tools_result = await self.client.list_tools()
        for tool in tools_result["tools"]:
            self.tools[tool["name"]] = tool

        # Discover and register available resources
        self.resources = {}
        resources_result = await self.client.list_resources()
        for resource in resources_result["resources"]:
            self.resources[resource["name"]] = resource

    async def call_tool(self, tool_name: str, **params):
        """Call a tool on the remote MCP server"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        if tool_name not in self.tools:
            available = list(self.tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not available. Available tools: {available}"
            )

        # Call the tool and return the result
        result = await self.client.call_tool(tool_name, params)
        return result["result"]

    async def read_resource(self, resource_uri: str):
        """Read a resource from the remote MCP server"""
        if not self.client:
            raise RuntimeError("Client not initialized")

        # Call the tool and return the result
        result = await self.client.read_resource(resource_uri)
        return result["value"]

    async def close(self):
        """Close the client connection and terminate the server process"""
        if self.client:
            await self.client.close()
            self.client = None

        if self.process:
            self.process.terminate()
            self.process = None


# MCP tools to interact with external MCP servers
@mcp.tool()
async def call_external_add(a: int, b: int) -> str:
    """
    Call the 'add' tool on an external MCP server

    Args:
        a: First number
        b: Second number
    """
    try:
        # Start an external MCP server
        process = await start_external_server()

        # Connect to the server
        client = McpServerClient(process)
        await client.initialize()

        # Call the 'add' tool
        result = await client.call_tool("add", a=a, b=b)

        # Close the connection
        await client.close()

        return f"External server returned: {result}"
    except Exception as e:
        return f"Error calling external server: {str(e)}"


@mcp.tool()
async def get_external_greeting(name: str) -> str:
    """
    Get a greeting from an external MCP server

    Args:
        name: Name to include in the greeting
    """
    try:
        # Start an external MCP server
        process = await start_external_server()

        # Connect to the server
        client = McpServerClient(process)
        await client.initialize()

        # Get a list of available resources
        resources = list(client.resources.keys())

        # Read the greeting resource
        resource_uri = f"greeting://{name}"
        greeting = await client.read_resource(resource_uri)

        # Close the connection
        await client.close()

        return f"External server resources: {resources}\nGreeting: {greeting}"
    except Exception as e:
        return f"Error reading from external server: {str(e)}"


@mcp.tool()
async def list_external_capabilities() -> str:
    """List all tools and resources available on the external MCP server"""
    try:
        # Start an external MCP server
        process = await start_external_server()

        # Connect to the server
        client = McpServerClient(process)
        await client.initialize()

        # Get available tools and resources
        tools = list(client.tools.keys())
        resources = list(client.resources.keys())

        # Close the connection
        await client.close()

        result = {"tools": tools, "resources": resources}

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error connecting to external server: {str(e)}"
