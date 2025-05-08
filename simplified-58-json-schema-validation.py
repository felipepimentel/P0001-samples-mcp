import getpass
import os
from typing import Dict, Any
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("simplified-58-json-schema-validation")

# Copy of tools and resources from 58-json-schema-validation.py
# with lifecycle hooks and middleware removed
import getpass
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict
import jsonschema
from mcp.server.fastmcp import FastMCP
# Workaround for os.getlogin issues in some environments
# Create an MCP server
# Dictionary to store schemas
# Custom exception for schema validation errors
class SchemaValidationException(Exception):
    """Exception raised for schema validation errors"""
    def __init__(self, errors):
# Helper function to validate data against a schema
def validate_schema(
    data: Any, schema: Dict[str, Any], schema_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        schema_name: Name of the schema for error reporting
    Returns:
    Raises:
        SchemaValidationException: If validation fails
    """
    if errors:
        for error in errors:
            # Create a human-readable error path
                    "path": path,
                    "message": error.message,
                    "schema_path": "/".join([str(p) for p in error.schema_path]),
    return {"valid": True, "schema": schema_name}
# Schema management tools
@mcp.tool()
def register_schema(name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        name: The name to register the schema under
        schema: The JSON schema definition
    """
    # Validate that the schema itself is valid
    try:
    except Exception as e:
        return {"error": "Invalid schema", "details": str(e)}
    # Store the schema
    return {"registered": True, "name": name, "schema": schema}
@mcp.tool()
def list_schemas() -> Dict[str, Any]:
    """
    """
    for name, schema in schemas.items():
        # Extract schema type and properties for summary
        if schema_type == "object" and "properties" in schema:
            for prop_name, prop_def in schema.get("properties", {}).items():
                properties[prop_name] = {"type": prop_type, "required": required}
        result.append({"name": name, "type": schema_type, "properties": properties})
    return {"total": len(result), "schemas": result}
@mcp.tool()
def get_schema(name: str) -> Dict[str, Any]:
    """
    Args:
        name: The name of the schema to retrieve
    """
    if name not in schemas:
        return {"error": "Schema not found", "name": name}
    return {"name": name, "schema": schemas[name]}
@mcp.tool()
def delete_schema(name: str) -> Dict[str, Any]:
    """
    Args:
        name: The name of the schema to delete
    """
    if name not in schemas:
        return {"error": "Schema not found", "name": name}
    return {"deleted": True, "name": name}
# Validation tools
@mcp.tool()
def validate_data(data: Any, schema_name: str) -> Dict[str, Any]:
    """
    Args:
        data: The data to validate
        schema_name: The name of the schema to validate against
    """
    if schema_name not in schemas:
        return {"error": "Schema not found", "schema_name": schema_name}
    try:
        return {"valid": True, "schema_name": schema_name, "data": data}
    except SchemaValidationException as e:
        return {"valid": False, "schema_name": schema_name, "errors": e.errors}
# Example schemas and data for demonstration
@mcp.tool()
def create_example_schemas() -> Dict[str, Any]:
    """
    """
    # Person schema
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
    # Product schema
        "type": "object",
        "required": ["id", "name", "price"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "price": {"type": "number", "minimum": 0},
            "tags": {"type": "array", "items": {"type": "string"}},
            "in_stock": {"type": "boolean"},
    # Order schema
        "type": "object",
        "required": ["order_id", "customer", "items"],
        "properties": {
            "order_id": {"type": "string"},
            "customer": {"$ref": "#/definitions/customer"},
            "items": {
                "type": "array",
                "items": {"$ref": "#/definitions/order_item"},
                "minItems": 1,
            "total": {"type": "number", "minimum": 0},
            "status": {
                "type": "string",
                "enum": ["pending", "processing", "shipped", "delivered"],
        "definitions": {
            "customer": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "address": {"type": "string"},
            "order_item": {
                "type": "object",
                "required": ["product_id", "quantity", "price"],
                "properties": {
                    "product_id": {"type": "string"},
                    "name": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "price": {"type": "number", "minimum": 0},
    # Register the schemas
    return {"created": True, "schemas": ["Person", "Product", "Order"]}
@mcp.tool()
def validation_demo() -> Dict[str, Any]:
    """
    """
    # Ensure we have example schemas
    if "Person" not in schemas:
    # Example 1: Valid person
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
        "address": {"street": "123 Main St", "city": "Anytown", "zipcode": "12345"},
    # Example 2: Invalid person (missing required field)
        "name": "Jane Smith",
        "email": "jane@example.com",
        # Missing required age field
    # Example 3: Invalid person (wrong type)
        "name": "Bob Johnson",
        "age": "thirty",  # Age should be integer
        "email": "bob@example.com",
    # Example 4: Valid product
        "id": "prod-123",
        "name": "Smartphone",
        "price": 599.99,
        "tags": ["electronics", "mobile"],
        "in_stock": True,
    # Example 5: Invalid product (negative price)
        "id": "prod-456",
        "name": "Laptop",
        "price": -999.99,  # Negative price not allowed
        "tags": ["electronics", "computer"],
        "in_stock": True,
    # Run validations
        {"case": "Valid Person", "result": validate_data(valid_person, "Person")}
            "case": "Invalid Person (Missing Field)",
            "result": validate_data(invalid_person_missing, "Person"),
            "case": "Invalid Person (Wrong Type)",
            "result": validate_data(invalid_person_type, "Person"),
        {"case": "Valid Product", "result": validate_data(valid_product, "Product")}
            "case": "Invalid Product (Negative Price)",
            "result": validate_data(invalid_product, "Product"),
    return {"demo_results": results}
# MCP tools with schema validation
@mcp.tool()
def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        user_data: User information to register
    """
    # Define the user schema inline for this tool
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
    # Validate user data before processing
    try:
        # We'd normally store the user in a database here
        # For this example, we just return the validated data
        return {"success": True, "user": user_data}
    except SchemaValidationException as e:
        return {"success": False, "validation_errors": e.errors}
@mcp.tool()
def submit_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        order_data: Order information to submit
    """
    # Get the Order schema (should be registered already)
    if "Order" not in schemas:
        return {"error": "Order schema not found. Run create_example_schemas first."}
    # Validate order data before processing
    try:
        # Calculate total if not provided
        if "total" not in order_data:
        # Set initial status if not provided
        if "status" not in order_data:
        # We'd normally store the order in a database here
        # For this example, we just return the validated data
        return {"success": True, "order": order_data}
    except SchemaValidationException as e:
        return {"success": False, "validation_errors": e.errors}
# Middleware for schema validation
async def validator_middleware(message, next_handler):
    """Middleware to validate schema for tools that should validate input"""
    # Process only tool calls
    if "method" in message and message["method"] == "tools/call":
        # Get the tool name and parameters
        # Map of tool names to schema names for automatic validation
        tool_schema_map = {"create_user": "User", "submit_order": "Order"}
        # Check if this tool needs automatic schema validation
        if tool_name in tool_schema_map and tool_schema_map[tool_name] in schemas:
            try:
                # Skip the validation for now since we do it within the tool itself
                # This would be used for tools that don't have built-in validation
            except SchemaValidationException as e:
                # Return validation error as response
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: Schema validation failed",
                        "data": {"validation_errors": e.errors},
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
    examples = {"schemas": {}}
    for name in ["Person", "Product", "Order"]:
        if name in schemas:
    return json.dumps(examples, indent=2)
# Initialization to set up default schemas
def handle_initialize(params):
    """Handle server initialization by setting up default schemas"""
    # Create example schemas on startup if not already defined
    if not schemas:
    # Return standard initialization response
    return {"capabilities": mcp.server_capabilities}
# Explain what this demo does when run with MCP CLI
sys.stderr.write("This example demonstrates JSON schema validation in MCP:\n")
sys.stderr.write("Try these commands to explore schema validation:\n")
# This server demonstrates MCP with JSON schema validation
# Run with: uv run mcp dev 58-json-schema-validation.py

if __name__ == "__main__":
    print("MCP Server ready to run!")
    # The server will be run by MCP CLI
    
# Run with: uv run mcp dev simplified-58-json-schema-validation.py
