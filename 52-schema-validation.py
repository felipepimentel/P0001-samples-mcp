import getpass
import json
import os
import sys
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SchemaValidationDemo")

# Track schema validation errors for demonstration
validation_errors = []


# Log validation errors
def log_validation_error(tool_name: str, error_msg: str, params: Dict[str, Any]):
    """Record schema validation errors"""
    validation_errors.append(
        {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "error": error_msg,
            "params": params,
        }
    )
    sys.stderr.write(f"Schema validation error for {tool_name}: {error_msg}\n")


# Simple tool with basic type validation
@mcp.tool()
def simple_calculator(operation: str, x: float, y: float) -> Dict[str, Any]:
    """
    Perform a basic arithmetic operation

    Args:
        operation: The operation to perform ('add', 'subtract', 'multiply', 'divide')
        x: The first number
        y: The second number

    Returns the result of the calculation.
    """
    if operation not in ["add", "subtract", "multiply", "divide"]:
        log_validation_error(
            "simple_calculator",
            f"Invalid operation: {operation}",
            {"operation": operation, "x": x, "y": y},
        )
        return {"error": f"Invalid operation: {operation}"}

    if operation == "divide" and y == 0:
        log_validation_error(
            "simple_calculator",
            "Division by zero",
            {"operation": operation, "x": x, "y": y},
        )
        return {"error": "Division by zero"}

    # Perform the calculation
    if operation == "add":
        result = x + y
    elif operation == "subtract":
        result = x - y
    elif operation == "multiply":
        result = x * y
    else:  # divide
        result = x / y

    return {"operation": operation, "x": x, "y": y, "result": result}


# Tool with complex object schema
@mcp.tool()
def create_user(
    username: str,
    email: str,
    password: str,
    age: Optional[int] = None,
    role: str = "user",
    settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new user with validation

    Args:
        username: Username (3-20 alphanumeric characters)
        email: Valid email address
        password: Password (min 8 characters)
        age: User's age (must be 18+)
        role: User role ('user', 'admin', 'moderator')
        settings: Optional user settings

    Returns user information if validation passes.
    """
    # Validate username
    if not isinstance(username, str) or len(username) < 3 or len(username) > 20:
        log_validation_error(
            "create_user", "Username must be 3-20 characters", locals()
        )
        return {"error": "Username must be 3-20 characters"}

    # Validate email format (simple check)
    if not isinstance(email, str) or "@" not in email or "." not in email.split("@")[1]:
        log_validation_error("create_user", "Invalid email format", locals())
        return {"error": "Invalid email format"}

    # Validate password
    if not isinstance(password, str) or len(password) < 8:
        log_validation_error(
            "create_user", "Password must be at least 8 characters", locals()
        )
        return {"error": "Password must be at least 8 characters"}

    # Validate age if provided
    if age is not None:
        if not isinstance(age, int) or age < 18:
            log_validation_error("create_user", "Age must be 18+", locals())
            return {"error": "Age must be 18+"}

    # Validate role
    if role not in ["user", "admin", "moderator"]:
        log_validation_error("create_user", f"Invalid role: {role}", locals())
        return {"error": f"Invalid role: {role}"}

    # Create user object (password would be hashed in a real implementation)
    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "settings": settings or {},
    }

    if age is not None:
        user["age"] = age

    return {"status": "success", "message": "User created successfully", "user": user}


# Tool with array schema validation
@mcp.tool()
def analyze_data_points(data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze a list of data points

    Args:
        data_points: List of data point objects, each with x and y values

    Returns analysis of the data points.
    """
    # Validate data points structure
    if not isinstance(data_points, list):
        log_validation_error(
            "analyze_data_points", "Data points must be an array", locals()
        )
        return {"error": "Data points must be an array"}

    if len(data_points) == 0:
        log_validation_error(
            "analyze_data_points", "Data points array cannot be empty", locals()
        )
        return {"error": "Data points array cannot be empty"}

    # Validate each data point
    validated_points = []
    for i, point in enumerate(data_points):
        if not isinstance(point, dict):
            log_validation_error(
                "analyze_data_points",
                f"Data point at index {i} is not an object",
                locals(),
            )
            return {"error": f"Data point at index {i} is not an object"}

        if "x" not in point or "y" not in point:
            log_validation_error(
                "analyze_data_points",
                f"Data point at index {i} missing x or y value",
                locals(),
            )
            return {"error": f"Data point at index {i} missing x or y value"}

        try:
            x = float(point["x"])
            y = float(point["y"])
            validated_points.append({"x": x, "y": y})
        except (ValueError, TypeError):
            log_validation_error(
                "analyze_data_points",
                f"Data point at index {i} has invalid x or y value",
                locals(),
            )
            return {"error": f"Data point at index {i} has invalid x or y value"}

    # Perform analysis
    x_values = [p["x"] for p in validated_points]
    y_values = [p["y"] for p in validated_points]

    # Basic statistics
    analysis = {
        "count": len(validated_points),
        "x_min": min(x_values),
        "x_max": max(x_values),
        "x_avg": sum(x_values) / len(x_values),
        "y_min": min(y_values),
        "y_max": max(y_values),
        "y_avg": sum(y_values) / len(y_values),
    }

    return {"analysis": analysis, "validated_points": validated_points}


# Tool with advanced schema validation and nesting
@mcp.tool()
def process_order(
    order_id: str,
    customer: Dict[str, Any],
    items: List[Dict[str, Any]],
    shipping_address: Dict[str, Any],
    payment_info: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a complete order with nested schema validation

    Args:
        order_id: Unique order identifier
        customer: Customer information object
        items: List of order items
        shipping_address: Shipping address object
        payment_info: Payment information object
        metadata: Optional additional order data

    Returns order processing results.
    """
    # Validate order ID
    if not isinstance(order_id, str) or not order_id:
        log_validation_error("process_order", "Invalid order ID", locals())
        return {"error": "Invalid order ID"}

    # Validate customer object
    if not isinstance(customer, dict):
        log_validation_error("process_order", "Customer must be an object", locals())
        return {"error": "Customer must be an object"}

    # Required customer fields
    for field in ["id", "name", "email"]:
        if field not in customer:
            log_validation_error(
                "process_order", f"Missing required customer field: {field}", locals()
            )
            return {"error": f"Missing required customer field: {field}"}

    # Validate items array
    if not isinstance(items, list) or not items:
        log_validation_error(
            "process_order", "Items must be a non-empty array", locals()
        )
        return {"error": "Items must be a non-empty array"}

    # Validate each item
    total_amount = 0
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            log_validation_error(
                "process_order", f"Item at index {i} is not an object", locals()
            )
            return {"error": f"Item at index {i} is not an object"}

        # Required item fields
        for field in ["product_id", "quantity", "price"]:
            if field not in item:
                log_validation_error(
                    "process_order",
                    f"Item at index {i} missing field: {field}",
                    locals(),
                )
                return {"error": f"Item at index {i} missing field: {field}"}

        # Validate numeric fields
        try:
            quantity = int(item["quantity"])
            price = float(item["price"])

            if quantity <= 0:
                log_validation_error(
                    "process_order", f"Item at index {i} has invalid quantity", locals()
                )
                return {"error": f"Item at index {i} has invalid quantity"}

            if price < 0:
                log_validation_error(
                    "process_order", f"Item at index {i} has invalid price", locals()
                )
                return {"error": f"Item at index {i} has invalid price"}

            # Calculate item total
            item_total = quantity * price
            total_amount += item_total

            # Add calculation to item
            item["total"] = item_total

        except (ValueError, TypeError):
            log_validation_error(
                "process_order",
                f"Item at index {i} has invalid quantity or price",
                locals(),
            )
            return {"error": f"Item at index {i} has invalid quantity or price"}

    # Validate shipping address
    if not isinstance(shipping_address, dict):
        log_validation_error(
            "process_order", "Shipping address must be an object", locals()
        )
        return {"error": "Shipping address must be an object"}

    # Required shipping address fields
    for field in ["street", "city", "zip", "country"]:
        if field not in shipping_address:
            log_validation_error(
                "process_order", f"Missing shipping address field: {field}", locals()
            )
            return {"error": f"Missing shipping address field: {field}"}

    # Validate payment info
    if not isinstance(payment_info, dict):
        log_validation_error(
            "process_order", "Payment info must be an object", locals()
        )
        return {"error": "Payment info must be an object"}

    # Required payment fields
    for field in ["method", "transaction_id"]:
        if field not in payment_info:
            log_validation_error(
                "process_order", f"Missing payment info field: {field}", locals()
            )
            return {"error": f"Missing payment info field: {field}"}

    # Create processed order
    processed_order = {
        "order_id": order_id,
        "customer": customer,
        "items": items,
        "shipping_address": shipping_address,
        "payment_info": payment_info,
        "total_amount": total_amount,
        "status": "processed",
        "processed_at": datetime.now().isoformat(),
    }

    if metadata:
        processed_order["metadata"] = metadata

    return {
        "status": "success",
        "message": "Order processed successfully",
        "order": processed_order,
    }


# Tool using Enums for stricter validation
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


@mcp.tool()
def create_task(
    title: str,
    description: str,
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.TODO,
    assignee: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: List[str] = None,
) -> Dict[str, Any]:
    """
    Create a new task with Enum-based validation

    Args:
        title: Task title
        description: Task description
        priority: Task priority (low, medium, high, critical)
        status: Task status (todo, in_progress, review, done)
        assignee: Person assigned to the task
        due_date: Due date (ISO format)
        tags: List of tags

    Returns the created task information.
    """
    # Validate title
    if not title or len(title) < 3:
        log_validation_error(
            "create_task", "Title must be at least 3 characters", locals()
        )
        return {"error": "Title must be at least 3 characters"}

    # Validate description
    if not description:
        log_validation_error("create_task", "Description is required", locals())
        return {"error": "Description is required"}

    # Validate due date if provided
    if due_date is not None:
        try:
            # Check if date format is valid
            datetime.fromisoformat(due_date)
        except ValueError:
            log_validation_error(
                "create_task", "Invalid due date format, use ISO format", locals()
            )
            return {"error": "Invalid due date format, use ISO format"}

    # Create the task
    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
        "created_at": datetime.now().isoformat(),
    }

    if assignee:
        task["assignee"] = assignee

    if due_date:
        task["due_date"] = due_date

    if tags:
        task["tags"] = tags

    return {"status": "success", "message": "Task created successfully", "task": task}


# Tool for retrieving validation errors
@mcp.tool()
def get_validation_errors(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve schema validation errors that have occurred

    Args:
        limit: Maximum number of errors to return (optional)

    Returns the recorded validation errors.
    """
    errors = validation_errors

    if limit is not None and limit > 0:
        errors = errors[-limit:]

    return {"total_errors": len(validation_errors), "errors": errors}


# Resource to expose schema information
@mcp.resource("schemas/calculator")
def get_calculator_schema() -> str:
    """Get JSON Schema for the calculator tool"""
    schema = {
        "type": "object",
        "required": ["operation", "x", "y"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The operation to perform",
            },
            "x": {"type": "number", "description": "The first number"},
            "y": {"type": "number", "description": "The second number"},
        },
    }
    return json.dumps(schema, indent=2)


@mcp.resource("schemas/create-user")
def get_user_schema() -> str:
    """Get JSON Schema for the create_user tool"""
    schema = {
        "type": "object",
        "required": ["username", "email", "password"],
        "properties": {
            "username": {
                "type": "string",
                "minLength": 3,
                "maxLength": 20,
                "description": "Username (3-20 alphanumeric characters)",
            },
            "email": {
                "type": "string",
                "format": "email",
                "description": "Valid email address",
            },
            "password": {
                "type": "string",
                "minLength": 8,
                "description": "Password (min 8 characters)",
            },
            "age": {
                "type": "integer",
                "minimum": 18,
                "description": "User's age (must be 18+)",
            },
            "role": {
                "type": "string",
                "enum": ["user", "admin", "moderator"],
                "default": "user",
                "description": "User role",
            },
            "settings": {"type": "object", "description": "Optional user settings"},
        },
    }
    return json.dumps(schema, indent=2)


@mcp.resource("schemas/process-order")
def get_order_schema() -> str:
    """Get JSON Schema for the process_order tool"""
    schema = {
        "type": "object",
        "required": [
            "order_id",
            "customer",
            "items",
            "shipping_address",
            "payment_info",
        ],
        "properties": {
            "order_id": {"type": "string", "description": "Unique order identifier"},
            "customer": {
                "type": "object",
                "required": ["id", "name", "email"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                },
                "description": "Customer information",
            },
            "items": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["product_id", "quantity", "price"],
                    "properties": {
                        "product_id": {"type": "string"},
                        "quantity": {"type": "integer", "minimum": 1},
                        "price": {"type": "number", "minimum": 0},
                    },
                },
                "description": "Order items",
            },
            "shipping_address": {
                "type": "object",
                "required": ["street", "city", "zip", "country"],
                "properties": {
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "zip": {"type": "string"},
                    "country": {"type": "string"},
                },
                "description": "Shipping address",
            },
            "payment_info": {
                "type": "object",
                "required": ["method", "transaction_id"],
                "properties": {
                    "method": {"type": "string"},
                    "transaction_id": {"type": "string"},
                },
                "description": "Payment information",
            },
            "metadata": {
                "type": "object",
                "description": "Optional additional order data",
            },
        },
    }
    return json.dumps(schema, indent=2)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP SCHEMA VALIDATION DEMO ===\n")
sys.stderr.write("This example demonstrates schema validation in MCP:\n")
sys.stderr.write("1. Tools define parameter schemas to enforce type safety\n")
sys.stderr.write("2. MCP validates inputs against these schemas\n")
sys.stderr.write("3. Complex nested object validation is supported\n")
sys.stderr.write("4. Enums can be used for strict validation of allowed values\n\n")
sys.stderr.write("Try these tools with valid and invalid inputs:\n")
sys.stderr.write("- simple_calculator: Basic type validation\n")
sys.stderr.write("- create_user: Object validation with required fields\n")
sys.stderr.write("- analyze_data_points: Array validation\n")
sys.stderr.write("- process_order: Complex nested object validation\n")
sys.stderr.write("- create_task: Enum-based validation\n")
sys.stderr.write("- get_validation_errors: See validation errors that occurred\n")
sys.stderr.write("=== END SCHEMA VALIDATION INFO ===\n\n")

# This server demonstrates MCP schema validation
# Run with: uv run mcp dev 52-schema-validation.py
