#!/usr/bin/env python3
"""
77-mcp-copilot-code-companion.py - MCP AI Code Companion

This script demonstrates how to build a powerful code companion
that integrates with VSCode Copilot to provide advanced code generation,
intelligent code reviews, and contextual debugging assistance.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from mcp.client import MCPClient
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Initialize console for rich output
console = Console()

# Sample code repository for demo purposes
DEMO_REPO = {
    "project_structure": [
        "src/",
        "├── api/",
        "│   ├── __init__.py",
        "│   ├── routes.py",
        "│   └── models.py",
        "├── utils/",
        "│   ├── __init__.py",
        "│   └── helpers.py",
        "├── services/",
        "│   ├── __init__.py",
        "│   ├── auth_service.py",
        "│   └── data_service.py",
        "└── main.py"
    ],
    "code_samples": {
        "auth_service.py": """
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

SECRET_KEY = "your-secret-key-here"  # Not secure, should use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token for authentication."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict:
    """Verify a JWT token and return the payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
""",
        "routes.py": """
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from .models import User, UserCreate, UserUpdate
from ..services.auth_service import verify_token

router = APIRouter()

@router.get("/users/", response_model=List[User])
async def get_users():
    # This should query a database, but for demo we'll return static data
    return [
        {"id": 1, "username": "johndoe", "email": "john@example.com", "is_active": True},
        {"id": 2, "username": "janedoe", "email": "jane@example.com", "is_active": True}
    ]

@router.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    # This should insert into a database, but for demo we'll return static data
    return {"id": 3, "username": user.username, "email": user.email, "is_active": True}

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    # This should query a database, but for demo we'll return static data
    return {"id": user_id, "username": "testuser", "email": "test@example.com", "is_active": True}
"""
    },
    "issues": [
        {
            "file": "auth_service.py",
            "line": 6,
            "severity": "high",
            "message": "Hardcoded secret key in source code",
            "fix": "Use environment variable for SECRET_KEY"
        },
        {
            "file": "auth_service.py",
            "line": 19,
            "severity": "medium",
            "message": "Missing exception handling",
            "fix": "Add proper exception handling with specific exceptions"
        },
        {
            "file": "routes.py",
            "line": 9,
            "severity": "medium",
            "message": "Authentication not enforced",
            "fix": "Add authentication dependency to route"
        }
    ]
}

# Define Code Companion capabilities
COMPANION_CAPABILITIES = [
    {
        "name": "Smart Code Generation",
        "description": "Generate code with awareness of your full codebase, patterns, and standards",
        "examples": [
            "Generate a new SQLAlchemy model for users table",
            "Create a unit test for the auth_service module",
            "Add type hints to this function"
        ]
    },
    {
        "name": "Code Review",
        "description": "Get intelligent feedback on your code, including security issues, performance improvements, and best practices",
        "examples": [
            "Review my authentication service for security issues",
            "Check my API routes for RESTful design",
            "Find potential performance bottlenecks in my database queries"
        ]
    },
    {
        "name": "Contextual Debugging",
        "description": "Get smart suggestions to fix bugs based on error messages and runtime behavior",
        "examples": [
            "Debug why my authentication token is being rejected",
            "Fix this ImportError in my service module",
            "Help me understand this stack trace"
        ]
    },
    {
        "name": "Architecture Assistance",
        "description": "Get help with architectural decisions and implementation patterns",
        "examples": [
            "What's the best way to structure my API authentication?",
            "How should I implement caching in this service?",
            "Design a database schema for a multi-tenant application"
        ]
    }
]

class CodeCompanion:
    """AI Code Companion powered by MCP."""
    
    def __init__(self):
        """Initialize the Code Companion."""
        self.console = Console()
        # In a real implementation, we would connect to an MCP server
        # self.mcp_client = MCPClient(...)
    
    def show_intro(self) -> None:
        """Show introduction to the AI Code Companion."""
        self.console.print("\n[bold magenta]===== MCP AI Code Companion =====\n[/]")
        
        self.console.print("[bold blue]Your personal AI pair programmer powered by MCP[/]")
        self.console.print("Seamlessly integrate with VSCode and Copilot to accelerate your development workflow\n")
        
        # Show capabilities
        self.console.print("[bold cyan]Capabilities:[/]")
        for capability in COMPANION_CAPABILITIES:
            self.console.print(f"[bold green]{capability['name']}[/]")
            self.console.print(f"  {capability['description']}")
            self.console.print("  [italic]Examples:[/]")
            for example in capability['examples']:
                self.console.print(f"    • {example}")
            self.console.print()
    
    def analyze_code(self, code: str, filename: str) -> Dict[str, Any]:
        """Analyze code for issues and improvements.
        
        In a real implementation, this would use MCP tools to analyze the code.
        For this demo, we return mock analysis results.
        """
        # Check if this file has known issues in our demo data
        issues = []
        for issue in DEMO_REPO["issues"]:
            if issue["file"] == filename:
                issues.append(issue)
        
        # Generate mock analysis
        return {
            "issues": issues,
            "complexity": {
                "cyclomatic": 4,
                "cognitive": 6,
                "maintainability_index": 75
            },
            "suggestions": [
                "Add docstrings to all public functions",
                "Consider adding more type hints",
                "Break down larger functions into smaller ones"
            ],
            "security": {
                "vulnerable_dependencies": [],
                "security_hotspots": [i for i in issues if i["severity"] == "high"]
            }
        }
    
    def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate code based on a prompt and optional context.
        
        In a real implementation, this would use MCP tools to generate code.
        For this demo, we return mock generated code.
        """
        self.console.print(f"\n[bold cyan]Generating code for:[/] {prompt}")
        self.console.print("[bold yellow]Processing request...[/]")
        
        # Simulate processing
        for i in range(3):
            self.console.print(f"[dim]Analyzing context... {i+1}/3[/]")
            time.sleep(0.5)
        
        # Mock generated code based on prompt
        if "sqlalchemy model" in prompt.lower():
            return """
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    """User model for SQLAlchemy."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
"""
        elif "unit test" in prompt.lower() and "auth" in prompt.lower():
            return """
import pytest
from datetime import timedelta
from .services.auth_service import create_access_token, verify_token

def test_create_access_token():
    # Test that a token is created with the expected payload
    data = {"sub": "testuser"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)
    
    # Test with explicit expiration
    token_with_expiry = create_access_token(data, timedelta(minutes=5))
    assert token_with_expiry is not None
    assert isinstance(token_with_expiry, str)

def test_verify_token():
    # Test that a valid token can be verified
    data = {"sub": "testuser"}
    token = create_access_token(data)
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    
    # Test that an invalid token returns None
    assert verify_token("invalid-token") is None
"""
        elif "type hints" in prompt.lower():
            return """
from typing import Dict, List, Optional, Union, Any

def process_data(data: Dict[str, Any], filters: Optional[List[str]] = None) -> Dict[str, Any]:
    """Process data with optional filters.
    
    Args:
        data: The input data dictionary to process
        filters: Optional list of filters to apply
        
    Returns:
        Processed data as a dictionary
    """
    result: Dict[str, Any] = {}
    
    # Apply filters if provided
    if filters is not None:
        for key, value in data.items():
            if key in filters:
                result[key] = value
    else:
        result = data.copy()
    
    return result
"""
        else:
            return """
# Generated code based on your request
def example_function():
    """Example function generated based on your prompt."""
    # Implement your logic here
    pass
"""
    
    def review_code(self, code: str, filename: str) -> Dict[str, Any]:
        """Review code and provide feedback.
        
        In a real implementation, this would use MCP tools to review the code.
        For this demo, we return a mock review.
        """
        self.console.print(f"\n[bold cyan]Reviewing code in:[/] {filename}")
        
        # Simulate processing
        for i in range(4):
            self.console.print(f"[dim]Analyzing patterns and issues... {i+1}/4[/]")
            time.sleep(0.5)
        
        # Get analysis
        analysis = self.analyze_code(code, filename)
        
        return {
            "issues": analysis["issues"],
            "suggestions": analysis["suggestions"],
            "security_issues": analysis["security"]["security_hotspots"],
            "summary": f"Found {len(analysis['issues'])} issues and provided {len(analysis['suggestions'])} suggestions for improvement."
        }
    
    def debug_error(self, error_message: str, code_context: str) -> Dict[str, Any]:
        """Debug an error message in the context of code.
        
        In a real implementation, this would use MCP tools to debug.
        For this demo, we return mock debugging help.
        """
        self.console.print(f"\n[bold cyan]Debugging error:[/] {error_message}")
        
        # Simulate processing
        for i in range(3):
            self.console.print(f"[dim]Analyzing error context... {i+1}/3[/]")
            time.sleep(0.5)
        
        # Mock debugging response - in a real implementation would be based on the actual error
        if "jwt" in error_message.lower():
            return {
                "cause": "JWT token validation failure",
                "explanation": "The JWT token is being rejected because it's either expired or the signature doesn't match.",
                "fix": "Check that you're using the same SECRET_KEY for encoding and decoding. Also verify that the token hasn't expired.",
                "code_snippet": """
# Fix for JWT validation issue
import os
from dotenv import load_dotenv

load_dotenv()

# Use environment variable instead of hardcoded secret
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")
"""
            }
        elif "import" in error_message.lower():
            return {
                "cause": "Missing or incorrect import",
                "explanation": "The module you're trying to import doesn't exist or isn't in the Python path.",
                "fix": "Check for typos in the import statement and verify the package is installed.",
                "code_snippet": """
# Make sure the package is installed
# pip install missing-package

# Fix the import
from correct.module import needed_function

# Or use try-except to handle import errors gracefully
try:
    from optional.module import optional_function
except ImportError:
    optional_function = None
"""
            }
        else:
            return {
                "cause": "Unknown error",
                "explanation": "The error message doesn't provide enough context to determine the exact cause.",
                "fix": "Try adding more logging or print statements to narrow down the issue.",
                "code_snippet": """
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add detailed logging
logger.debug("Debug information")
logger.info("Processing step completed")
logger.error("Error occurred", exc_info=True)
"""
            }

    def display_code_review(self, review: Dict[str, Any]) -> None:
        """Display a code review in a readable format."""
        self.console.print("\n[bold magenta]Code Review Results[/]")
        
        # Display issues
        if review["issues"]:
            self.console.print("\n[bold red]Issues Found:[/]")
            for issue in review["issues"]:
                panel = Panel(
                    f"[bold]{issue['message']}[/]\n\n"
                    f"[yellow]Location:[/] Line {issue['line']}\n"
                    f"[yellow]Severity:[/] {issue['severity'].title()}\n\n"
                    f"[green]Suggested Fix:[/] {issue['fix']}",
                    title=f"Issue in {issue['file']}",
                    border_style="red"
                )
                self.console.print(panel)
        else:
            self.console.print("\n[green]No issues found! 🎉[/]")
        
        # Display suggestions
        if review["suggestions"]:
            self.console.print("\n[bold yellow]Suggestions for Improvement:[/]")
            for i, suggestion in enumerate(review["suggestions"], 1):
                self.console.print(f"{i}. {suggestion}")
        
        # Display summary
        self.console.print(f"\n[bold blue]Summary:[/] {review['summary']}")

    def display_generated_code(self, code: str, language: str = "python") -> None:
        """Display generated code with syntax highlighting."""
        self.console.print("\n[bold magenta]Generated Code:[/]")
        syntax = Syntax(code.strip(), language, theme="monokai", line_numbers=True, word_wrap=True)
        self.console.print(syntax)

    def display_debug_help(self, debug_result: Dict[str, Any]) -> None:
        """Display debugging help in a readable format."""
        self.console.print("\n[bold magenta]Debugging Results[/]")
        
        panel = Panel(
            f"[bold red]Cause:[/] {debug_result['cause']}\n\n"
            f"[yellow]Explanation:[/] {debug_result['explanation']}\n\n"
            f"[green]Recommended Fix:[/] {debug_result['fix']}",
            title="Debugging Analysis",
            border_style="yellow"
        )
        self.console.print(panel)
        
        if debug_result.get("code_snippet"):
            self.console.print("\n[bold cyan]Fix Implementation:[/]")
            syntax = Syntax(
                debug_result['code_snippet'].strip(), 
                "python", 
                theme="monokai",
                line_numbers=True,
                word_wrap=True
            )
            self.console.print(syntax)

def interactive_demo() -> None:
    """Run an interactive demo of the MCP AI Code Companion."""
    companion = CodeCompanion()
    companion.show_intro()
    
    # Menu options
    MENU_OPTIONS = {
        "1": "Generate Code",
        "2": "Review Code",
        "3": "Debug Error",
        "4": "Show Project Structure",
        "q": "Quit"
    }
    
    while True:
        # Display menu
        console.print("\n[bold green]What would you like to do?[/]")
        for key, value in MENU_OPTIONS.items():
            console.print(f"  {key}. {value}")
        
        choice = input("> ").strip().lower()
        
        if choice == "q":
            break
        
        elif choice == "1":  # Generate Code
            console.print("\n[bold cyan]Smart Code Generation[/]")
            console.print("Example prompts:")
            console.print("  1. Generate a SQLAlchemy model for users table")
            console.print("  2. Create a unit test for the auth_service module")
            console.print("  3. Add type hints to a function")
            
            prompt_choice = input("Enter a number or your own prompt: ").strip()
            
            if prompt_choice == "1":
                prompt = "Generate a SQLAlchemy model for users table"
            elif prompt_choice == "2":
                prompt = "Create a unit test for the auth_service module"
            elif prompt_choice == "3":
                prompt = "Add type hints to this function"
            else:
                prompt = prompt_choice
            
            code = companion.generate_code(prompt)
            companion.display_generated_code(code)
        
        elif choice == "2":  # Review Code
            console.print("\n[bold cyan]Code Review[/]")
            console.print("Available files to review:")
            console.print("  1. auth_service.py")
            console.print("  2. routes.py")
            
            file_choice = input("Enter a number: ").strip()
            
            if file_choice == "1":
                filename = "auth_service.py"
                code = DEMO_REPO["code_samples"]["auth_service.py"]
            elif file_choice == "2":
                filename = "routes.py"
                code = DEMO_REPO["code_samples"]["routes.py"]
            else:
                console.print("[bold red]Invalid choice[/]")
                continue
            
            # Display the code
            console.print(f"\n[bold blue]Code to review in {filename}:[/]")
            syntax = Syntax(code.strip(), "python", theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Get and display review
            review = companion.review_code(code, filename)
            companion.display_code_review(review)
        
        elif choice == "3":  # Debug Error
            console.print("\n[bold cyan]Contextual Debugging[/]")
            console.print("Example errors to debug:")
            console.print("  1. JWT token validation failure")
            console.print("  2. ImportError: No module named 'missing_module'")
            
            error_choice = input("Enter a number or describe your error: ").strip()
            
            if error_choice == "1":
                error = "PyJWTError: Signature verification failed"
                context = DEMO_REPO["code_samples"]["auth_service.py"]
            elif error_choice == "2":
                error = "ImportError: No module named 'missing_module'"
                context = "from missing_module import missing_function"
            else:
                error = error_choice
                context = ""
            
            # Get and display debugging help
            debug_result = companion.debug_error(error, context)
            companion.display_debug_help(debug_result)
        
        elif choice == "4":  # Show Project Structure
            console.print("\n[bold cyan]Project Structure[/]")
            for line in DEMO_REPO["project_structure"]:
                console.print(line)
        
        else:
            console.print("[bold red]Invalid choice[/]")

def main() -> None:
    """Main function to run the demo."""
    try:
        interactive_demo()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Demo interrupted by user. Exiting...[/]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/]")
    finally:
        console.print("\n[bold blue]Thank you for trying the MCP AI Code Companion![/]")
        console.print("[italic]This demo shows how MCP can power intelligent coding assistants that integrate with VSCode Copilot.[/]")

if __name__ == "__main__":
    main() 