import getpass
import json
import os
import sys
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server with custom capabilities
mcp = FastMCP("CapabilityNegotiationDemo")

# Define our server's capabilities
# We'll create different capability levels to show how negotiation works
mcp.server_capabilities = {
    "protocol_version": "2024-11-05",
    "features": {
        # Basic capabilities - should be supported by all clients
        "resources": {
            "supported": True,
        },
        "tools": {
            "supported": True,
        },
        # Advanced capabilities - may not be supported by all clients
        "progress": {
            "supported": True,
        },
        "sampling": {
            "supported": True,
            "maxDepth": 3,
            "maxBranches": 2,
        },
        "prompts": {
            "supported": True,
        },
        "notifications": {
            "supported": True,
        },
        # Experimental capabilities - likely unsupported by most clients
        "experimental_feature": {
            "supported": True,
            "version": "0.1.0",
        },
        "future_feature": {
            "supported": True,
            "version": "dev",
        },
    },
}

# Track client capabilities
client_capabilities = {
    "recorded": False,
    "details": {},
    "negotiated_features": {},
}


# Handle initialization and capability negotiation
@mcp.on_initialize
def handle_initialize(params):
    """
    Handle client initialization and capability negotiation

    This is where the client and server exchange capabilities and agree
    on which features to use during the session.
    """
    sys.stderr.write("\n=== CAPABILITY NEGOTIATION STARTED ===\n")

    # Extract client capabilities
    client_caps = params.get("capabilities", {})
    client_features = client_caps.get("features", {})

    # Record client details
    client_capabilities["recorded"] = True
    client_capabilities["details"] = client_caps

    # Log client info
    client_info = params.get("client_info", {})
    sys.stderr.write(
        f"Client: {client_info.get('name', 'Unknown')} {client_info.get('version', '')}\n"
    )
    sys.stderr.write(
        f"Protocol version: {client_caps.get('protocol_version', 'Unknown')}\n"
    )

    # Determine which features both client and server support
    negotiated_features = {}

    for feature_name, server_feature in mcp.server_capabilities["features"].items():
        client_feature = client_features.get(feature_name, {})
        client_supported = client_feature.get("supported", False)
        server_supported = server_feature.get("supported", False)

        negotiated = {
            "supported": client_supported and server_supported,
            "client_supported": client_supported,
            "server_supported": server_supported,
        }

        # Add any additional parameters from both sides
        for key, value in server_feature.items():
            if key != "supported":
                negotiated[f"server_{key}"] = value

        for key, value in client_feature.items():
            if key != "supported":
                negotiated[f"client_{key}"] = value

        negotiated_features[feature_name] = negotiated

        # Log the negotiation results
        status = "✅ AVAILABLE" if negotiated["supported"] else "❌ UNAVAILABLE"
        sys.stderr.write(
            f"Feature '{feature_name}': {status} (Client: {'✓' if client_supported else '✗'}, Server: {'✓' if server_supported else '✗'})\n"
        )

    # Store negotiation results
    client_capabilities["negotiated_features"] = negotiated_features

    sys.stderr.write("=== CAPABILITY NEGOTIATION COMPLETED ===\n\n")

    # Return our server capabilities to the client
    return {"capabilities": mcp.server_capabilities}


# Tools that demonstrate feature detection and capability awareness
@mcp.tool()
def get_client_capabilities() -> Dict[str, Any]:
    """
    Get the client's capabilities as reported during initialization

    This shows what features the client advertised support for
    """
    if not client_capabilities["recorded"]:
        return {"error": "No client capabilities recorded yet. Initialize first."}

    return client_capabilities["details"]


@mcp.tool()
def get_server_capabilities() -> Dict[str, Any]:
    """
    Get the server's capabilities as advertised to clients

    This shows what features the server supports
    """
    return mcp.server_capabilities


@mcp.tool()
def get_negotiated_features() -> Dict[str, Any]:
    """
    Get the negotiated features available in the current session

    This shows which features both client and server support
    """
    if not client_capabilities["recorded"]:
        return {
            "error": "No capability negotiation has occurred yet. Initialize first."
        }

    # Extract just the supported features for clarity
    available_features = {}
    for feature_name, details in client_capabilities["negotiated_features"].items():
        if details["supported"]:
            available_features[feature_name] = details

    return {
        "available_features": available_features,
        "all_features": client_capabilities["negotiated_features"],
    }


@mcp.tool()
def check_feature_availability(feature_name: str) -> Dict[str, Any]:
    """
    Check if a specific feature is available in the current session

    Args:
        feature_name: The name of the feature to check

    Returns details about the feature's availability and support status
    """
    if not client_capabilities["recorded"]:
        return {
            "error": "No capability negotiation has occurred yet. Initialize first."
        }

    if feature_name not in client_capabilities["negotiated_features"]:
        return {
            "feature": feature_name,
            "available": False,
            "reason": "Feature not defined in server capabilities",
        }

    feature_details = client_capabilities["negotiated_features"][feature_name]
    is_available = feature_details["supported"]

    result = {
        "feature": feature_name,
        "available": is_available,
        "client_supported": feature_details["client_supported"],
        "server_supported": feature_details["server_supported"],
    }

    # Add reason if not available
    if not is_available:
        if not feature_details["client_supported"]:
            if not feature_details["server_supported"]:
                result["reason"] = "Neither client nor server supports this feature"
            else:
                result["reason"] = "Client does not support this feature"
        else:
            result["reason"] = "Server does not support this feature"

    # Add detailed parameters if available
    for key, value in feature_details.items():
        if key not in ["supported", "client_supported", "server_supported"]:
            result[key] = value

    return result


@mcp.tool()
def use_feature(feature_name: str) -> Dict[str, Any]:
    """
    Try to use a specific feature, demonstrating capability-aware behavior

    Args:
        feature_name: The feature to use

    Returns success or error based on feature availability
    """
    if not client_capabilities["recorded"]:
        return {
            "error": "No capability negotiation has occurred yet. Initialize first."
        }

    # Check if the feature is available
    if feature_name not in client_capabilities["negotiated_features"]:
        return {
            "success": False,
            "feature": feature_name,
            "error": "Feature not defined in capabilities",
        }

    feature_details = client_capabilities["negotiated_features"][feature_name]
    is_available = feature_details["supported"]

    if not is_available:
        if not feature_details["client_supported"]:
            if not feature_details["server_supported"]:
                reason = "Neither client nor server supports this feature"
            else:
                reason = "Client does not support this feature"
        else:
            reason = "Server does not support this feature"

        return {
            "success": False,
            "feature": feature_name,
            "error": f"Feature not available: {reason}",
        }

    # Feature is available, simulate using it
    return {
        "success": True,
        "feature": feature_name,
        "message": f"Successfully used the '{feature_name}' feature",
        "details": feature_details,
    }


# Resources that expose capability information
@mcp.resource("capabilities://server")
def get_server_capabilities_resource() -> str:
    """Get the server's capabilities as a resource"""
    return json.dumps(mcp.server_capabilities, indent=2)


@mcp.resource("capabilities://client")
def get_client_capabilities_resource() -> str:
    """Get the client's capabilities as a resource"""
    if not client_capabilities["recorded"]:
        return json.dumps({"error": "No client capabilities recorded yet"})

    return json.dumps(client_capabilities["details"], indent=2)


@mcp.resource("capabilities://negotiated")
def get_negotiated_capabilities_resource() -> str:
    """Get the negotiated capabilities as a resource"""
    if not client_capabilities["recorded"]:
        return json.dumps({"error": "No capability negotiation has occurred yet"})

    return json.dumps(client_capabilities["negotiated_features"], indent=2)


# Capability-aware features that adapt based on client support
@mcp.tool()
def demonstrate_adaptive_behavior() -> Dict[str, Any]:
    """
    Demonstrate how servers can adapt their behavior based on client capabilities

    This tool shows different behavior depending on what the client supports
    """
    if not client_capabilities["recorded"]:
        return {
            "error": "No capability negotiation has occurred yet. Initialize first."
        }

    response = {
        "base_functionality": "This basic functionality is always available",
        "adaptive_behaviors": [],
    }

    negotiated = client_capabilities["negotiated_features"]

    # Check for sampling support
    if negotiated.get("sampling", {}).get("supported", False):
        response["adaptive_behaviors"].append(
            {
                "feature": "sampling",
                "behavior": "Server can request LLM operations from the client",
                "details": negotiated["sampling"],
            }
        )
    else:
        response["adaptive_behaviors"].append(
            {
                "feature": "sampling",
                "behavior": "Server is not using LLM sampling features",
                "reason": "Client does not support sampling",
            }
        )

    # Check for progress tracking support
    if negotiated.get("progress", {}).get("supported", False):
        response["adaptive_behaviors"].append(
            {
                "feature": "progress",
                "behavior": "Server can provide real-time progress updates",
                "details": negotiated["progress"],
            }
        )
    else:
        response["adaptive_behaviors"].append(
            {
                "feature": "progress",
                "behavior": "Server is not providing progress updates",
                "reason": "Client does not support progress tracking",
            }
        )

    # Check for notifications support
    if negotiated.get("notifications", {}).get("supported", False):
        response["adaptive_behaviors"].append(
            {
                "feature": "notifications",
                "behavior": "Server can send real-time notifications for resource changes",
                "details": negotiated["notifications"],
            }
        )
    else:
        response["adaptive_behaviors"].append(
            {
                "feature": "notifications",
                "behavior": "Server is not sending change notifications",
                "reason": "Client does not support notifications",
            }
        )

    return response


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP CAPABILITY NEGOTIATION DEMO ===\n")
sys.stderr.write(
    "This example demonstrates how MCP clients and servers negotiate features:\n"
)
sys.stderr.write("1. During initialization, client and server exchange capabilities\n")
sys.stderr.write("2. The server determines which features are mutually supported\n")
sys.stderr.write(
    "3. The session uses only the features both client and server support\n"
)
sys.stderr.write("4. Use get_client_capabilities to see what the client supports\n")
sys.stderr.write("5. Use get_server_capabilities to see what the server offers\n")
sys.stderr.write("6. Use get_negotiated_features to see what features are available\n")
sys.stderr.write("7. Use check_feature_availability to check specific features\n\n")
sys.stderr.write("This mechanism allows clients and servers to work together even if\n")
sys.stderr.write("they support different feature sets or protocol versions.\n")
sys.stderr.write("=== END CAPABILITY NEGOTIATION INFO ===\n\n")

# This server demonstrates MCP capability negotiation
# Run with: uv run mcp dev 41-capability-negotiation.py
