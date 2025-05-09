import getpass
import os

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# API Catalog
API_CATALOG = {
    "weather": {
        "name": "OpenWeatherMap",
        "base_url": "https://api.openweathermap.org/data/2.5",
        "docs": "https://openweathermap.org/api",
        "example": "GET /weather?q=London&appid=YOUR_KEY",
        "auth": "API Key required",
    },
    "github": {
        "name": "GitHub API",
        "base_url": "https://api.github.com",
        "docs": "https://docs.github.com/rest",
        "example": "GET /users/octocat",
        "auth": "OAuth or PAT",
    },
    "jsonplaceholder": {
        "name": "JSONPlaceholder",
        "base_url": "https://jsonplaceholder.typicode.com",
        "docs": "https://jsonplaceholder.typicode.com",
        "example": "GET /posts/1",
        "auth": "None",
    },
}

mcp = FastMCP("API Discovery")


@mcp.tool()
def discover_api(api_name: str) -> str:
    """Get information about a specific API.

    Args:
        api_name: Name of the API (weather, github, etc.)

    Returns:
        Information about the API
    """
    api_name = api_name.lower()
    api = API_CATALOG.get(api_name)

    if not api:
        return f"❌ API '{api_name}' not found.\n\nAvailable APIs: {', '.join(API_CATALOG.keys())}"

    return f"""# {api["name"]}

📍 **Base URL:** `{api["base_url"]}`
📚 **Documentation:** {api["docs"]}
🔐 **Authentication:** {api["auth"]}

## Example usage:
```
{api["example"]}
```

## How to use in code:
```python
import requests

response = requests.get("{api["base_url"]}/endpoint")
data = response.json()
```
"""


@mcp.tool()
def list_apis() -> str:
    """List all available APIs.

    Returns:
        List of all available APIs
    """
    apis_list = "\n".join([f"- **{k}**: {v['name']}" for k, v in API_CATALOG.items()])
    return f"# Available APIs\n\n{apis_list}"
