import asyncio
import getpass
import json
import os
import sys
import uuid
from typing import Any, Dict, Optional

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# JSON-RPC Constants
JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"


class RawMCPClient:
    """
    A minimal MCP client implemented directly with JSON-RPC

    This bypasses the MCP SDK to demonstrate the raw protocol from the client side.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.session_id = str(uuid.uuid4())
        self.request_id = 1
        self.initialized = False
        self.server_capabilities = None
        self.server_info = None
        self.available_tools = {}

        # Set up client capabilities
        self.capabilities = {
            "protocol_version": MCP_PROTOCOL_VERSION,
            "features": {
                "resources": {"supported": True},
                "tools": {"supported": True},
            },
        }

    async def connect(self, server_command: Optional[str] = None):
        """
        Connect to an MCP server

        If server_command is provided, it will be started as a subprocess.
        Otherwise, it assumes the server is already running on stdin/stdout.
        """
        self.reader = asyncio.StreamReader()
        self.writer = None

        if server_command:
            # Start server as subprocess
            sys.stderr.write(f"Starting server process: {server_command}\n")
            process = await asyncio.create_subprocess_shell(
                server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=sys.stderr,
            )

            self.process = process
            self.reader = process.stdout
            self.writer = process.stdin
        else:
            # Use standard IO
            reader_protocol = asyncio.StreamReaderProtocol(self.reader)

            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

            self.writer_transport, _ = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin, sys.stdout
            )
            self.writer = asyncio.StreamWriter(
                self.writer_transport, protocol=None, reader=None, loop=loop
            )

        # Initialize the session
        await self.initialize()

    async def initialize(self):
        """Initialize the session with the server"""
        sys.stderr.write("Initializing MCP session...\n")

        # Build initialization request
        init_params = {
            "session_id": self.session_id,
            "client_info": {"name": self.name, "version": self.version},
            "capabilities": self.capabilities,
        }

        # Send initialization request
        response = await self.send_request("initialize", init_params)

        if response and "result" in response:
            self.initialized = True
            self.server_capabilities = response["result"].get("capabilities")
            self.server_info = response["result"].get("serverInfo")

            # Log server info
            sys.stderr.write(
                f"Connected to {self.server_info.get('name', 'unknown')} {self.server_info.get('version', '')}\n"
            )
            sys.stderr.write(
                f"Server capabilities: {json.dumps(self.server_capabilities, indent=2)}\n"
            )

            # Get available tools
            await self.list_tools()

            return True
        else:
            error = (
                response.get("error", {}) if response else {"message": "No response"}
            )
            sys.stderr.write(
                f"Initialization failed: {error.get('message', 'Unknown error')}\n"
            )
            return False

    async def list_tools(self):
        """List available tools from the server"""
        response = await self.send_request("tools/list", {})

        if response and "result" in response:
            tools = response["result"].get("tools", [])

            # Store tools by name
            for tool in tools:
                self.available_tools[tool["name"]] = tool

            return tools
        else:
            error = (
                response.get("error", {}) if response else {"message": "No response"}
            )
            sys.stderr.write(
                f"Failed to list tools: {error.get('message', 'Unknown error')}\n"
            )
            return []

    async def call_tool(self, tool_name: str, params: Dict[str, Any] = None):
        """Call a tool on the server"""
        if not self.initialized:
            sys.stderr.write("Client not initialized. Call initialize() first.\n")
            return None

        if tool_name not in self.available_tools:
            sys.stderr.write(
                f"Tool '{tool_name}' not available. Available tools: {', '.join(self.available_tools.keys())}\n"
            )
            return None

        params = params or {}

        # Create tool call request
        tool_params = {"name": tool_name, "params": params}

        # Send the request
        response = await self.send_request("tools/call", tool_params)

        if response and "result" in response:
            return response["result"].get("result")
        else:
            error = (
                response.get("error", {}) if response else {"message": "No response"}
            )
            sys.stderr.write(
                f"Tool call failed: {error.get('message', 'Unknown error')}\n"
            )
            return None

    async def get_resource(self, uri: str):
        """Get a resource from the server"""
        if not self.initialized:
            sys.stderr.write("Client not initialized. Call initialize() first.\n")
            return None

        # Create resource request
        resource_params = {"uri": uri}

        # Send the request
        response = await self.send_request("resources/get", resource_params)

        if response and "result" in response:
            return {
                "content": response["result"].get("content"),
                "contentType": response["result"].get("contentType"),
            }
        else:
            error = (
                response.get("error", {}) if response else {"message": "No response"}
            )
            sys.stderr.write(
                f"Resource request failed: {error.get('message', 'Unknown error')}\n"
            )
            return None

    async def shutdown(self):
        """Shut down the session"""
        if not self.initialized:
            return True

        # Send shutdown request
        response = await self.send_request("shutdown", {})

        if response and "result" in response:
            self.initialized = False
            sys.stderr.write("Session shut down successfully\n")
            return True
        else:
            error = (
                response.get("error", {}) if response else {"message": "No response"}
            )
            sys.stderr.write(
                f"Shutdown failed: {error.get('message', 'Unknown error')}\n"
            )
            return False

    async def send_request(self, method: str, params: Dict):
        """Send a JSON-RPC request and await response"""
        request_id = self.request_id
        self.request_id += 1

        # Create the request
        request = {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Format and send the request
        request_str = json.dumps(request) + "\n"

        if not self.writer:
            sys.stderr.write("No connection to server\n")
            return None

        # Log outgoing request
        sys.stderr.write(f"--> Sending: {method} (ID: {request_id})\n")

        # Write request to stdout or subprocess stdin
        if isinstance(self.writer, asyncio.StreamWriter):
            self.writer.write(request_str.encode("utf-8"))
            await self.writer.drain()
        else:
            self.writer.write(request_str.encode("utf-8"))
            await self.writer.drain()

        # Wait for response with matching ID
        while True:
            try:
                if isinstance(self.reader, asyncio.StreamReader):
                    line = await self.reader.readline()
                else:
                    line = await self.reader.readline()

                if not line:
                    sys.stderr.write("Connection closed by server\n")
                    break

                # Parse the response
                response_str = line.decode("utf-8").strip()
                if response_str:
                    response = json.loads(response_str)

                    # Check if this is a response to our request
                    if "id" in response and response["id"] == request_id:
                        if "error" in response:
                            sys.stderr.write(
                                f"<-- Error: {response['error'].get('message')}\n"
                            )
                        else:
                            sys.stderr.write(
                                f"<-- Received response for ID: {request_id}\n"
                            )
                        return response
            except json.JSONDecodeError:
                sys.stderr.write(f"Invalid JSON received: {response_str}\n")
            except Exception as e:
                sys.stderr.write(f"Error receiving response: {str(e)}\n")
                break

        return None


async def interactive_session(client):
    """Run an interactive client session"""
    print("\n=== MCP CLIENT INTERACTIVE MODE ===")
    print("Available commands:")
    print("  tools            - List available tools")
    print("  call TOOL PARAMS - Call a tool (PARAMS as JSON)")
    print("  get URI          - Get a resource")
    print("  quit             - Exit the session")
    print("======================================\n")

    while True:
        try:
            command = input("> ")
            parts = command.strip().split(maxsplit=2)

            if not parts:
                continue

            action = parts[0].lower()

            if action == "quit" or action == "exit":
                await client.shutdown()
                break

            elif action == "tools":
                tools = client.available_tools
                print("Available tools:")
                for name, tool in tools.items():
                    print(f"  - {name}: {tool.get('description', '')}")

            elif action == "call" and len(parts) >= 2:
                tool_name = parts[1]
                params = {}

                if len(parts) > 2:
                    try:
                        params = json.loads(parts[2])
                    except json.JSONDecodeError:
                        print(f"Invalid JSON parameters: {parts[2]}")
                        continue

                result = await client.call_tool(tool_name, params)
                print(f"Result: {json.dumps(result, indent=2)}")

            elif action == "get" and len(parts) >= 2:
                uri = parts[1]
                result = await client.get_resource(uri)
                if result:
                    print(f"Content-Type: {result.get('contentType', 'text/plain')}")
                    print(f"Content: {result.get('content', '')}")

            else:
                print(f"Unknown command: {action}")
                print("Available commands: tools, call, get, quit")

        except KeyboardInterrupt:
            print("\nExiting...")
            await client.shutdown()
            break
        except Exception as e:
            print(f"Error: {str(e)}")


async def demo_session(client):
    """Run a demonstration session with preset commands"""
    print("\n=== MCP CLIENT DEMO MODE ===")
    print("This will automatically run several commands to demonstrate the client")

    # List available tools
    print("\n=== Listing available tools ===")
    tools = client.available_tools
    for name, tool in tools.items():
        print(f"  - {name}: {tool.get('description', '')}")

    # Call the echo tool
    print("\n=== Calling echo tool ===")
    result = await client.call_tool("echo", {"message": "Hello from raw MCP client!"})
    print(f"Result: {result}")

    # Get server time
    print("\n=== Getting server time ===")
    result = await client.call_tool("get_server_time")
    print(f"Server time: {json.dumps(result, indent=2)}")

    # Get system info
    print("\n=== Getting system info ===")
    result = await client.call_tool("get_system_info")
    print(f"System info: {json.dumps(result, indent=2)}")

    # Get a resource
    print("\n=== Getting user profile resource ===")
    result = await client.get_resource("users/1/profile")
    if result:
        print(f"User profile: {result.get('content')}")

    # Get server info resource
    print("\n=== Getting server info resource ===")
    result = await client.get_resource("server/info.json")
    if result:
        print(f"Server info: {result.get('content')}")

    # Shut down the session
    print("\n=== Shutting down session ===")
    await client.shutdown()
    print("Demo completed")


async def main():
    """Run the MCP client"""
    # Determine mode from command line arguments
    mode = "interactive"
    server_command = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            mode = "demo"
        elif sys.argv[1] == "--server":
            if len(sys.argv) > 2:
                server_command = sys.argv[2]

    # Create client
    client = RawMCPClient("RawMCPClient", "1.0.0")

    try:
        # Connect to server
        await client.connect(server_command)

        # Run session based on mode
        if mode == "demo":
            await demo_session(client)
        else:
            await interactive_session(client)

    except Exception as e:
        sys.stderr.write(f"Client error: {str(e)}\n")

    finally:
        # Ensure proper shutdown
        if client.initialized:
            await client.shutdown()


# Print intro when run with the MCP CLI
if __name__ != "__main__":
    sys.stderr.write("\n=== RAW MCP CLIENT IMPLEMENTATION ===\n")
    sys.stderr.write("This example demonstrates a minimal MCP client implementation\n")
    sys.stderr.write("using raw JSON-RPC instead of the MCP SDK.\n\n")
    sys.stderr.write("Usage:\n")
    sys.stderr.write(
        "  python 44-client-implementation.py           # Interactive mode\n"
    )
    sys.stderr.write(
        "  python 44-client-implementation.py --demo    # Demonstration mode\n"
    )
    sys.stderr.write(
        '  python 44-client-implementation.py --server "python 43-raw-protocol.py"  # Connect to specific server\n\n'
    )
    sys.stderr.write(
        "The client can connect to any MCP server, including the raw protocol server\n"
    )
    sys.stderr.write("from the previous example (43-raw-protocol.py).\n")
    sys.stderr.write("=== END CLIENT IMPLEMENTATION INFO ===\n\n")
else:
    # Create and run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        sys.stderr.write("Client stopped by user\n")
    finally:
        loop.close()

# This client demonstrates the raw MCP protocol without using the SDK
# Run with: python 44-client-implementation.py
