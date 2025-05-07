import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
import jwt
from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, TextContent

# Initialize MCP server with secure communication features
mcp = FastMCP("Secure Agent Communication")

# Directory for storing security and communication data
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_secure_communication"
AUTH_DIR = DATA_DIR / "auth"
LOGS_DIR = DATA_DIR / "logs"
AGENT_DIR = DATA_DIR / "agents"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
AUTH_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
AGENT_DIR.mkdir(exist_ok=True)

# Secure secret key file
SECRET_KEY_PATH = AUTH_DIR / "secret_key.txt"


# Default permissions for different operations
class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


# Security roles for agents
class SecurityRole(str, Enum):
    ADMIN = "admin"  # Can manage other agents and security settings
    OPERATOR = "operator"  # Can perform most operations
    READER = "reader"  # Read-only access to data
    UNTRUSTED = "untrusted"  # Minimal permissions, heavily restricted


# Track API rate limits
@dataclass
class RateLimitInfo:
    max_calls_per_minute: int = 60
    max_calls_per_hour: int = 1000
    call_history: List[float] = field(default_factory=list)


# Agent information with security details
@dataclass
class SecureAgentInfo:
    id: str
    name: str
    endpoint: str
    api_key: str
    role: SecurityRole
    permissions: Set[Permission]
    created_at: float
    rate_limit: RateLimitInfo = field(default_factory=RateLimitInfo)
    jwt_secret: Optional[str] = None
    last_active: Optional[float] = None
    blocked: bool = False
    block_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Security events for audit
@dataclass
class SecurityEvent:
    timestamp: float
    event_type: str
    agent_id: Optional[str]
    details: Dict[str, Any]
    severity: str


# In-memory storage
registered_agents: Dict[str, SecureAgentInfo] = {}
security_events: List[SecurityEvent] = []
authorized_token_hashes: Set[str] = set()


# Secure random generator to create a secret key if one doesn't exist
def generate_secret_key() -> str:
    """Generate a secure random key for JWT signing"""
    return base64.b64encode(os.urandom(32)).decode("utf-8")


# Load or create secret key
def get_secret_key() -> str:
    """Get the secret key for JWT signing, creating one if it doesn't exist"""
    if os.path.exists(SECRET_KEY_PATH):
        with open(SECRET_KEY_PATH, "r") as f:
            return f.read().strip()
    else:
        secret_key = generate_secret_key()
        with open(SECRET_KEY_PATH, "w") as f:
            f.write(secret_key)
        # Set restrictive permissions
        os.chmod(SECRET_KEY_PATH, 0o600)
        return secret_key


# Get the secret key
SECRET_KEY = get_secret_key()


# Load registered agents from disk
def load_agents_from_disk() -> None:
    """Load registered agents from disk"""
    for agent_file in AGENT_DIR.glob("*.json"):
        try:
            with open(agent_file, "r") as f:
                agent_data = json.load(f)
                agent_id = agent_file.stem

                # Convert permissions from list to set
                permissions = set(
                    [Permission(p) for p in agent_data.get("permissions", [])]
                )

                # Create RateLimitInfo
                rate_limit = RateLimitInfo(
                    max_calls_per_minute=agent_data.get("rate_limit", {}).get(
                        "max_calls_per_minute", 60
                    ),
                    max_calls_per_hour=agent_data.get("rate_limit", {}).get(
                        "max_calls_per_hour", 1000
                    ),
                )

                agent_info = SecureAgentInfo(
                    id=agent_id,
                    name=agent_data["name"],
                    endpoint=agent_data["endpoint"],
                    api_key=agent_data["api_key"],
                    role=SecurityRole(agent_data["role"]),
                    permissions=permissions,
                    created_at=agent_data["created_at"],
                    rate_limit=rate_limit,
                    jwt_secret=agent_data.get("jwt_secret"),
                    last_active=agent_data.get("last_active"),
                    blocked=agent_data.get("blocked", False),
                    block_reason=agent_data.get("block_reason"),
                    metadata=agent_data.get("metadata", {}),
                )

                registered_agents[agent_id] = agent_info
        except Exception as e:
            log_security_event(
                "agent_load_error",
                None,
                {"agent_file": str(agent_file), "error": str(e)},
                "warning",
            )


# Save agent to disk
def save_agent_to_disk(agent: SecureAgentInfo) -> None:
    """Save agent information to disk"""
    agent_file = AGENT_DIR / f"{agent.id}.json"

    agent_data = {
        "name": agent.name,
        "endpoint": agent.endpoint,
        "api_key": agent.api_key,
        "role": agent.role,
        "permissions": list(agent.permissions),
        "created_at": agent.created_at,
        "rate_limit": {
            "max_calls_per_minute": agent.rate_limit.max_calls_per_minute,
            "max_calls_per_hour": agent.rate_limit.max_calls_per_hour,
        },
        "jwt_secret": agent.jwt_secret,
        "last_active": agent.last_active,
        "blocked": agent.blocked,
        "block_reason": agent.block_reason,
        "metadata": agent.metadata,
    }

    with open(agent_file, "w") as f:
        json.dump(agent_data, f, indent=2)


# Log security events
def log_security_event(
    event_type: str, agent_id: Optional[str], details: Dict[str, Any], severity: str
) -> None:
    """Log a security event for audit purposes"""
    event = SecurityEvent(
        timestamp=time.time(),
        event_type=event_type,
        agent_id=agent_id,
        details=details,
        severity=severity,
    )

    security_events.append(event)

    # Save to disk for persistence
    log_file = LOGS_DIR / f"security_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a") as f:
        log_entry = {
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "agent_id": event.agent_id,
            "details": event.details,
            "severity": event.severity,
        }
        f.write(json.dumps(log_entry) + "\n")


# Security Utilities
def generate_token(agent_id: str, expiration_minutes: int = 30) -> str:
    """Generate a JWT for secure communication with an agent"""
    if agent_id not in registered_agents:
        raise ValueError(f"Unknown agent ID: {agent_id}")

    agent = registered_agents[agent_id]

    # Check if agent is blocked
    if agent.blocked:
        raise ValueError(f"Agent is blocked: {agent.block_reason}")

    # Create expiration time
    expiration = datetime.now() + timedelta(minutes=expiration_minutes)

    # Create the payload
    payload = {
        "sub": agent_id,
        "name": agent.name,
        "role": agent.role,
        "exp": expiration.timestamp(),
        "iat": datetime.now().timestamp(),
        "jti": str(uuid.uuid4()),
    }

    # Sign the token
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    # Store the token hash for validation
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    authorized_token_hashes.add(token_hash)

    # Log token creation
    log_security_event(
        "token_created",
        agent_id,
        {"expiration_minutes": expiration_minutes, "token_hash": token_hash},
        "info",
    )

    return token


def verify_token(token: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """Verify a JWT token and return (is_valid, agent_id, payload)"""
    # Check if token is in the authorized list
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if token_hash not in authorized_token_hashes:
        log_security_event(
            "token_unauthorized", None, {"token_hash": token_hash}, "warning"
        )
        return False, None, None

    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        agent_id = payload.get("sub")

        # Validate agent exists and isn't blocked
        if agent_id not in registered_agents:
            log_security_event(
                "token_invalid_agent", agent_id, {"token_hash": token_hash}, "warning"
            )
            return False, None, None

        agent = registered_agents[agent_id]
        if agent.blocked:
            log_security_event(
                "blocked_agent_attempt",
                agent_id,
                {"reason": agent.block_reason},
                "warning",
            )
            return False, None, None

        # Update last active timestamp
        agent.last_active = time.time()
        save_agent_to_disk(agent)

        return True, agent_id, payload
    except jwt.ExpiredSignatureError:
        log_security_event("token_expired", None, {"token_hash": token_hash}, "info")
        # Remove expired token
        authorized_token_hashes.discard(token_hash)
        return False, None, None
    except jwt.InvalidTokenError as e:
        log_security_event(
            "token_invalid",
            None,
            {"token_hash": token_hash, "error": str(e)},
            "warning",
        )
        return False, None, None


def check_rate_limit(agent_id: str) -> Tuple[bool, Optional[str]]:
    """Check if agent has exceeded rate limits, returns (is_allowed, reason)"""
    if agent_id not in registered_agents:
        return False, "Unknown agent"

    agent = registered_agents[agent_id]
    now = time.time()

    # Remove calls older than 1 hour
    agent.rate_limit.call_history = [
        t for t in agent.rate_limit.call_history if now - t < 3600
    ]

    # Check hourly limit
    if len(agent.rate_limit.call_history) >= agent.rate_limit.max_calls_per_hour:
        log_security_event(
            "rate_limit_exceeded_hourly",
            agent_id,
            {
                "calls": len(agent.rate_limit.call_history),
                "limit": agent.rate_limit.max_calls_per_hour,
            },
            "warning",
        )
        return False, "Hourly rate limit exceeded"

    # Check minute limit
    minute_calls = sum(1 for t in agent.rate_limit.call_history if now - t < 60)
    if minute_calls >= agent.rate_limit.max_calls_per_minute:
        log_security_event(
            "rate_limit_exceeded_minute",
            agent_id,
            {"calls": minute_calls, "limit": agent.rate_limit.max_calls_per_minute},
            "warning",
        )
        return False, "Per-minute rate limit exceeded"

    # Record this call
    agent.rate_limit.call_history.append(now)
    return True, None


def has_permission(agent_id: str, required_permission: Permission) -> bool:
    """Check if agent has the required permission"""
    if agent_id not in registered_agents:
        return False

    agent = registered_agents[agent_id]

    # Admins have all permissions
    if agent.role == SecurityRole.ADMIN:
        return True

    # Check specific permission
    return required_permission in agent.permissions


# Initialize by loading agents
load_agents_from_disk()


# A2A Secure Communication Functions
async def send_secure_message(agent_id: str, message: str) -> Dict[str, Any]:
    """Send a secure message to another agent using JWT authentication"""
    if agent_id not in registered_agents:
        return {"error": f"Unknown agent: {agent_id}"}

    agent = registered_agents[agent_id]

    # Check if agent is blocked
    if agent.blocked:
        log_security_event(
            "message_to_blocked_agent",
            agent_id,
            {"reason": agent.block_reason},
            "warning",
        )
        return {"error": f"Agent is blocked: {agent.block_reason}"}

    # Check rate limits
    rate_allowed, rate_reason = check_rate_limit(agent_id)
    if not rate_allowed:
        return {"error": f"Rate limit exceeded: {rate_reason}"}

    # Check permission
    if not has_permission(agent_id, Permission.WRITE):
        log_security_event(
            "permission_denied",
            agent_id,
            {"required_permission": Permission.WRITE.value},
            "warning",
        )
        return {"error": "Permission denied: WRITE permission required"}

    # Generate a new token for this communication
    try:
        token = generate_token(agent_id)
    except ValueError as e:
        return {"error": str(e)}

    # Create a unique message ID
    message_id = str(uuid.uuid4())

    # A2A protocol message with security
    a2a_message = {
        "message": message,
        "message_id": message_id,
        "sender": {"name": "Secure MCP Bridge", "id": "secure-mcp-bridge"},
        "timestamp": time.time(),
        "security": {
            "encryption": "none",  # In a real app, you might encrypt the content
            "integrity": "jwt",
        },
    }

    # Set up headers with JWT
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                agent.endpoint, json=a2a_message, headers=headers, timeout=30.0
            )

            # Update last activity time
            agent.last_active = time.time()
            save_agent_to_disk(agent)

            if response.status_code == 200:
                response_data = response.json()

                # Verify response integrity
                if "signature" in response_data:
                    expected_sig = hmac.new(
                        agent.api_key.encode(),
                        json.dumps(response_data["data"]).encode(),
                        hashlib.sha256,
                    ).hexdigest()

                    if response_data["signature"] != expected_sig:
                        log_security_event(
                            "invalid_response_signature",
                            agent_id,
                            {"message_id": message_id},
                            "critical",
                        )
                        return {"error": "Response signature validation failed"}

                # Log successful communication
                log_security_event(
                    "successful_communication",
                    agent_id,
                    {"message_id": message_id},
                    "info",
                )

                return response_data
            else:
                error_msg = (
                    f"Communication error: {response.status_code} - {response.text}"
                )
                log_security_event(
                    "communication_error",
                    agent_id,
                    {"status_code": response.status_code, "message_id": message_id},
                    "error",
                )
                return {"error": error_msg}
    except Exception as e:
        log_security_event(
            "communication_exception",
            agent_id,
            {"error": str(e), "message_id": message_id},
            "error",
        )
        return {"error": f"Exception: {str(e)}"}


# MCP Tools for Agent Security Management
@mcp.tool()
def create_agent(
    name: str,
    endpoint: str,
    role: str,
    permissions: List[str] = None,
    max_calls_per_minute: int = 60,
    max_calls_per_hour: int = 1000,
) -> str:
    """
    Create a new secure agent with specified permissions

    Args:
        name: Agent name
        endpoint: A2A endpoint URL
        role: Security role (admin, operator, reader, untrusted)
        permissions: List of permissions (read, write, execute, admin)
        max_calls_per_minute: Rate limit per minute
        max_calls_per_hour: Rate limit per hour
    """
    # Validate role
    try:
        security_role = SecurityRole(role)
    except ValueError:
        valid_roles = [r.value for r in SecurityRole]
        return f"Error: Invalid role. Choose from: {', '.join(valid_roles)}"

    # Validate permissions
    validated_permissions = set()
    if permissions:
        for perm in permissions:
            try:
                validated_permissions.add(Permission(perm))
            except ValueError:
                valid_perms = [p.value for p in Permission]
                return f"Error: Invalid permission '{perm}'. Choose from: {', '.join(valid_perms)}"

    # Set default permissions based on role if none provided
    if not permissions:
        if security_role == SecurityRole.ADMIN:
            validated_permissions = {
                Permission.READ,
                Permission.WRITE,
                Permission.EXECUTE,
                Permission.ADMIN,
            }
        elif security_role == SecurityRole.OPERATOR:
            validated_permissions = {
                Permission.READ,
                Permission.WRITE,
                Permission.EXECUTE,
            }
        elif security_role == SecurityRole.READER:
            validated_permissions = {Permission.READ}
        else:  # UNTRUSTED
            validated_permissions = set()

    # Generate ID and API key
    agent_id = str(uuid.uuid4())[:8]
    api_key = base64.b64encode(os.urandom(24)).decode("utf-8")

    # Create agent
    agent = SecureAgentInfo(
        id=agent_id,
        name=name,
        endpoint=endpoint,
        api_key=api_key,
        role=security_role,
        permissions=validated_permissions,
        created_at=time.time(),
        rate_limit=RateLimitInfo(
            max_calls_per_minute=max_calls_per_minute,
            max_calls_per_hour=max_calls_per_hour,
        ),
    )

    # Save to registry
    registered_agents[agent_id] = agent
    save_agent_to_disk(agent)

    # Log creation
    log_security_event(
        "agent_created",
        agent_id,
        {"role": role, "permissions": list(validated_permissions)},
        "info",
    )

    return json.dumps(
        {
            "message": f"Agent '{name}' created successfully",
            "agent_id": agent_id,
            "api_key": api_key,
            "role": role,
            "permissions": list(validated_permissions),
        },
        indent=2,
    )


@mcp.tool()
def block_agent(agent_id: str, reason: str) -> str:
    """
    Block an agent from communication

    Args:
        agent_id: ID of the agent to block
        reason: Reason for blocking the agent
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    agent = registered_agents[agent_id]
    agent.blocked = True
    agent.block_reason = reason
    save_agent_to_disk(agent)

    # Log block
    log_security_event("agent_blocked", agent_id, {"reason": reason}, "warning")

    return json.dumps(
        {"message": f"Agent '{agent.name}' blocked successfully", "reason": reason},
        indent=2,
    )


@mcp.tool()
def unblock_agent(agent_id: str) -> str:
    """
    Unblock a previously blocked agent

    Args:
        agent_id: ID of the agent to unblock
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    agent = registered_agents[agent_id]

    if not agent.blocked:
        return f"Agent '{agent.name}' is not blocked"

    agent.blocked = False
    agent.block_reason = None
    save_agent_to_disk(agent)

    # Log unblock
    log_security_event("agent_unblocked", agent_id, {}, "info")

    return json.dumps(
        {"message": f"Agent '{agent.name}' unblocked successfully"}, indent=2
    )


@mcp.tool()
def update_agent_permissions(agent_id: str, permissions: List[str]) -> str:
    """
    Update an agent's permissions

    Args:
        agent_id: ID of the agent to update
        permissions: New list of permissions
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    # Validate permissions
    validated_permissions = set()
    for perm in permissions:
        try:
            validated_permissions.add(Permission(perm))
        except ValueError:
            valid_perms = [p.value for p in Permission]
            return f"Error: Invalid permission '{perm}'. Choose from: {', '.join(valid_perms)}"

    # Update agent
    agent = registered_agents[agent_id]
    old_permissions = agent.permissions
    agent.permissions = validated_permissions
    save_agent_to_disk(agent)

    # Log update
    log_security_event(
        "permissions_updated",
        agent_id,
        {
            "old_permissions": list(old_permissions),
            "new_permissions": list(validated_permissions),
        },
        "info",
    )

    return json.dumps(
        {
            "message": f"Permissions updated for agent '{agent.name}'",
            "permissions": list(validated_permissions),
        },
        indent=2,
    )


@mcp.tool()
def list_security_events(severity: Optional[str] = None, limit: int = 20) -> str:
    """
    List recent security events, optionally filtered by severity

    Args:
        severity: Optional filter by severity (info, warning, error, critical)
        limit: Maximum number of events to return
    """
    filtered_events = security_events

    if severity:
        filtered_events = [e for e in filtered_events if e.severity == severity]

    # Sort by timestamp (most recent first) and limit
    sorted_events = sorted(filtered_events, key=lambda e: e.timestamp, reverse=True)[
        :limit
    ]

    result = []
    for event in sorted_events:
        result.append(
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "agent_id": event.agent_id,
                "details": event.details,
                "severity": event.severity,
            }
        )

    return json.dumps(result, indent=2)


# MCP Tools for Secure A2A Communication
@mcp.tool()
async def secure_agent_query(agent_id: str, query: str) -> str:
    """
    Send a secure query to another agent

    Args:
        agent_id: ID of the agent to query
        query: The query text to send
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    response = await send_secure_message(agent_id, query)

    if "error" in response:
        return f"Error: {response['error']}"

    result = {
        "agent": registered_agents[agent_id].name,
        "response": response.get("message", ""),
        "metadata": response.get("metadata", {}),
    }

    return json.dumps(result, indent=2)


@mcp.tool()
async def secure_delegate_task(
    agent_id: str, task: str, sensitivity: str = "low"
) -> str:
    """
    Securely delegate a task to another agent with sensitivity level

    Args:
        agent_id: ID of the agent to delegate to
        task: The task to delegate
        sensitivity: Task sensitivity level (low, medium, high)
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    agent = registered_agents[agent_id]

    # Check sensitivity level requirements
    if sensitivity == "high" and agent.role not in [
        SecurityRole.ADMIN,
        SecurityRole.OPERATOR,
    ]:
        log_security_event(
            "sensitive_task_blocked",
            agent_id,
            {"sensitivity": sensitivity, "required_role": "admin or operator"},
            "warning",
        )
        return "Error: High sensitivity tasks can only be delegated to admin or operator agents"

    if sensitivity == "medium" and agent.role == SecurityRole.UNTRUSTED:
        log_security_event(
            "sensitive_task_blocked",
            agent_id,
            {"sensitivity": sensitivity, "agent_role": agent.role},
            "warning",
        )
        return "Error: Medium sensitivity tasks cannot be delegated to untrusted agents"

    # Format message with sensitivity
    message = f"Task [Sensitivity: {sensitivity}]: {task}"

    response = await send_secure_message(agent_id, message)

    if "error" in response:
        return f"Error: {response['error']}"

    result = {
        "agent": agent.name,
        "sensitivity": sensitivity,
        "response": response.get("message", ""),
        "metadata": response.get("metadata", {}),
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def generate_access_token(agent_id: str, expiration_minutes: int = 30) -> str:
    """
    Generate a temporary access token for an agent

    Args:
        agent_id: ID of the agent to generate token for
        expiration_minutes: Token lifetime in minutes
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    try:
        token = generate_token(agent_id, expiration_minutes)

        return json.dumps(
            {
                "message": f"Token generated for agent '{registered_agents[agent_id].name}'",
                "token": token,
                "expires_in_minutes": expiration_minutes,
            },
            indent=2,
        )
    except ValueError as e:
        return f"Error: {str(e)}"


@mcp.tool()
def invalidate_tokens(agent_id: Optional[str] = None) -> str:
    """
    Invalidate all tokens for an agent, or all tokens if no agent specified

    Args:
        agent_id: Optional ID of agent whose tokens to invalidate
    """
    global authorized_token_hashes

    if agent_id:
        if agent_id not in registered_agents:
            return f"Error: Agent with ID {agent_id} not found"

        # We'd need to store token-to-agent mapping to do this precisely
        # For now, we'll invalidate all tokens
        token_count = len(authorized_token_hashes)
        authorized_token_hashes = set()

        log_security_event(
            "tokens_invalidated", agent_id, {"token_count": token_count}, "warning"
        )

        return json.dumps(
            {
                "message": f"All tokens invalidated due to request for agent '{registered_agents[agent_id].name}'",
                "invalidated_count": token_count,
            },
            indent=2,
        )
    else:
        token_count = len(authorized_token_hashes)
        authorized_token_hashes = set()

        log_security_event(
            "all_tokens_invalidated", None, {"token_count": token_count}, "warning"
        )

        return json.dumps(
            {"message": "All tokens invalidated", "invalidated_count": token_count},
            indent=2,
        )


# MCP Resources
@mcp.resource("security://agents")
def get_security_agents_resource() -> str:
    """Get a list of all registered agents with security information"""
    agents_list = []
    for agent_id, agent in registered_agents.items():
        agents_list.append(
            {
                "id": agent_id,
                "name": agent.name,
                "role": agent.role,
                "permissions": list(agent.permissions),
                "created_at": agent.created_at,
                "last_active": agent.last_active,
                "blocked": agent.blocked,
                "rate_limits": {
                    "per_minute": agent.rate_limit.max_calls_per_minute,
                    "per_hour": agent.rate_limit.max_calls_per_hour,
                },
            }
        )

    return json.dumps(agents_list, indent=2)


@mcp.resource("security://agent/{agent_id}")
def get_security_agent_resource(agent_id: str) -> str:
    """Get security details for a specific agent"""
    if agent_id not in registered_agents:
        return json.dumps({"error": f"Agent with ID {agent_id} not found"})

    agent = registered_agents[agent_id]
    now = time.time()

    # Calculate current rate usage
    minute_calls = sum(1 for t in agent.rate_limit.call_history if now - t < 60)
    hour_calls = len(agent.rate_limit.call_history)

    return json.dumps(
        {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "permissions": list(agent.permissions),
            "created_at": agent.created_at,
            "last_active": agent.last_active,
            "blocked": agent.blocked,
            "block_reason": agent.block_reason,
            "rate_limits": {
                "per_minute": {
                    "limit": agent.rate_limit.max_calls_per_minute,
                    "current": minute_calls,
                    "remaining": agent.rate_limit.max_calls_per_minute - minute_calls,
                },
                "per_hour": {
                    "limit": agent.rate_limit.max_calls_per_hour,
                    "current": hour_calls,
                    "remaining": agent.rate_limit.max_calls_per_hour - hour_calls,
                },
            },
        },
        indent=2,
    )


@mcp.resource("security://events")
def get_security_events_resource() -> str:
    """Get recent security events"""
    # Return the 50 most recent events
    recent_events = sorted(security_events, key=lambda e: e.timestamp, reverse=True)[
        :50
    ]

    events_list = []
    for event in recent_events:
        events_list.append(
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "agent_id": event.agent_id,
                "severity": event.severity,
            }
        )

    return json.dumps(events_list, indent=2)


# Enhanced Prompts
@mcp.prompt()
def secure_delegation_prompt(task: str, sensitivity: str) -> list:
    """Generate a structured prompt for securely delegating a sensitive task"""
    system_message = "You are a security-focused task delegation assistant. Your goal is to help format sensitive tasks securely."
    user_message = f"I need to securely delegate a {sensitivity}-sensitivity task to another agent:\n\nTask: {task}\n\nPlease help me format this task in a secure way that:\n1. Minimizes unnecessary data exposure\n2. Provides clear scope and boundaries\n3. Includes appropriate security handling instructions\n4. Follows the principle of least privilege (only share what's needed)\n\nBe specific about any security precautions that should be taken with the response."
    return [
        SamplingMessage(
            role="user", content=TextContent(type="text", text=system_message)
        ),
        SamplingMessage(
            role="user", content=TextContent(type="text", text=user_message)
        ),
    ]


@mcp.prompt()
def security_assessment_prompt(agent_id: str) -> list:
    """Generate a prompt for assessing an agent's security posture"""
    agent = registered_agents.get(agent_id)
    if not agent:
        return [
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text", text="You are a security assessment specialist."
                ),
            ),
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"The agent with ID {agent_id} does not exist. Please recommend proper agent validation procedures.",
                ),
            ),
        ]
    agent_info = {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "permissions": list(agent.permissions),
        "created_at": agent.created_at,
        "last_active": agent.last_active,
        "blocked": agent.blocked,
        "rate_limits": {
            "per_minute": agent.rate_limit.max_calls_per_minute,
            "per_hour": agent.rate_limit.max_calls_per_hour,
        },
    }
    agent_json = json.dumps(agent_info, indent=2)
    return [
        SamplingMessage(
            role="user",
            content=TextContent(
                type="text",
                text="You are a security assessment specialist for AI agents.",
            ),
        ),
        SamplingMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Please analyze this agent's security profile and provide:\n1. A comprehensive security assessment\n2. Potential vulnerabilities in the current configuration\n3. Recommendations for improving security\n4. What level of sensitive tasks this agent should be allowed to handle\n\nAgent Profile:\n{agent_json}\n\nFocus on role-based access control, rate limiting, and data handling risks.",
            ),
        ),
    ]
