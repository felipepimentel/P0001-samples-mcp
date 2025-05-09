import getpass
import json
import os
import re
from typing import Dict, List, Optional, Any, Union

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Code Companion")

# Cache for code analysis to avoid redundant processing
analysis_cache = {}

@mcp.tool()
def analyze_code(code: str, language: str = "python", filename: str = "unknown.py") -> str:
    """Analyze code for issues, complexity, and improvement suggestions.
    
    Args:
        code: The source code to analyze
        language: Programming language of the code
        filename: Name of the file for reference
        
    Returns:
        Analysis report with issues, metrics, and suggestions
    """
    # Use cached analysis if available
    cache_key = f"{filename}:{hash(code)}"
    if cache_key in analysis_cache:
        return analysis_cache[cache_key]
    
    # Initialize analysis result
    analysis = {
        "issues": [],
        "metrics": {
            "lines": len(code.strip().split("\n")),
            "complexity": estimate_complexity(code, language),
        },
        "suggestions": []
    }
    
    # Python-specific analysis
    if language.lower() == "python":
        # Check for security issues
        if "SECRET_KEY" in code and re.search(r'SECRET_KEY\s*=\s*[\'"][^\'"]+[\'"]', code):
            analysis["issues"].append({
                "severity": "high",
                "line": find_line_number(code, "SECRET_KEY"),
                "message": "Hardcoded secret key detected in source code",
                "fix": "Use environment variables for sensitive data"
            })
            
        # Check for proper exception handling
        if "except:" in code and not re.search(r'except\s+\w+', code):
            analysis["issues"].append({
                "severity": "medium", 
                "line": find_line_number(code, "except:"),
                "message": "Bare except clause used",
                "fix": "Catch specific exceptions instead of using bare except"
            })
            
        # Check for missing docstrings
        if re.search(r'def\s+\w+[^#]*:', code) and not re.search(r'def\s+\w+[^#]*:\s*\n\s*[\'"]', code):
            analysis["issues"].append({
                "severity": "low",
                "line": find_line_number(code, "def"),
                "message": "Missing docstring in function",
                "fix": "Add a docstring to describe function purpose and parameters"
            })
            
        # Check for type hints
        if re.search(r'def\s+\w+\([^)]*\):', code) and not re.search(r'def\s+\w+\([^)]*\)\s*->\s*\w+\s*:', code):
            analysis["suggestions"].append("Add return type hints to functions")
            
        # Suggest improvements
        if "print(" in code:
            analysis["suggestions"].append("Consider using a logger instead of print statements")
            
        if "import *" in code:
            analysis["suggestions"].append("Avoid wildcard imports for better code clarity")
    
    # Format result as markdown
    result = format_analysis_as_markdown(analysis, filename, language)
    
    # Cache analysis for future use
    analysis_cache[cache_key] = result
    
    return result

@mcp.tool()
def generate_code(prompt: str, language: str = "python", context: Optional[str] = None) -> str:
    """Generate code based on a prompt and optional context.
    
    Args:
        prompt: Description of what code to generate
        language: Programming language to use
        context: Optional existing code or context for the generation
        
    Returns:
        Generated code with explanation
    """
    # For this example, we'll simulate different code generation cases
    # In a real implementation, this would use LLM-based code generation
    
    if "model" in prompt.lower() and "sqlalchemy" in prompt.lower():
        code = """
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    """User model for authentication and profile data."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="author")
    
    def __repr__(self):
        return f"<User {self.username}>"
"""
        explanation = """
# Code Explanation

This SQLAlchemy model defines a User table with:

- Primary key ID field
- Unique username and email fields
- Password storage (hashed)
- Active status flag
- Creation timestamp
- Relationship to a Posts table

**Best Practices Applied:**
- Strong type definitions
- Sensible defaults
- Clear documentation
- Unique constraints on username/email
- Proper relationship definition

**Next Steps:**
1. Add this model to your database initialization
2. Create migration scripts if needed
3. Add validation logic in your service layer
"""

    elif "test" in prompt.lower():
        code = """
import pytest
from datetime import timedelta
from app.services.auth import create_access_token, verify_token
from app.models.user import User

# Fixtures
@pytest.fixture
def sample_user():
    return User(id=1, username="testuser", email="test@example.com")

@pytest.fixture
def token_payload(sample_user):
    return {"sub": str(sample_user.id), "username": sample_user.username}

# Tests
def test_create_access_token(token_payload):
    # Test token creation
    token = create_access_token(token_payload)
    assert token is not None
    assert isinstance(token, str)
    
    # Test with custom expiration
    token_with_expiry = create_access_token(token_payload, timedelta(minutes=5))
    assert token_with_expiry != token

def test_verify_token(token_payload):
    # Test successful verification
    token = create_access_token(token_payload)
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == token_payload["sub"]
    
    # Test invalid token
    with pytest.raises(Exception):
        verify_token("invalid-token")
        
    # Test expired token
    expired_token = create_access_token(token_payload, timedelta(seconds=0))
    import time
    time.sleep(1)
    with pytest.raises(Exception):
        verify_token(expired_token)
"""
        explanation = """
# Code Explanation

This test suite validates the authentication token system with:

- Tests for token creation functionality
- Tests for token verification
- Tests for handling invalid tokens
- Tests for token expiration

**Testing Patterns Used:**
- Pytest fixtures for test setup
- Multiple assertions per test for comprehensive validation
- Exception testing with context managers
- Parameterized test cases

**Coverage:**
- Token generation
- Token validation
- Error handling
- Expiration logic

**Note:** You may need to adjust imports to match your project structure.
"""

    elif "api" in prompt.lower() and "endpoint" in prompt.lower():
        code = """
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.models.item import Item
from app.db.database import get_db
from app.auth.deps import get_current_user

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=List[ItemResponse])
def get_items(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a list of items with pagination."""
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new item."""
    db_item = Item(**item.dict(), owner_id=current_user.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing item."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this item")
    
    # Update fields
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an item."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")
    
    db.delete(db_item)
    db.commit()
    return None
"""
        explanation = """
# Code Explanation

This FastAPI router implements a RESTful CRUD API for an "items" resource:

- GET /items - List all items with pagination
- POST /items - Create a new item
- GET /items/{id} - Get a specific item
- PUT /items/{id} - Update an item
- DELETE /items/{id} - Delete an item

**Features Implemented:**
- Authentication using FastAPI dependency injection
- Authorization via ownership checks
- Database operations with SQLAlchemy
- Error handling with proper HTTP status codes
- Input validation via Pydantic schemas
- Detailed documentation via docstrings

**Best Practices:**
- Clear separation of routes and business logic
- Consistent error handling patterns
- Proper use of HTTP methods and status codes
- Resource ownership protection
"""
    else:
        code = """
# Generated code based on your description
def example_function():
    """This is a placeholder implementation."""
    # TODO: Implement specific logic based on requirements
    pass
"""
        explanation = """
# Code Generation

Please provide more specific details about what you'd like to generate.
Examples of specific requests:

- "Generate a SQLAlchemy model for users table"
- "Create a REST API endpoint for user authentication" 
- "Write a unit test for password hashing functions"

The more specific details you provide, the better the generated code will match your needs.
"""

    # Format the result as markdown combining code and explanation
    result = f"""
# Generated Code

```{language}
{code.strip()}
```

{explanation}
"""
    
    return result

@mcp.tool()
def debug_error(error_message: str, code_context: Optional[str] = None, language: str = "python") -> str:
    """Debug an error message and suggest fixes.
    
    Args:
        error_message: The error message to analyze
        code_context: Optional code where the error occurred
        language: Programming language of the code
        
    Returns:
        Debugging analysis with suggested fixes
    """
    # For this example, we'll simulate different debugging scenarios
    # In a real implementation, this would use more advanced error analysis
    
    if "jwt" in error_message.lower() or "token" in error_message.lower():
        cause = "JWT token validation failure"
        explanation = """
The JWT token is being rejected because of one of these common causes:
1. The signature doesn't match (wrong secret key)
2. The token has expired
3. The token payload format is incorrect
"""
        fix_code = """
# Fix for JWT validation issues
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get secret key from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")

# Improved token verification with better error handling
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        # Handle expired token specifically
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        # Handle other token validation errors
        raise ValueError(f"Invalid token: {str(e)}")
"""
    
    elif "import" in error_message.lower():
        cause = "Module import error"
        explanation = """
The Python interpreter couldn't find the module you're trying to import. This could be due to:
1. The module isn't installed
2. There's a typo in the import statement
3. The module is installed but not in the Python path
"""
        fix_code = """
# Option 1: Install the missing package
# pip install missing-package

# Option 2: Fix potential typo in import
# from correct_package import module

# Option 3: Add the module path to Python path
import sys
import os

# Add the directory containing the module to the Python path
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_path not in sys.path:
    sys.path.append(module_path)

# Now try importing
try:
    from module import function
except ImportError as e:
    print(f"Import still failed: {e}")
    # Fallback option if available
"""

    elif "key error" in error_message.lower() or "keyerror" in error_message.lower():
        cause = "Dictionary key error"
        explanation = """
A KeyError occurs when you try to access a dictionary key that doesn't exist.
This is similar to trying to access an undefined property of an object in other languages.
"""
        fix_code = """
# Option 1: Check if key exists before accessing
if key in my_dict:
    value = my_dict[key]
else:
    value = default_value

# Option 2: Use get() method with default
value = my_dict.get(key, default_value)

# Option 3: Try/except pattern
try:
    value = my_dict[key]
except KeyError:
    value = default_value
    # Or handle the error in another way
"""

    else:
        cause = "General error"
        explanation = """
Without more specific error details, it's difficult to provide targeted debugging.
Here are some general debugging approaches that might help:
1. Add print statements or logging to trace execution flow
2. Check variable types using type() or isinstance()
3. Use a debugger to step through the code
4. Break complex expressions into smaller steps
"""
        fix_code = """
# General debugging techniques

# 1. Add detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Variable value: {variable}")
logger.info("Operation completed")
logger.error("Error occurred", exc_info=True)

# 2. Check variable types
print(f"Type of variable: {type(variable)}")

# 3. Simplify complex expressions
# Instead of: result = complex_function(another_function(variable))
temp_result = another_function(variable)
print(f"Intermediate result: {temp_result}")
final_result = complex_function(temp_result)

# 4. Use try/except for better error handling
try:
    result = potentially_failing_function()
except Exception as e:
    print(f"Error details: {type(e).__name__}: {str(e)}")
    # Handle or re-raise as appropriate
"""
    
    # Format the result as markdown
    result = f"""
# Debugging Analysis: {cause}

## Error
```
{error_message}
```

## Explanation
{explanation}

## Suggested Fix
```python
{fix_code.strip()}
```

## Debugging Tips
1. Test the fix in isolation before integrating
2. Add logging/print statements at key points
3. Consider unit tests to verify the fix works
4. Check documentation for the specific error
"""
    
    return result

# Helper functions
def estimate_complexity(code: str, language: str) -> Dict[str, int]:
    """Estimate code complexity metrics."""
    # In a real implementation, this would use language-specific analysis
    lines = code.strip().split('\n')
    
    # Very simplistic complexity estimate based on code patterns
    function_count = len(re.findall(r'def\s+\w+', code))
    class_count = len(re.findall(r'class\s+\w+', code))
    control_flow_count = len(re.findall(r'if|else|elif|for|while|try|except', code))
    
    # Cyclomatic complexity (very rough approximation)
    cyclomatic = control_flow_count + 1
    
    # Cognitive complexity (even rougher approximation)
    nesting_levels = max([len(re.findall(r'^\s+', line)) // 4 for line in lines if line.strip()], default=0)
    cognitive = control_flow_count + nesting_levels * 2
    
    return {
        "cyclomatic": cyclomatic,
        "cognitive": cognitive,
        "function_count": function_count,
        "class_count": class_count,
        "nesting_max": nesting_levels
    }

def find_line_number(code: str, pattern: str) -> int:
    """Find the line number for a pattern in code."""
    lines = code.strip().split('\n')
    for i, line in enumerate(lines, 1):
        if pattern in line:
            return i
    return 0

def format_analysis_as_markdown(analysis: Dict[str, Any], filename: str, language: str) -> str:
    """Format code analysis as a markdown string."""
    issues_count = len(analysis["issues"])
    metrics = analysis["metrics"]
    suggestions = analysis["suggestions"]
    
    # Create the markdown output
    result = f"""
# Code Analysis: {filename}

## Summary
- **Language**: {language}
- **Lines**: {metrics['lines']}
- **Issues Found**: {issues_count}
- **Suggestions**: {len(suggestions)}

## Complexity Metrics
- Cyclomatic Complexity: {metrics['complexity']['cyclomatic']}
- Cognitive Complexity: {metrics['complexity'].get('cognitive', 'N/A')}
- Functions: {metrics['complexity'].get('function_count', 'N/A')}
- Classes: {metrics['complexity'].get('class_count', 'N/A')}
"""

    # Add issues section if there are any
    if issues_count > 0:
        result += "\n## Issues\n"
        for i, issue in enumerate(analysis["issues"], 1):
            result += f"""
### Issue {i}: {issue['message']}
- **Severity**: {issue['severity']}
- **Line**: {issue['line']}
- **Suggested Fix**: {issue['fix']}
"""

    # Add suggestions section if there are any
    if suggestions:
        result += "\n## Improvement Suggestions\n"
        for i, suggestion in enumerate(suggestions, 1):
            result += f"- {suggestion}\n"
    
    return result

if __name__ == "__main__":
    # This will be executed when the server is run directly
    import os

    os.environ["MCP_INSPECTOR_URL"] = "http://127.0.0.1:6274"
    mcp.serve_stdio() 