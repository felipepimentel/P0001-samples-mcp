import getpass
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

import jsonschema
from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SchemaValidationMCP")

# Dictionary to store schemas
schemas = {}


# Custom exception for schema validation errors
class SchemaValidationException(Exception):
    """Exception raised for schema validation errors"""

    def __init__(self, errors):
        self.errors = errors
        message = f"Schema validation failed with {len(errors)} errors"
        super().__init__(message)


# Helper function to validate data against a schema
def validate_schema(
    data: Any, schema: Dict[str, Any], schema_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Validate data against a JSON schema

    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        schema_name: Name of the schema for error reporting

    Returns:
        Dictionary with validation results

    Raises:
        SchemaValidationException: If validation fails
    """
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        error_details = []
        for error in errors:
            # Create a human-readable error path
            path = "/".join([str(p) for p in error.path]) if error.path else "root"

            error_details.append(
                {
                    "path": path,
                    "message": error.message,
                    "schema_path": "/".join([str(p) for p in error.schema_path]),
                }
            )

        raise SchemaValidationException(error_details)

    return {"valid": True, "schema": schema_name}


# Schema management tools
@mcp.tool()
def register_schema(name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a new JSON schema

    Args:
        name: The name to register the schema under
        schema: The JSON schema definition

    Returns information about the registered schema
    """
    # Validate that the schema itself is valid
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except Exception as e:
        return {"error": "Invalid schema", "details": str(e)}

    # Store the schema
    schemas[name] = schema

    return {"registered": True, "name": name, "schema": schema}


@mcp.tool()
def list_schemas() -> Dict[str, Any]:
    """
    List all registered schemas

    Returns a list of all registered schema names and their structures
    """
    result = []

    for name, schema in schemas.items():
        # Extract schema type and properties for summary
        schema_type = schema.get("type", "unknown")
        properties = {}

        if schema_type == "object" and "properties" in schema:
            for prop_name, prop_def in schema.get("properties", {}).items():
                prop_type = prop_def.get("type", "any")
                required = prop_name in schema.get("required", [])
                properties[prop_name] = {"type": prop_type, "required": required}

        result.append({"name": name, "type": schema_type, "properties": properties})

    return {"total": len(result), "schemas": result}


@mcp.tool()
def get_schema(name: str) -> Dict[str, Any]:
    """
    Retrieve a schema by name

    Args:
        name: The name of the schema to retrieve

    Returns the schema definition
    """
    if name not in schemas:
        return {"error": "Schema not found", "name": name}

    return {"name": name, "schema": schemas[name]}


@mcp.tool()
def delete_schema(name: str) -> Dict[str, Any]:
    """
    Delete a schema by name

    Args:
        name: The name of the schema to delete

    Returns the result of the deletion operation
    """
    if name not in schemas:
        return {"error": "Schema not found", "name": name}

    del schemas[name]

    return {"deleted": True, "name": name}


# Validation tools
@mcp.tool()
def validate_data(data: Any, schema_name: str) -> Dict[str, Any]:
    """
    Validate data against a registered schema

    Args:
        data: The data to validate
        schema_name: The name of the schema to validate against

    Returns the validation result
    """
    if schema_name not in schemas:
        return {"error": "Schema not found", "schema_name": schema_name}

    schema = schemas[schema_name]

    try:
        validate_schema(data, schema, schema_name)
        return {"valid": True, "schema_name": schema_name, "data": data}
    except SchemaValidationException as e:
        return {"valid": False, "schema_name": schema_name, "errors": e.errors}


# Example schemas and data for demonstration
@mcp.tool()
def create_example_schemas() -> Dict[str, Any]:
    """
    Create example schemas for demonstration

    Returns the created schema definitions
    """
    # Person schema
    person_schema = {
        "type": "object",
        "required": ["name", "age"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
            "email": {"type": "string", "format": "email"},
            "address": {
                "type": "object",
                "properties": {
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "zipcode": {"type": "string"},
                },
            },
        },
    }

    # Product schema
    product_schema = {
        "type": "object",
        "required": ["id", "name", "price"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "price": {"type": "number", "minimum": 0},
            "tags": {"type": "array", "items": {"type": "string"}},
            "in_stock": {"type": "boolean"},
        },
    }

    # Order schema
    order_schema = {
        "type": "object",
        "required": ["order_id", "customer", "items"],
        "properties": {
            "order_id": {"type": "string"},
            "customer": {"$ref": "#/definitions/customer"},
            "items": {
                "type": "array",
                "items": {"$ref": "#/definitions/order_item"},
                "minItems": 1,
            },
            "total": {"type": "number", "minimum": 0},
            "status": {
                "type": "string",
                "enum": ["pending", "processing", "shipped", "delivered"],
            },
        },
        "definitions": {
            "customer": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "address": {"type": "string"},
                },
            },
            "order_item": {
                "type": "object",
                "required": ["product_id", "quantity", "price"],
                "properties": {
                    "product_id": {"type": "string"},
                    "name": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "price": {"type": "number", "minimum": 0},
                },
            },
        },
    }

    # Register the schemas
    schemas["Person"] = person_schema
    schemas["Product"] = product_schema
    schemas["Order"] = order_schema

    return {"created": True, "schemas": ["Person", "Product", "Order"]}


@mcp.tool()
def validation_demo() -> Dict[str, Any]:
    """
    Run a demonstration of schema validation

    Validates various example data against schemas
    """
    results = []

    # Ensure we have example schemas
    if "Person" not in schemas:
        create_example_schemas()

    # Example 1: Valid person
    valid_person = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
        "address": {"street": "123 Main St", "city": "Anytown", "zipcode": "12345"},
    }

    # Example 2: Invalid person (missing required field)
    invalid_person_missing = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        # Missing required age field
    }

    # Example 3: Invalid person (wrong type)
    invalid_person_type = {
        "name": "Bob Johnson",
        "age": "thirty",  # Age should be integer
        "email": "bob@example.com",
    }

    # Example 4: Valid product
    valid_product = {
        "id": "prod-123",
        "name": "Smartphone",
        "price": 599.99,
        "tags": ["electronics", "mobile"],
        "in_stock": True,
    }

    # Example 5: Invalid product (negative price)
    invalid_product = {
        "id": "prod-456",
        "name": "Laptop",
        "price": -999.99,  # Negative price not allowed
        "tags": ["electronics", "computer"],
        "in_stock": True,
    }

    # Run validations
    results.append(
        {"case": "Valid Person", "result": validate_data(valid_person, "Person")}
    )

    results.append(
        {
            "case": "Invalid Person (Missing Field)",
            "result": validate_data(invalid_person_missing, "Person"),
        }
    )

    results.append(
        {
            "case": "Invalid Person (Wrong Type)",
            "result": validate_data(invalid_person_type, "Person"),
        }
    )

    results.append(
        {"case": "Valid Product", "result": validate_data(valid_product, "Product")}
    )

    results.append(
        {
            "case": "Invalid Product (Negative Price)",
            "result": validate_data(invalid_product, "Product"),
        }
    )

    return {"demo_results": results}


# MCP tools with schema validation
@mcp.tool()
def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a user (with schema validation)

    Args:
        user_data: User information to register

    Returns the created user information
    """
    # Define the user schema inline for this tool
    user_schema = {
        "type": "object",
        "required": ["username", "email", "first_name", "last_name"],
        "properties": {
            "username": {"type": "string", "minLength": 3},
            "email": {"type": "string", "format": "email"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "age": {"type": "integer", "minimum": 18},
            "preferences": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string", "enum": ["light", "dark", "system"]},
                    "notifications": {"type": "boolean"},
                },
            },
        },
    }

    # Validate user data before processing
    try:
        validate_schema(user_data, user_schema, "User")

        # We'd normally store the user in a database here
        # For this example, we just return the validated data
        user_data["created_at"] = datetime.now().isoformat()
        user_data["id"] = f"user-{hash(user_data['username']) % 10000}"

        return {"success": True, "user": user_data}
    except SchemaValidationException as e:
        return {"success": False, "validation_errors": e.errors}


@mcp.tool()
def submit_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit an order (with schema validation)

    Args:
        order_data: Order information to submit

    Returns the processed order
    """
    # Get the Order schema (should be registered already)
    if "Order" not in schemas:
        return {"error": "Order schema not found. Run create_example_schemas first."}

    order_schema = schemas["Order"]

    # Validate order data before processing
    try:
        validate_schema(order_data, order_schema, "Order")

        # Calculate total if not provided
        if "total" not in order_data:
            total = sum(
                item["price"] * item["quantity"] for item in order_data["items"]
            )
            order_data["total"] = total

        # Set initial status if not provided
        if "status" not in order_data:
            order_data["status"] = "pending"

        # We'd normally store the order in a database here
        # For this example, we just return the validated data
        order_data["submitted_at"] = datetime.now().isoformat()

        return {"success": True, "order": order_data}
    except SchemaValidationException as e:
        return {"success": False, "validation_errors": e.errors}


# Middleware for schema validation
@mcp.middleware
async def validator_middleware(message, next_handler):
    """Middleware to validate schema for tools that should validate input"""
    # Process only tool calls
    if "method" in message and message["method"] == "tools/call":
        # Get the tool name and parameters
        tool_name = message.get("params", {}).get("name", "")
        params = message.get("params", {}).get("params", {})

        # Map of tool names to schema names for automatic validation
        tool_schema_map = {"create_user": "User", "submit_order": "Order"}

        # Check if this tool needs automatic schema validation
        if tool_name in tool_schema_map and tool_schema_map[tool_name] in schemas:
            schema_name = tool_schema_map[tool_name]
            schema = schemas[schema_name]

            try:
                # Skip the validation for now since we do it within the tool itself
                # This would be used for tools that don't have built-in validation
                pass
            except SchemaValidationException as e:
                # Return validation error as response
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: Schema validation failed",
                        "data": {"validation_errors": e.errors},
                    },
                }

    # Process message normally
    return await next_handler(message)


# Resources
@mcp.resource("schema://registry")
def schema_registry_resource() -> str:
    """Get a list of all schemas as a resource"""
    return json.dumps(list_schemas(), indent=2)


@mcp.resource("schema://examples")
def schema_examples_resource() -> str:
    """Get example schemas as a resource"""

    # Ensure example schemas exist
    if "Person" not in schemas:
        create_example_schemas()

    examples = {"schemas": {}}

    for name in ["Person", "Product", "Order"]:
        if name in schemas:
            examples["schemas"][name] = schemas[name]

    return json.dumps(examples, indent=2)


# Initialization to set up default schemas
@mcp.initialize
def handle_initialize(params):
    """Handle server initialization by setting up default schemas"""
    # Create example schemas on startup if not already defined
    if not schemas:
        create_example_schemas()

    # Return standard initialization response
    return {"capabilities": mcp.server_capabilities}


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP JSON SCHEMA VALIDATION ===\n")
sys.stderr.write("This example demonstrates JSON schema validation in MCP:\n")
sys.stderr.write("1. Define and register JSON schemas\n")
sys.stderr.write("2. Validate data against schemas\n")
sys.stderr.write("3. Automatically validate input to MCP tools\n")
sys.stderr.write("4. Handle validation errors gracefully\n\n")
sys.stderr.write("Try these commands to explore schema validation:\n")
sys.stderr.write("1. list_schemas - see all registered schemas\n")
sys.stderr.write("2. validation_demo - run validation tests with example data\n")
sys.stderr.write("3. create_user - submit user data with validation\n")
sys.stderr.write("=== END SCHEMA VALIDATION INFO ===\n\n")

# This server demonstrates MCP with JSON schema validation
# Run with: uv run mcp dev 58-json-schema-validation.py
