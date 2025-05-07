import hashlib
import hmac
import json
import os
import re
import secrets
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Security and Authentication")

# Simulated user database - in production this would be a real database
# Format: {"username": {"password_hash": "...", "salt": "...", "role": "...", "api_keys": [...]}}
USER_DB_PATH = os.path.join(os.path.expanduser("~"), "mcp_users.json")


# User roles with different permission levels
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass
class User:
    username: str
    password_hash: str
    salt: str
    role: UserRole
    api_keys: List[str]
    last_login: Optional[float] = None


# Authentication token store with expiration
# Format: {"token": {"username": "...", "expires_at": timestamp}}
active_tokens = {}


# Initialize user database if it doesn't exist
def init_user_db():
    if os.path.exists(USER_DB_PATH):
        return

    # Create initial admin user with a random password
    admin_password = secrets.token_urlsafe(12)
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", admin_password.encode(), salt.encode(), 100000
    ).hex()

    users = {
        "admin": {
            "password_hash": password_hash,
            "salt": salt,
            "role": "admin",
            "api_keys": [secrets.token_urlsafe(32)],
            "last_login": None,
        }
    }

    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f, indent=2)

    print(f"Created initial admin user with password: {admin_password}")
    print("Please change this password immediately after first login.")


# Initialize the user database
init_user_db()


# Load users from the database
def load_users() -> Dict[str, User]:
    if not os.path.exists(USER_DB_PATH):
        return {}

    with open(USER_DB_PATH, "r") as f:
        user_dict = json.load(f)

    users = {}
    for username, data in user_dict.items():
        users[username] = User(
            username=username,
            password_hash=data["password_hash"],
            salt=data["salt"],
            role=UserRole(data["role"]),
            api_keys=data["api_keys"],
            last_login=data.get("last_login"),
        )

    return users


# Save users to the database
def save_users(users: Dict[str, User]):
    user_dict = {}
    for username, user in users.items():
        user_dict[username] = {
            "password_hash": user.password_hash,
            "salt": user.salt,
            "role": user.role,
            "api_keys": user.api_keys,
            "last_login": user.last_login,
        }

    with open(USER_DB_PATH, "w") as f:
        json.dump(user_dict, f, indent=2)


# Input validation helpers
def is_valid_username(username: str) -> bool:
    """Check if username is valid (3-20 chars, alphanumeric and underscores only)"""
    return bool(re.match(r"^[a-zA-Z0-9_]{3,20}$", username))


def is_valid_password(password: str) -> bool:
    """Check if password is valid (min 8 chars, at least one letter and one number)"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


def is_strong_password(password: str) -> bool:
    """Check if password is strong (min 10 chars, uppercase, lowercase, number, special char)"""
    if len(password) < 10:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


# Authentication helpers
def verify_password(username: str, password: str) -> bool:
    """Verify a user's password"""
    users = load_users()
    if username not in users:
        return False

    user = users[username]
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), user.salt.encode(), 100000
    ).hex()

    return hmac.compare_digest(password_hash, user.password_hash)


def create_auth_token(username: str) -> str:
    """Create an authentication token for a user that expires in 1 hour"""
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + 3600  # 1 hour from now

    active_tokens[token] = {"username": username, "expires_at": expires_at}

    return token


def verify_token(token: str) -> Optional[str]:
    """Verify an authentication token and return the username if valid"""
    if token not in active_tokens:
        return None

    token_data = active_tokens[token]
    if token_data["expires_at"] < time.time():
        # Token expired
        del active_tokens[token]
        return None

    return token_data["username"]


def verify_api_key(api_key: str) -> Optional[str]:
    """Verify an API key and return the username if valid"""
    users = load_users()
    for username, user in users.items():
        if api_key in user.api_keys:
            return username
    return None


def user_has_permission(username: str, required_role: UserRole) -> bool:
    """Check if a user has the required role permission"""
    users = load_users()
    if username not in users:
        return False

    user_role = users[username].role

    # Role hierarchy: ADMIN > USER > GUEST
    if user_role == UserRole.ADMIN:
        return True
    if user_role == UserRole.USER and required_role != UserRole.ADMIN:
        return True
    if user_role == UserRole.GUEST and required_role == UserRole.GUEST:
        return True

    return False


# MCP Tools
@mcp.tool()
def register_user(username: str, password: str) -> str:
    """
    Register a new user with GUEST permissions

    Args:
        username: Desired username (3-20 chars, alphanumeric and underscores only)
        password: Password (min 8 chars, must include at least one letter and one number)
    """
    # Input validation
    if not is_valid_username(username):
        return "Error: Invalid username. Must be 3-20 characters, using only letters, numbers, and underscores."

    if not is_valid_password(password):
        return "Error: Password too weak. Must be at least 8 characters with at least one letter and one number."

    users = load_users()
    if username in users:
        return f"Error: Username '{username}' is already taken."

    # Create new user with GUEST role
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    ).hex()

    users[username] = User(
        username=username,
        password_hash=password_hash,
        salt=salt,
        role=UserRole.GUEST,
        api_keys=[],
        last_login=None,
    )

    save_users(users)
    return f"User '{username}' registered successfully with GUEST permissions."


@mcp.tool()
def login(username: str, password: str) -> str:
    """
    Login with username and password to get an authentication token

    Args:
        username: User's username
        password: User's password
    """
    if not verify_password(username, password):
        return "Error: Invalid username or password."

    # Update last login time
    users = load_users()
    users[username].last_login = time.time()
    save_users(users)

    # Create authentication token
    token = create_auth_token(username)

    return json.dumps(
        {
            "token": token,
            "expires_in": 3600,  # 1 hour
            "user": username,
            "role": users[username].role,
        }
    )


@mcp.tool()
def create_api_key(username: str, password: str) -> str:
    """
    Create a new API key for a user

    Args:
        username: User's username
        password: User's password
    """
    if not verify_password(username, password):
        return "Error: Invalid username or password."

    users = load_users()
    user = users[username]

    # Generate new API key
    api_key = secrets.token_urlsafe(32)
    user.api_keys.append(api_key)

    # Limit to 3 API keys per user
    if len(user.api_keys) > 3:
        user.api_keys.pop(0)  # Remove oldest key

    save_users(users)

    return json.dumps(
        {
            "api_key": api_key,
            "message": "API key created successfully. Store this key securely as it won't be shown again.",
        }
    )


@mcp.tool()
def change_password(username: str, current_password: str, new_password: str) -> str:
    """
    Change a user's password

    Args:
        username: User's username
        current_password: Current password
        new_password: New password
    """
    if not verify_password(username, current_password):
        return "Error: Invalid username or password."

    if not is_valid_password(new_password):
        return "Error: New password is too weak. Must be at least 8 characters with at least one letter and one number."

    # Additional check for strong password
    if not is_strong_password(new_password):
        return "Warning: Password meets minimum requirements but is not strong. Consider using a stronger password with at least 10 characters including uppercase, lowercase, numbers, and special characters."

    users = load_users()
    user = users[username]

    # Update password
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", new_password.encode(), salt.encode(), 100000
    ).hex()

    user.password_hash = password_hash
    user.salt = salt

    # Invalidate all API keys for security
    user.api_keys = []

    save_users(users)

    # Revoke all active tokens for this user
    for token in list(active_tokens.keys()):
        if active_tokens[token]["username"] == username:
            del active_tokens[token]

    return "Password changed successfully. All API keys have been revoked for security."


@mcp.tool()
def protected_admin_tool(token: str, action: str) -> str:
    """
    Execute an admin-only action

    Args:
        token: Authentication token
        action: Admin action to perform
    """
    username = verify_token(token)
    if not username:
        return "Error: Invalid or expired token. Please log in again."

    if not user_has_permission(username, UserRole.ADMIN):
        return "Error: Admin permission required for this operation."

    # Execute admin action (simplified for example)
    if action == "list_users":
        users = load_users()
        user_list = [
            {
                "username": username,
                "role": user.role,
                "api_keys_count": len(user.api_keys),
                "last_login": user.last_login,
            }
            for username, user in users.items()
        ]
        return json.dumps(user_list, indent=2)
    elif action == "system_status":
        return json.dumps(
            {
                "active_tokens": len(active_tokens),
                "registered_users": len(load_users()),
                "server_time": time.time(),
            },
            indent=2,
        )
    else:
        return f"Error: Unknown admin action '{action}'."


@mcp.tool()
def api_request(api_key: str, resource: str) -> str:
    """
    Make an API request using an API key

    Args:
        api_key: User's API key
        resource: Resource to access
    """
    username = verify_api_key(api_key)
    if not username:
        return "Error: Invalid API key."

    users = load_users()
    user = users[username]

    # Example resources with different permission levels
    if resource == "public_data":
        # Accessible to all roles
        return json.dumps(
            {
                "message": "This is public data accessible to all users.",
                "timestamp": time.time(),
            }
        )
    elif resource == "user_data":
        # Requires USER role or higher
        if not user_has_permission(username, UserRole.USER):
            return "Error: User permission required to access this resource."

        return json.dumps(
            {
                "message": "This is user data accessible to USER and ADMIN roles.",
                "username": username,
                "timestamp": time.time(),
            }
        )
    elif resource == "admin_data":
        # Requires ADMIN role
        if not user_has_permission(username, UserRole.ADMIN):
            return "Error: Admin permission required to access this resource."

        return json.dumps(
            {
                "message": "This is admin data accessible only to ADMIN role.",
                "active_users": len(active_tokens),
                "timestamp": time.time(),
            }
        )
    else:
        return f"Error: Unknown resource '{resource}'."


@mcp.resource("auth://status")
def get_auth_status() -> str:
    """Get information about the authentication system"""
    users = load_users()

    return json.dumps(
        {
            "active_sessions": len(active_tokens),
            "registered_users": len(users),
            "roles": {
                role.value: sum(1 for user in users.values() if user.role == role)
                for role in UserRole
            },
        },
        indent=2,
    )
