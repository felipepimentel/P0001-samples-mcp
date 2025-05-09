import getpass
import os

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Code templates by API type
CODE_TEMPLATES = {
    "rest": """
import requests
from typing import Dict, Any

class {api_name}Client:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"
    
    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        response = self.session.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

# Example usage
client = {api_name}Client("https://api.example.com", "your-api-key")
data = client.get("/users/1")
""",
    "weather": '''
import requests
from datetime import datetime

def get_weather(city: str, api_key: str) -> dict:
    """Get weather data for a city"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "en"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Usage
weather = get_weather("London", "your-api-key")
print(f"Temperature in {weather['city']}: {weather['temperature']}°C")
''',
}

# Best practices by API type
BEST_PRACTICES = {
    "general": [
        "Use environment variables for API keys",
        "Implement retry with exponential backoff",
        "Cache responses when appropriate",
        "Use timeouts on all calls",
        "Handle API-specific errors",
    ],
    "weather": [
        "Cache data for 10-15 minutes",
        "Use metric units for consistency",
        "Consider rate limits of free API",
        "Implement fallback to alternative APIs",
    ],
    "github": [
        "Use GraphQL for complex queries",
        "Respect rate limits (5000/hour authenticated)",
        "Use ETags for efficient caching",
        "Paginate large results",
    ],
}

mcp = FastMCP("API Context Helper")


@mcp.tool()
def get_api_template(api_type: str) -> str:
    """Generate code template for API integration.

    Args:
        api_type: Type of API (rest, weather, github)

    Returns:
        Code template for the specified API type
    """
    api_type = api_type.lower()
    template = CODE_TEMPLATES.get(api_type, CODE_TEMPLATES["rest"])
    api_name = api_type.title()

    return f"# Code Template: {api_name} API\n\n```python{template.format(api_name=api_name)}```"


@mcp.tool()
def get_best_practices(api_type: str) -> str:
    """Get best practices for a specific API type.

    Args:
        api_type: Type of API (general, weather, github)

    Returns:
        Best practices for the specified API type
    """
    api_type = api_type.lower()
    practices = BEST_PRACTICES.get(api_type, BEST_PRACTICES["general"])

    practices_text = "\n".join([f"- {p}" for p in practices])

    return f"# Best Practices: {api_type.title()} API\n\n{practices_text}"
