import getpass
import json
import os
import re
from typing import Any, Dict, List

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Sample OpenAPI specification template (for demonstration)
SAMPLE_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "User API",
        "version": "1.0.0",
        "description": "API for managing users",
    },
    "paths": {
        "/v1/users": {
            "get": {
                "summary": "List users",
                "description": "Returns a list of users",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of users to return",
                        "schema": {"type": "integer", "default": 10},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/User"},
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "Create user",
                "description": "Creates a new user",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/User"}
                        }
                    }
                },
                "responses": {"201": {"description": "User created"}},
            },
        },
        "/v1/users/{userId}": {
            "get": {
                "summary": "Get user",
                "description": "Returns a user by ID",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        },
                    },
                    "404": {"description": "User not found"},
                },
            }
        },
    },
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
            }
        }
    },
}

# MCP template for generating tool code
MCP_TOOL_TEMPLATE = """
@mcp.tool()
def {function_name}({parameters}) -> {return_type}:
    \"\"\"{description}
    
    Args:
{args_docstring}
    
    Returns:
        {return_description}
    \"\"\"
    # Here you would implement the actual API call
    # This is a mock implementation
    mock_response = {mock_response}
    
    return mock_response
"""

# MCP template for generating resource code
MCP_RESOURCE_TEMPLATE = """
@mcp.resource("{resource_path}")
def {function_name}({parameters}) -> {return_type}:
    \"\"\"{description}
    
    Args:
{args_docstring}
    
    Returns:
        {return_description}
    \"\"\"
    # Here you would implement the actual API call
    # This is a mock implementation
    mock_response = {mock_response}
    
    return mock_response
"""

mcp = FastMCP("API to MCP Transformer")


@mcp.tool()
def transform_openapi_to_mcp(openapi_json: str) -> str:
    """Transform an OpenAPI specification into MCP server code.

    Args:
        openapi_json: OpenAPI specification as JSON string

    Returns:
        MCP server code implementing the API
    """
    try:
        openapi = json.loads(openapi_json)
    except json.JSONDecodeError:
        return "❌ Invalid JSON: The provided OpenAPI specification is not valid JSON."

    # Extract API info
    api_title = openapi.get("info", {}).get("title", "API")
    api_version = openapi.get("info", {}).get("version", "1.0.0")
    api_description = openapi.get("info", {}).get("description", "")

    # Start building the MCP server code
    mcp_code = f"""import getpass
import os
import json
import requests
from typing import Dict, List, Any, Optional, Union

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Server setup
mcp = FastMCP("{api_title}")

# API Configuration
API_BASE_URL = "https://api.example.com"  # Replace with actual base URL
API_VERSION = "{api_version}"
"""

    # Generate tool functions for each path
    tools = []
    resources = []

    for path, path_item in openapi.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue

            # Extract operation details
            summary = operation.get("summary", "")
            description = operation.get("description", summary)

            # Convert path to a function name
            # E.g., /users/{userId} -> get_user_by_id
            path_without_version = re.sub(r"^/v\d+", "", path)
            base_name = re.sub(r"[{}]", "", path_without_version.replace("-", "_"))
            base_name = re.sub(r"/", "_", base_name.strip("_"))
            function_name = f"{method.lower()}_{base_name}"

            # Get parameters
            param_list = []
            args_docstring = ""
            path_params = []

            # Add path parameters
            for param in operation.get("parameters", []):
                if param.get("in") == "path":
                    param_name = param.get("name", "")
                    param_type = get_python_type(
                        param.get("schema", {}).get("type", "string")
                    )
                    param_list.append(f"{param_name}: {param_type}")
                    args_docstring += (
                        f"        {param_name}: {param.get('description', '')}\n"
                    )
                    path_params.append(param_name)

            # Add query parameters (optional with defaults)
            for param in operation.get("parameters", []):
                if param.get("in") == "query":
                    param_name = param.get("name", "")
                    param_type = get_python_type(
                        param.get("schema", {}).get("type", "string")
                    )
                    default = param.get("schema", {}).get("default", "None")
                    param_list.append(f"{param_name}: {param_type} = {default}")
                    args_docstring += (
                        f"        {param_name}: {param.get('description', '')}\n"
                    )

            # Add request body for POST/PUT/PATCH
            if method.lower() in ["post", "put", "patch"]:
                param_list.append("data: Dict[str, Any]")
                args_docstring += "        data: Request body data\n"

            # Determine return type based on responses
            return_type = "Dict[str, Any]"  # Default
            return_description = "Response data"

            # Check if this is a good candidate for a resource
            is_resource = (
                method.lower() == "get" and bool(path_params) and len(path_params) == 1
            )

            # Generate mock response based on schema
            mock_response = generate_mock_response(
                operation.get("responses", {}).get("200", {})
            )

            # Now build the function
            if is_resource:
                # This is a good candidate for a resource (GET with a single path parameter)
                resource_path = path.replace("{", "").replace("}", "")
                # Make sure there's a : before the parameter
                for param in path_params:
                    resource_path = resource_path.replace(param, f"{{{param}}}")

                code = MCP_RESOURCE_TEMPLATE.format(
                    resource_path=resource_path,
                    function_name=f"get_{base_name}",
                    parameters=", ".join(param_list),
                    return_type=return_type,
                    description=description,
                    args_docstring=args_docstring,
                    return_description=return_description,
                    mock_response=mock_response,
                )
                resources.append(code)
            else:
                # Regular tool function
                code = MCP_TOOL_TEMPLATE.format(
                    function_name=function_name,
                    parameters=", ".join(param_list),
                    return_type=return_type,
                    description=description,
                    args_docstring=args_docstring,
                    return_description=return_description,
                    mock_response=mock_response,
                )
                tools.append(code)

    # Add all tools and resources to the code
    mcp_code += "\n# Tools - API Operations\n"
    for tool in tools:
        mcp_code += tool + "\n"

    mcp_code += "\n# Resources - API Resources\n"
    for resource in resources:
        mcp_code += resource + "\n"

    # Add a demo in the main block
    mcp_code += """
# Usage examples
if __name__ == "__main__":
    import os
    os.environ["MCP_INSPECTOR_URL"] = "http://127.0.0.1:6274"
    mcp.serve_stdio()
"""

    return f"""# Generated MCP Server for {api_title}

```python
{mcp_code}
```

## Implementation Notes

- This is a starting template - you'll need to implement the actual API calls.
- Each function currently returns mock data.
- To run this server:
  1. Save to a file (e.g., `{api_title.lower().replace(" ", "_")}_server.py`)
  2. Run with: `uv run mcp dev {api_title.lower().replace(" ", "_")}_server.py`
  3. The MCP Inspector will open at http://127.0.0.1:6274

## Recommendations

1. Replace the mock implementations with actual API calls using `requests`
2. Add error handling and proper response processing
3. Implement authentication if required by the API
4. Add any missing endpoints or parameters
"""


@mcp.tool()
def get_sample_openapi() -> str:
    """Get a sample OpenAPI specification.

    Returns:
        Sample OpenAPI specification as JSON string
    """
    return json.dumps(SAMPLE_OPENAPI, indent=2)


@mcp.tool()
def transform_rest_api_to_mcp(
    api_name: str, base_url: str, endpoints: List[Dict[str, Any]]
) -> str:
    """Transform REST API details directly into MCP server code.

    Args:
        api_name: Name of the API
        base_url: Base URL of the API
        endpoints: List of endpoints to transform

    Returns:
        MCP server code implementing the API
    """
    # Start building the MCP server code
    mcp_code = f"""import getpass
import os
import json
import requests
from typing import Dict, List, Any, Optional, Union

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Server setup
mcp = FastMCP("{api_name}")

# API Configuration
API_BASE_URL = "{base_url}"
"""

    # Generate tool functions for each endpoint
    tools = []
    resources = []

    for endpoint in endpoints:
        path = endpoint.get("path", "")
        method = endpoint.get("method", "get").lower()
        summary = endpoint.get("summary", "")
        description = endpoint.get("description", summary)
        params = endpoint.get("parameters", [])

        # Convert path to a function name
        path_clean = re.sub(r"[{}]", "", path.replace("-", "_"))
        base_name = re.sub(r"/", "_", path_clean.strip("_"))
        function_name = f"{method}_{base_name}"

        # Get parameters
        param_list = []
        args_docstring = ""
        path_params = []

        # Process parameters
        for param in params:
            param_name = param.get("name", "")
            param_type = get_python_type(param.get("type", "string"))
            param_in = param.get("in", "query")
            required = param.get("required", False)

            if param_in == "path":
                param_list.append(f"{param_name}: {param_type}")
                args_docstring += (
                    f"        {param_name}: {param.get('description', '')}\n"
                )
                path_params.append(param_name)
            elif param_in == "query":
                if required:
                    param_list.append(f"{param_name}: {param_type}")
                else:
                    param_list.append(f"{param_name}: Optional[{param_type}] = None")
                args_docstring += (
                    f"        {param_name}: {param.get('description', '')}\n"
                )

        # Add request body for POST/PUT/PATCH
        if method in ["post", "put", "patch"]:
            if endpoint.get("requestBody"):
                param_list.append("data: Dict[str, Any]")
                args_docstring += "        data: Request body data\n"

        # Determine return type
        return_type = "Dict[str, Any]"  # Default
        return_description = "Response data"

        # Check if this is a good candidate for a resource
        is_resource = method == "get" and bool(path_params) and len(path_params) == 1

        # Create a generic mock response
        mock_response = {}
        if method == "get":
            if path.endswith("}"):  # Single item
                mock_response = {
                    "id": "123",
                    "name": "Example",
                    "created_at": "2023-01-01T00:00:00Z",
                }
            else:  # Collection
                mock_response = {
                    "items": [{"id": "123", "name": "Example"}],
                    "total": 1,
                }
        elif method == "post":
            mock_response = {"id": "new-id", "success": True}
        elif method in ["put", "patch"]:
            mock_response = {"success": True, "updated": True}
        elif method == "delete":
            mock_response = {"success": True, "deleted": True}

        # Now build the function
        if is_resource:
            # This is a good candidate for a resource
            resource_path = path
            # Make sure parameters are in the format {param_name}
            for param in path_params:
                if f"{{{param}}}" not in resource_path:
                    resource_path = resource_path.replace(param, f"{{{param}}}")

            code = f"""
@mcp.resource("{resource_path}")
def get_{base_name}({", ".join(param_list)}) -> {return_type}:
    \"\"\"{description}
    
    Args:
{args_docstring}
    
    Returns:
        {return_description}
    \"\"\"
    # Here you would implement the actual API call
    url = f"{{API_BASE_URL}}{path}"
    response = requests.get(url)
    
    # This is a mock - replace with real implementation
    mock_response = {mock_response}
    
    return mock_response
"""
            resources.append(code)
        else:
            # Regular tool function
            code = f"""
@mcp.tool()
def {function_name}({", ".join(param_list)}) -> {return_type}:
    \"\"\"{description}
    
    Args:
{args_docstring}
    
    Returns:
        {return_description}
    \"\"\"
    # Here you would implement the actual API call
    url = f"{{API_BASE_URL}}{path}"
    
    # This is a mock - replace with real implementation
    # In a real implementation, you would use:
    # response = requests.{method}(url, params=..., json=...)
    mock_response = {mock_response}
    
    return mock_response
"""
            tools.append(code)

    # Add all tools and resources to the code
    mcp_code += "\n# Tools - API Operations\n"
    for tool in tools:
        mcp_code += tool + "\n"

    mcp_code += "\n# Resources - API Resources\n"
    for resource in resources:
        mcp_code += resource + "\n"

    # Add a demo in the main block
    mcp_code += """
# Usage examples
if __name__ == "__main__":
    import os
    os.environ["MCP_INSPECTOR_URL"] = "http://127.0.0.1:6274"
    mcp.serve_stdio()
"""

    return f"""# Generated MCP Server for {api_name}

```python
{mcp_code}
```

## Implementation Notes

- This is a starting template - you'll need to implement the actual API calls.
- Each function currently returns mock data.
- To run this server:
  1. Save to a file (e.g., `{api_name.lower().replace(" ", "_")}_server.py`)
  2. Run with: `uv run mcp dev {api_name.lower().replace(" ", "_")}_server.py`
  3. The MCP Inspector will open at http://127.0.0.1:6274

## Recommendations

1. Replace the mock implementations with actual API calls
2. Add authentication handling if required
3. Implement proper error handling
4. Add any missing endpoints or parameters
"""


# Helper functions
def get_python_type(openapi_type: str) -> str:
    """Convert OpenAPI type to Python type hint."""
    type_mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "List",
        "object": "Dict[str, Any]",
    }
    return type_mapping.get(openapi_type, "Any")


def generate_mock_response(response: Dict[str, Any]) -> str:
    """Generate a mock response based on the schema."""
    content = response.get("content", {}).get("application/json", {})
    schema = content.get("schema", {})

    if schema.get("type") == "array":
        return "[{'id': '123', 'name': 'Example Item'}]"
    elif schema.get("type") == "object" or "$ref" in schema:
        return "{'id': '123', 'name': 'Example', 'created_at': '2023-01-01T00:00:00Z'}"
    else:
        return "{}"
