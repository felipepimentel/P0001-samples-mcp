import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("API Integration")


# Simple rate limiter
class RateLimiter:
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_times = []

    async def wait_if_needed(self):
        """Wait if we've exceeded our rate limit"""
        now = time.time()

        # Remove calls older than 60 seconds
        self.call_times = [t for t in self.call_times if now - t < 60]

        # If we've made too many calls, wait
        if len(self.call_times) >= self.calls_per_minute:
            oldest_call = self.call_times[0]
            wait_time = 60 - (now - oldest_call)
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        # Record this call
        self.call_times.append(time.time())


# Create a rate limiter for API calls
weather_limiter = RateLimiter(calls_per_minute=10)


@dataclass
class WeatherData:
    temperature: float
    conditions: str
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    location: Optional[str] = None


# API client with retries and error handling
async def fetch_weather(location: str) -> Dict:
    """Fetch weather data from a public API with proper error handling"""
    # Wait if we're rate limited
    await weather_limiter.wait_if_needed()

    url = "https://api.openweathermap.org/data/2.5/weather"

    # This is a free API key for demo purposes only - would use env vars in real app
    # Free tier has very limited calls, replace with your own if needed
    params = {
        "q": location,
        "appid": "1a2b3c4d5e6f7a8b9c0d",  # Fake API key
        "units": "metric",
    }

    max_retries = 3
    backoff = 1

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", backoff))
                    await asyncio.sleep(retry_after)
                elif response.status_code == 404:
                    return {"error": f"Location '{location}' not found"}
                else:
                    # For other errors, retry with exponential backoff
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                    else:
                        return {
                            "error": f"API error: {response.status_code} - {response.text}"
                        }
        except (httpx.RequestError, asyncio.TimeoutError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff)
                backoff *= 2
            else:
                return {"error": f"Connection error: {str(e)}"}

    return {"error": "Maximum retries exceeded"}


@mcp.tool()
async def get_weather(location: str) -> str:
    """
    Get current weather information for a location

    Args:
        location: City name (e.g., "London", "New York", "Tokyo")
    """
    try:
        weather_data = await fetch_weather(location)

        if "error" in weather_data:
            return f"Error: {weather_data['error']}"

        # Parse the response
        weather = WeatherData(
            temperature=weather_data["main"]["temp"],
            conditions=weather_data["weather"][0]["description"],
            humidity=weather_data["main"].get("humidity"),
            wind_speed=weather_data["wind"].get("speed"),
            location=f"{weather_data['name']}, {weather_data.get('sys', {}).get('country', '')}",
        )

        # Format the output
        result = [
            f"Weather for {weather.location}:",
            f"Temperature: {weather.temperature}°C",
            f"Conditions: {weather.conditions}",
        ]

        if weather.humidity is not None:
            result.append(f"Humidity: {weather.humidity}%")

        if weather.wind_speed is not None:
            result.append(f"Wind Speed: {weather.wind_speed} m/s")

        return "\n".join(result)

    except Exception as e:
        # Catch any other unexpected errors
        return f"Error retrieving weather data: {str(e)}"


@mcp.tool()
async def get_multi_city_weather(locations: List[str]) -> str:
    """
    Get weather for multiple cities at once

    Args:
        locations: List of city names
    """
    if not locations:
        return "Error: No locations provided"

    if len(locations) > 5:
        return "Error: Maximum 5 locations allowed at once"

    # Fetch weather for all cities concurrently
    results = []

    for location in locations:
        # Process one at a time to respect rate limits
        weather = await get_weather(location)
        results.append(f"== {location} ==\n{weather}")

    return "\n\n".join(results)
