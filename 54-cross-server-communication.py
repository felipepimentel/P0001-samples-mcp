import asyncio
import getpass
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from mcp.client import MCPClient
from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("CrossServerCommunicationDemo")

# Track remote server connections
remote_servers = {}
service_registry = {}


# Process to run sub-servers
def start_service_server(port, service_type):
    """Start a specialized service server in a subprocess"""
    env = os.environ.copy()
    env["MCP_SERVICE_TYPE"] = service_type
    env["MCP_SERVICE_PORT"] = str(port)

    # Command to run the server
    cmd = [sys.executable, __file__, "--service", service_type, "--port", str(port)]

    # Start the server as a subprocess
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Allow time for server to start
    time.sleep(1)

    return process


# MCP client for communicating with other servers
async def connect_to_server(service_id, host, port):
    """Connect to a remote MCP server"""
    # Create a client
    client = MCPClient()

    # Connect to the server via HTTP
    await client.connect_http(f"http://{host}:{port}/mcp")

    # Register the client
    remote_servers[service_id] = {
        "client": client,
        "host": host,
        "port": port,
        "connected_at": datetime.now().isoformat(),
    }

    # Get server info
    try:
        server_info = await client.call_tool("get_service_info")
        remote_servers[service_id]["info"] = server_info
        service_registry[service_id] = server_info
        sys.stderr.write(
            f"Connected to service: {service_id} ({server_info.get('service_type')})\n"
        )
    except Exception as e:
        sys.stderr.write(f"Error getting service info: {str(e)}\n")

    return client


# Tools for managing remote servers
@mcp.tool()
def list_remote_servers() -> Dict[str, Any]:
    """
    List all registered remote MCP servers

    Returns information about connected servers.
    """
    servers = []

    for server_id, server in remote_servers.items():
        servers.append(
            {
                "id": server_id,
                "host": server["host"],
                "port": server["port"],
                "connected_at": server["connected_at"],
                "info": server.get("info", {}),
            }
        )

    return {"server_count": len(servers), "servers": servers}


@mcp.tool()
def register_service(service_type: str, port: Optional[int] = None) -> Dict[str, Any]:
    """
    Register a new service server of the specified type

    Args:
        service_type: Type of service to register ('database', 'calculator', or 'translator')
        port: Port to run the service on (optional, will use a random port if not specified)

    This starts a new specialized MCP server as a child process.
    """
    # Validate service type
    valid_types = ["database", "calculator", "translator"]
    if service_type not in valid_types:
        return {
            "error": f"Invalid service type: {service_type}. Must be one of: {', '.join(valid_types)}"
        }

    # Generate a random port if not specified
    if port is None:
        # Use a port in the range 8100-8199
        port = 8100 + len(remote_servers) % 100

    # Start the service
    process = start_service_server(port, service_type)

    # Generate a service ID
    service_id = f"{service_type}-{uuid.uuid4().hex[:8]}"

    # Set up an async event loop to connect to the server
    loop = asyncio.new_event_loop()

    try:
        # Connect to the server
        client = loop.run_until_complete(
            connect_to_server(service_id, "localhost", port)
        )

        return {
            "status": "success",
            "message": f"Service {service_type} started on port {port}",
            "service_id": service_id,
            "port": port,
        }
    except Exception as e:
        return {"error": f"Failed to connect to service: {str(e)}"}
    finally:
        loop.close()


@mcp.tool()
def call_remote_service(
    service_id: str, tool_name: str, parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Call a tool on a remote MCP server

    Args:
        service_id: ID of the registered service
        tool_name: Name of the tool to call
        parameters: Parameters to pass to the tool

    This demonstrates cross-server MCP communication.
    """
    # Check if the service exists
    if service_id not in remote_servers:
        return {"error": f"Service not found: {service_id}"}

    # Get the client
    server = remote_servers[service_id]
    client = server["client"]

    # Create an async event loop
    loop = asyncio.new_event_loop()

    try:
        # Call the remote tool
        parameters = parameters or {}
        result = loop.run_until_complete(client.call_tool(tool_name, **parameters))

        return {
            "service_id": service_id,
            "tool": tool_name,
            "parameters": parameters,
            "result": result,
        }
    except Exception as e:
        return {"error": f"Error calling remote tool: {str(e)}"}
    finally:
        loop.close()


@mcp.tool()
def get_remote_resource(service_id: str, resource_uri: str) -> Dict[str, Any]:
    """
    Get a resource from a remote MCP server

    Args:
        service_id: ID of the registered service
        resource_uri: URI of the resource to retrieve

    This demonstrates cross-server resource access.
    """
    # Check if the service exists
    if service_id not in remote_servers:
        return {"error": f"Service not found: {service_id}"}

    # Get the client
    server = remote_servers[service_id]
    client = server["client"]

    # Create an async event loop
    loop = asyncio.new_event_loop()

    try:
        # Get the remote resource
        result = loop.run_until_complete(client.get_resource(resource_uri))

        return {
            "service_id": service_id,
            "resource_uri": resource_uri,
            "content": result,
        }
    except Exception as e:
        return {"error": f"Error getting remote resource: {str(e)}"}
    finally:
        loop.close()


@mcp.tool()
def orchestrate_multi_service_task(
    task_description: str,
    database_query: Optional[str] = None,
    calculation: Optional[Dict[str, Any]] = None,
    text_to_translate: Optional[str] = None,
    target_language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a task across multiple specialized services

    Args:
        task_description: Description of the task to perform
        database_query: Optional query to run on the database service
        calculation: Optional calculation to perform with the calculator service
        text_to_translate: Optional text to translate using the translator service
        target_language: Optional target language for translation

    This demonstrates orchestrating a complex task across multiple MCP servers.
    """
    results = {
        "task_description": task_description,
        "timestamp": datetime.now().isoformat(),
        "services_used": [],
        "errors": [],
        "database_result": None,
        "calculation_result": None,
        "translation_result": None,
    }

    # Find available services
    database_service = next(
        (
            sid
            for sid, info in service_registry.items()
            if info.get("service_type") == "database"
        ),
        None,
    )
    calculator_service = next(
        (
            sid
            for sid, info in service_registry.items()
            if info.get("service_type") == "calculator"
        ),
        None,
    )
    translator_service = next(
        (
            sid
            for sid, info in service_registry.items()
            if info.get("service_type") == "translator"
        ),
        None,
    )

    # Start any missing services
    if database_query and not database_service:
        db_result = register_service("database")
        if "error" not in db_result:
            database_service = db_result["service_id"]
        else:
            results["errors"].append(
                f"Failed to start database service: {db_result.get('error')}"
            )

    if calculation and not calculator_service:
        calc_result = register_service("calculator")
        if "error" not in calc_result:
            calculator_service = calc_result["service_id"]
        else:
            results["errors"].append(
                f"Failed to start calculator service: {calc_result.get('error')}"
            )

    if text_to_translate and not translator_service:
        trans_result = register_service("translator")
        if "error" not in trans_result:
            translator_service = trans_result["service_id"]
        else:
            results["errors"].append(
                f"Failed to start translator service: {trans_result.get('error')}"
            )

    # Execute database query
    if database_query and database_service:
        db_result = call_remote_service(
            database_service, "query_database", {"query": database_query}
        )
        results["services_used"].append(database_service)
        results["database_result"] = db_result

    # Execute calculation
    if calculation and calculator_service:
        calc_result = call_remote_service(calculator_service, "calculate", calculation)
        results["services_used"].append(calculator_service)
        results["calculation_result"] = calc_result

    # Execute translation
    if text_to_translate and translator_service:
        trans_result = call_remote_service(
            translator_service,
            "translate_text",
            {"text": text_to_translate, "target_language": target_language or "es"},
        )
        results["services_used"].append(translator_service)
        results["translation_result"] = trans_result

    return results


# Resources to expose server information
@mcp.resource("services")
def get_services_resource() -> str:
    """Get information about all registered services"""
    return json.dumps(
        {"services": service_registry, "count": len(service_registry)}, indent=2
    )


@mcp.resource("services/{service_id}")
def get_service_resource(service_id: str) -> str:
    """Get information about a specific service"""
    if service_id in service_registry:
        return json.dumps(service_registry[service_id], indent=2)
    else:
        return json.dumps({"error": f"Service not found: {service_id}"})


# SERVICE IMPLEMENTATION
# This section defines the specialized service servers that can be started by the main server


# Service server class
class ServiceServer:
    """Base class for specialized service servers"""

    def __init__(self, service_type, port):
        self.service_type = service_type
        self.port = port
        self.server = FastMCP(f"MCP-{service_type.capitalize()}-Service")
        self.setup_tools()

    def setup_tools(self):
        """Set up the tools for this service - override in subclasses"""
        pass

    def run(self):
        """Run the service server using FastAPI"""
        try:
            import uvicorn
            from fastapi import FastAPI

            # Create FastAPI app
            app = FastAPI(title=f"MCP {self.service_type.capitalize()} Service")

            # Add MCP HTTP endpoint
            @app.post("/mcp")
            async def mcp_endpoint(data: Dict[str, Any]):
                response = await self.server.process_http_message(data)
                return response

            # Add info endpoint
            @app.get("/")
            async def info():
                return {
                    "service_type": self.service_type,
                    "port": self.port,
                    "version": "1.0.0",
                    "description": f"MCP {self.service_type.capitalize()} Service",
                }

            # Register basic tools on all services
            @self.server.tool()
            def get_service_info() -> Dict[str, Any]:
                """Get information about this service"""
                return {
                    "service_type": self.service_type,
                    "port": self.port,
                    "version": "1.0.0",
                    "description": f"MCP {self.service_type.capitalize()} Service",
                    "started_at": datetime.now().isoformat(),
                }

            # Run the server
            sys.stderr.write(
                f"Starting {self.service_type} service on port {self.port}\n"
            )
            uvicorn.run(app, host="0.0.0.0", port=self.port)

        except Exception as e:
            sys.stderr.write(f"Error starting service server: {str(e)}\n")


class DatabaseService(ServiceServer):
    """Database service implementation"""

    def setup_tools(self):
        # Simulated database storage
        self.data = {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            ],
            "products": [
                {"id": 101, "name": "Laptop", "price": 999.99},
                {"id": 102, "name": "Smartphone", "price": 699.99},
                {"id": 103, "name": "Headphones", "price": 149.99},
            ],
            "orders": [
                {
                    "id": 1001,
                    "user_id": 1,
                    "product_id": 101,
                    "quantity": 1,
                    "date": "2025-01-15",
                },
                {
                    "id": 1002,
                    "user_id": 2,
                    "product_id": 103,
                    "quantity": 2,
                    "date": "2025-01-16",
                },
                {
                    "id": 1003,
                    "user_id": 3,
                    "product_id": 102,
                    "quantity": 1,
                    "date": "2025-01-17",
                },
            ],
        }

        # Register database-specific tools
        @self.server.tool()
        def query_database(query: str) -> Dict[str, Any]:
            """Query the database with a simple query language"""
            parts = query.strip().lower().split()
            if len(parts) < 2:
                return {
                    "error": "Invalid query format. Use: GET <table> [WHERE <field>=<value>]"
                }

            command, table = parts[0], parts[1]

            if command != "get":
                return {
                    "error": f"Unsupported command: {command}. Only GET is supported."
                }

            if table not in self.data:
                return {"error": f"Table not found: {table}"}

            # Select all records from the table
            results = self.data[table].copy()

            # Apply filters if WHERE clause exists
            if len(parts) > 2 and parts[2] == "where" and len(parts) > 3:
                filter_expr = " ".join(parts[3:])

                # Simple parsing of field=value
                if "=" in filter_expr:
                    field, value = filter_expr.split("=", 1)
                    field = field.strip()
                    value = value.strip().strip("'\"")

                    # Try to convert value to number if possible
                    try:
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass

                    # Filter the results
                    results = [r for r in results if str(r.get(field)) == str(value)]

            return {
                "query": query,
                "table": table,
                "count": len(results),
                "results": results,
            }

        @self.server.resource("tables")
        def get_tables() -> str:
            """Get a list of all tables"""
            tables = []
            for table_name, records in self.data.items():
                tables.append(
                    {
                        "name": table_name,
                        "record_count": len(records),
                        "fields": list(records[0].keys()) if records else [],
                    }
                )

            return json.dumps(
                {
                    "tables": tables,
                    "count": len(tables),
                },
                indent=2,
            )

        @self.server.resource("tables/{table}")
        def get_table(table: str) -> str:
            """Get all records in a table"""
            if table in self.data:
                return json.dumps(
                    {
                        "table": table,
                        "records": self.data[table],
                        "count": len(self.data[table]),
                    },
                    indent=2,
                )
            else:
                return json.dumps({"error": f"Table not found: {table}"})


class CalculatorService(ServiceServer):
    """Calculator service implementation"""

    def setup_tools(self):
        # Register calculator-specific tools
        @self.server.tool()
        def calculate(
            operation: str, x: float, y: Optional[float] = None, precision: int = 2
        ) -> Dict[str, Any]:
            """Perform a calculation"""
            # Validate operation
            valid_ops = [
                "add",
                "subtract",
                "multiply",
                "divide",
                "power",
                "sqrt",
                "log",
            ]
            if operation not in valid_ops:
                return {
                    "error": f"Invalid operation. Supported: {', '.join(valid_ops)}"
                }

            # Validate parameters
            if (
                operation in ["add", "subtract", "multiply", "divide", "power"]
                and y is None
            ):
                return {
                    "error": f"Operation '{operation}' requires two operands (x and y)"
                }

            if operation == "divide" and y == 0:
                return {"error": "Division by zero"}

            # Perform the calculation
            result = None
            if operation == "add":
                result = x + y
            elif operation == "subtract":
                result = x - y
            elif operation == "multiply":
                result = x * y
            elif operation == "divide":
                result = x / y
            elif operation == "power":
                result = x**y
            elif operation == "sqrt":
                result = x**0.5
            elif operation == "log":
                import math

                if y is not None:
                    # Log with custom base
                    result = math.log(x, y)
                else:
                    # Natural log
                    result = math.log(x)

            # Format with appropriate precision
            if isinstance(result, (int, float)):
                result = round(result, precision)

            return {
                "operation": operation,
                "x": x,
                "y": y,
                "result": result,
                "precision": precision,
            }

        @self.server.tool()
        def solve_equation(equation: str) -> Dict[str, Any]:
            """Solve a simple mathematical equation"""
            try:
                # Very basic equation solver - dangerous in production!
                # In a real system, you'd use a proper parser with strict validation

                # Replace common mathematical expressions
                equation = equation.replace("^", "**")

                # Evaluate the expression - in a real system, use a proper safe evaluator
                # This is only for demonstration purposes
                result = eval(equation)

                return {
                    "equation": equation,
                    "result": result,
                }
            except Exception as e:
                return {"error": f"Error solving equation: {str(e)}"}

        @self.server.resource("operations")
        def get_operations() -> str:
            """Get a list of supported operations"""
            operations = [
                {"name": "add", "description": "Addition (x + y)"},
                {"name": "subtract", "description": "Subtraction (x - y)"},
                {"name": "multiply", "description": "Multiplication (x * y)"},
                {"name": "divide", "description": "Division (x / y)"},
                {"name": "power", "description": "Power (x ^ y)"},
                {"name": "sqrt", "description": "Square root (√x)"},
                {"name": "log", "description": "Logarithm (log_y(x))"},
            ]

            return json.dumps(
                {
                    "operations": operations,
                    "count": len(operations),
                },
                indent=2,
            )


class TranslatorService(ServiceServer):
    """Translator service implementation"""

    def setup_tools(self):
        # Simulated translations
        self.translations = {
            "hello": {
                "es": "hola",
                "fr": "bonjour",
                "de": "hallo",
                "it": "ciao",
                "ja": "こんにちは",
            },
            "world": {
                "es": "mundo",
                "fr": "monde",
                "de": "welt",
                "it": "mondo",
                "ja": "世界",
            },
            "thank you": {
                "es": "gracias",
                "fr": "merci",
                "de": "danke",
                "it": "grazie",
                "ja": "ありがとう",
            },
            "goodbye": {
                "es": "adiós",
                "fr": "au revoir",
                "de": "auf wiedersehen",
                "it": "arrivederci",
                "ja": "さようなら",
            },
        }

        # Register translator-specific tools
        @self.server.tool()
        def translate_text(text: str, target_language: str) -> Dict[str, Any]:
            """Translate text to the target language"""
            # Validate language
            supported_languages = ["es", "fr", "de", "it", "ja"]
            if target_language not in supported_languages:
                return {
                    "error": f"Unsupported language: {target_language}. Supported: {', '.join(supported_languages)}"
                }

            # Simple word-by-word translation (for demonstration only)
            words = text.lower().split()
            translated_words = []

            for word in words:
                # Clean up punctuation
                clean_word = word.strip(".,!?;:\"'()[]{}").lower()

                # Look up translation
                if (
                    clean_word in self.translations
                    and target_language in self.translations[clean_word]
                ):
                    translated_word = self.translations[clean_word][target_language]
                else:
                    # Fall back to original word if no translation available
                    translated_word = word

                translated_words.append(translated_word)

            translated_text = " ".join(translated_words)

            return {
                "original_text": text,
                "translated_text": translated_text,
                "target_language": target_language,
                "detected_language": "en",  # Always assuming English input for this demo
            }

        @self.server.tool()
        def list_supported_languages() -> Dict[str, Any]:
            """List all supported languages"""
            languages = [
                {"code": "es", "name": "Spanish"},
                {"code": "fr", "name": "French"},
                {"code": "de", "name": "German"},
                {"code": "it", "name": "Italian"},
                {"code": "ja", "name": "Japanese"},
            ]

            return {
                "languages": languages,
                "count": len(languages),
                "source_language": "en",  # Always English for this demo
            }

        @self.server.resource("languages")
        def get_languages() -> str:
            """Get a list of supported languages"""
            languages = [
                {"code": "es", "name": "Spanish", "word_count": len(self.translations)},
                {"code": "fr", "name": "French", "word_count": len(self.translations)},
                {"code": "de", "name": "German", "word_count": len(self.translations)},
                {"code": "it", "name": "Italian", "word_count": len(self.translations)},
                {
                    "code": "ja",
                    "name": "Japanese",
                    "word_count": len(self.translations),
                },
            ]

            return json.dumps(
                {
                    "languages": languages,
                    "count": len(languages),
                    "source_language": "en",
                },
                indent=2,
            )


# Main function to run as a service
def run_as_service(service_type, port):
    """Run as a specialized service"""
    if service_type == "database":
        service = DatabaseService(service_type, port)
    elif service_type == "calculator":
        service = CalculatorService(service_type, port)
    elif service_type == "translator":
        service = TranslatorService(service_type, port)
    else:
        sys.stderr.write(f"Unknown service type: {service_type}\n")
        return

    service.run()


# Main entry point - check if we're running as a service
if __name__ == "__main__" and "--service" in sys.argv:
    # Get service type and port from arguments
    service_idx = sys.argv.index("--service")
    port_idx = sys.argv.index("--port")

    if service_idx + 1 < len(sys.argv) and port_idx + 1 < len(sys.argv):
        service_type = sys.argv[service_idx + 1]
        port = int(sys.argv[port_idx + 1])
        run_as_service(service_type, port)
        sys.exit(0)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP CROSS-SERVER COMMUNICATION DEMO ===\n")
sys.stderr.write("This example demonstrates communication between MCP servers:\n")
sys.stderr.write("1. The main server can start specialized service servers\n")
sys.stderr.write("2. Services can communicate with each other through MCP\n")
sys.stderr.write("3. Complex tasks can be orchestrated across multiple servers\n\n")
sys.stderr.write("Try these tools to see cross-server communication in action:\n")
sys.stderr.write("- register_service: Start a specialized service server\n")
sys.stderr.write("- list_remote_servers: List all registered services\n")
sys.stderr.write("- call_remote_service: Call a tool on a remote service\n")
sys.stderr.write("- get_remote_resource: Get a resource from a remote service\n")
sys.stderr.write("- orchestrate_multi_service_task: Coordinate work across services\n")
sys.stderr.write("=== END CROSS-SERVER COMMUNICATION INFO ===\n\n")

# This server demonstrates MCP cross-server communication
# Run with: uv run mcp dev 54-cross-server-communication.py
