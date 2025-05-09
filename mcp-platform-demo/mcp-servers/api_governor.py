import getpass
import json
import os
import re

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("API Governor")

# Mock company API standards
COMPANY_STANDARDS = {
    "naming_conventions": {
        "endpoints": "kebab-case for paths (e.g., /user-profiles)",
        "parameters": "camelCase for query and body parameters",
        "versions": "Must include /v{n} in path",
    },
    "response_codes": {
        "required": [200, 400, 401, 403, 404, 500],
        "descriptions": {
            "200": "Success response with data",
            "400": "Bad request - client error",
            "401": "Unauthorized - authentication required",
            "403": "Forbidden - insufficient permissions",
            "404": "Not found - resource doesn't exist",
            "500": "Server error - unexpected condition",
        },
    },
    "security": {
        "authentication": ["Bearer token required for all non-public endpoints"],
        "rate_limiting": [
            "Must implement rate limiting headers: X-RateLimit-Limit, X-RateLimit-Remaining"
        ],
    },
    "documentation": {
        "required_fields": ["description", "parameters", "responses", "examples"]
    },
}

# Mock API gateways
API_GATEWAYS = {
    "production": {
        "name": "Production API Gateway",
        "url": "https://api.example.com",
        "api_key_required": True,
        "supports_oauth": True,
        "supports_jwt": True,
    },
    "staging": {
        "name": "Staging API Gateway",
        "url": "https://staging-api.example.com",
        "api_key_required": True,
        "supports_oauth": True,
        "supports_jwt": True,
    },
    "development": {
        "name": "Development API Gateway",
        "url": "https://dev-api.example.com",
        "api_key_required": False,
        "supports_oauth": True,
        "supports_jwt": True,
    },
}


@mcp.tool()
def validate_api_contract(openapi_json: str) -> str:
    """Validate an OpenAPI contract against company standards.

    Args:
        openapi_json: The OpenAPI specification as a JSON string

    Returns:
        Validation report with issues and suggestions
    """
    try:
        spec = json.loads(openapi_json)
    except json.JSONDecodeError:
        return "❌ Invalid JSON: The provided OpenAPI specification is not valid JSON."

    # Initialize validation results
    validation = {"passed": True, "errors": [], "warnings": [], "suggestions": []}

    # Validate version
    if "openapi" not in spec:
        validation["errors"].append("Missing 'openapi' version field")
        validation["passed"] = False
    elif not spec["openapi"].startswith("3."):
        validation["errors"].append(
            f"Invalid OpenAPI version: {spec['openapi']}. Must use OpenAPI 3.x"
        )
        validation["passed"] = False

    # Validate info
    if "info" not in spec:
        validation["errors"].append("Missing 'info' section")
        validation["passed"] = False
    else:
        if "title" not in spec["info"] or not spec["info"]["title"]:
            validation["errors"].append("Missing or empty API title in 'info' section")
            validation["passed"] = False
        if "version" not in spec["info"] or not spec["info"]["version"]:
            validation["errors"].append(
                "Missing or empty API version in 'info' section"
            )
            validation["passed"] = False
        if "description" not in spec["info"] or not spec["info"]["description"]:
            validation["warnings"].append(
                "Missing or empty API description in 'info' section"
            )

    # Validate paths
    if "paths" not in spec or not spec["paths"]:
        validation["errors"].append("Missing or empty 'paths' section")
        validation["passed"] = False
    else:
        # Check each path
        for path, path_item in spec["paths"].items():
            # Validate path naming conventions
            if not re.match(r"^/[a-z0-9-/{}]+$", path):
                validation["errors"].append(
                    f"Path '{path}' does not follow kebab-case convention"
                )
                validation["passed"] = False

            # Check version in path
            if not re.search(r"/v\d+/?", path):
                validation["errors"].append(
                    f"Path '{path}' does not include version (e.g., /v1)"
                )
                validation["passed"] = False

            # Check HTTP methods
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]

                    # Check responses
                    if "responses" not in operation:
                        validation["errors"].append(
                            f"{method.upper()} {path}: Missing 'responses' section"
                        )
                        validation["passed"] = False
                    else:
                        for required_code in COMPANY_STANDARDS["response_codes"][
                            "required"
                        ]:
                            if str(required_code) not in operation["responses"]:
                                validation["warnings"].append(
                                    f"{method.upper()} {path}: Missing required response code {required_code}"
                                )

                    # Check security
                    if "security" not in operation and method != "options":
                        validation["warnings"].append(
                            f"{method.upper()} {path}: No security defined. Is this intentionally public?"
                        )

    # Generate report
    report = "# API Contract Validation Report\n\n"

    if validation["passed"] and not validation["warnings"]:
        report += "✅ **PASSED**: The API contract meets all company standards.\n\n"
    elif validation["passed"]:
        report += "⚠️ **PASSED WITH WARNINGS**: The API contract meets minimal standards but has issues.\n\n"
    else:
        report += "❌ **FAILED**: The API contract does not meet company standards.\n\n"

    if validation["errors"]:
        report += "## Critical Issues\n\n"
        for error in validation["errors"]:
            report += f"- {error}\n"
        report += "\n"

    if validation["warnings"]:
        report += "## Warnings\n\n"
        for warning in validation["warnings"]:
            report += f"- {warning}\n"
        report += "\n"

    if validation["suggestions"]:
        report += "## Suggestions\n\n"
        for suggestion in validation["suggestions"]:
            report += f"- {suggestion}\n"
        report += "\n"

    report += "## Company API Standards\n\n"
    report += "### Naming Conventions\n"
    for key, value in COMPANY_STANDARDS["naming_conventions"].items():
        report += f"- **{key}**: {value}\n"

    report += "\n### Required Response Codes\n"
    for code in COMPANY_STANDARDS["response_codes"]["required"]:
        desc = COMPANY_STANDARDS["response_codes"]["descriptions"].get(str(code), "")
        report += f"- **{code}**: {desc}\n"

    return report


@mcp.tool()
def list_api_gateways() -> str:
    """List all available API gateways.

    Returns:
        List of available API gateways with details
    """
    result = "# Available API Gateways\n\n"

    for env, gateway in API_GATEWAYS.items():
        result += f"## {gateway['name']}\n\n"
        result += f"- **Environment:** {env}\n"
        result += f"- **URL:** {gateway['url']}\n"
        result += f"- **API Key Required:** {'Yes' if gateway['api_key_required'] else 'No'}\n"
        result += (
            f"- **OAuth Support:** {'Yes' if gateway['supports_oauth'] else 'No'}\n"
        )
        result += f"- **JWT Support:** {'Yes' if gateway['supports_jwt'] else 'No'}\n\n"

    return result


@mcp.tool()
def get_company_standards() -> str:
    """Get the company API standards.

    Returns:
        Company API standards documentation
    """
    result = "# Company API Standards\n\n"

    result += "## Naming Conventions\n\n"
    for key, value in COMPANY_STANDARDS["naming_conventions"].items():
        result += f"- **{key}**: {value}\n"

    result += "\n## Required Response Codes\n\n"
    for code in COMPANY_STANDARDS["response_codes"]["required"]:
        desc = COMPANY_STANDARDS["response_codes"]["descriptions"].get(str(code), "")
        result += f"- **{code}**: {desc}\n"

    result += "\n## Security Requirements\n\n"
    for category, items in COMPANY_STANDARDS["security"].items():
        result += f"### {category.title()}\n\n"
        for item in items:
            result += f"- {item}\n"

    result += "\n## Documentation Requirements\n\n"
    result += "Every API must document the following fields:\n\n"
    for field in COMPANY_STANDARDS["documentation"]["required_fields"]:
        result += f"- {field}\n"

    return result


if __name__ == "__main__":
    # This will be executed when the server is run directly
    import os

    os.environ["MCP_INSPECTOR_URL"] = "http://127.0.0.1:6274"
    mcp.serve_stdio()
