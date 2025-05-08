import getpass
import os
from typing import Dict, Any
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("simplified-56-memory-cache-integration")

# Copy of tools and resources from 56-memory-cache-integration.py
# with lifecycle hooks and middleware removed
import getpass
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
# Workaround for os.getlogin issues in some environments
# Create an MCP server
# Simple in-memory cache implementation
class MemoryCache:
    def __init__(self, default_ttl_seconds=300):
        """Initialize cache with default time-to-live"""
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time to live in seconds (optional, uses default if not specified)
        """
        self.cache[key] = {"value": value, "expiry": expiry}
    def get(self, key: str) -> Optional[Any]:
        """
        Args:
            key: Cache key
        Returns:
        """
        if key not in self.cache:
            return None
        # Check if item has expired
        if datetime.now() > cache_item["expiry"]:
            # Evict expired item
            return None
        return cache_item["value"]
    def delete(self, key: str) -> bool:
        """
        Args:
            key: Cache key
        Returns:
        """
        if key in self.cache:
            return True
        return False
    def clear(self) -> int:
        """
        Returns:
        """
        return count
    def cleanup(self) -> int:
        """
        Returns:
        """
        for key in keys_to_remove:
        return len(keys_to_remove)
    def get_stats(self) -> Dict[str, Any]:
        """
        Returns:
        """
        return {
            "items": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2%}",
            "stores": self.stores,
            "evictions": self.evictions,
# Create a cache instance
# Function to create a cache key from tool name and parameters
def create_cache_key(tool_name: str, params: Dict) -> str:
    """Create a deterministic cache key from tool name and parameters"""
    key_data = f"{tool_name}:{params_str}"
    return hashlib.md5(key_data.encode()).hexdigest()
# Decorator for caching tool results
def cached_tool(ttl_seconds=None):
    """
    Args:
        ttl_seconds: Time to live in seconds (uses cache default if not specified)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            # Try to get from cache
            if cached_result is not None:
                return {"result": cached_result, "cached": True}
            # Call the function if not in cache
            # Store result in cache
            return {
                "result": result,
                "cached": False,
                "execution_time": f"{execution_time:.6f} seconds",
        return wrapper
    return decorator
# Simulated slow function to demonstrate caching
def slow_calculation(n: int) -> int:
    """Simulate a slow calculation by sleeping"""
    time.sleep(1)  # Sleep for 1 second to simulate processing
    return sum(i * i for i in range(1, n + 1))
# Simulated slow database call
def slow_database_query(query: str) -> Dict:
    """Simulate a slow database query"""
    time.sleep(1.5)  # Sleep for 1.5 seconds to simulate database query
    return {"query": query, "rows": 42, "timestamp": datetime.now().isoformat()}
# Tools demonstrating cache usage
@mcp.tool()
def calculate_sum_of_squares(n: int) -> Dict[str, Any]:
    """
    Args:
        n: Upper limit for calculation
    """
    return {
        "n": n,
        "sum_of_squares": result,
        "formula": "sum(i^2) for i in range(1, n+1)",
@mcp.tool()
def fetch_data(query: str) -> Dict[str, Any]:
    """
    Args:
        query: Database query string
    """
    return {"query_result": result, "fetched_at": datetime.now().isoformat()}
@mcp.tool()
def invalidate_cache(
    tool_name: Optional[str] = None, params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Args:
        tool_name: Optional specific tool name to invalidate
        params: Optional parameters to create a specific cache key
    """
    if tool_name and params:
        # Invalidate specific cache entry
        return {
            "invalidated": deleted,
            "key": cache_key,
            "tool": tool_name,
            "params": params,
    elif tool_name:
        # We can't easily invalidate by tool name only, so inform the user
        return {
            "invalidated": False,
            "error": "Cannot invalidate by tool name only, parameters required",
            "tool": tool_name,
    else:
        # Clear entire cache
        return {
            "invalidated": True,
            "cleared_count": cleared_count,
            "message": "Entire cache cleared",
@mcp.tool()
def get_cache_stats() -> Dict[str, Any]:
    """
    """
    # Run cleanup to remove expired items first
    return stats
# Tool to demonstrate the cache system
@mcp.tool()
def cache_demo() -> Dict[str, Any]:
    """
    """
    # Clear the cache to start fresh
    results.append({"step": "Cache cleared", "stats": cache.get_stats()})
    # First call - should be a cache miss
            "step": "First call (cache miss)",
            "time": f"{time1:.3f} seconds",
            "result": result1,
    # Second call - should be a cache hit
            "step": "Second call (cache hit)",
            "time": f"{time2:.3f} seconds",
            "result": result2,
            "speedup": f"{time1 / time2:.1f}x faster",
    # Call with different parameters - should be a cache miss
            "step": "Different parameter (cache miss)",
            "time": f"{time3:.3f} seconds",
            "result": result3,
    # Final cache stats
    results.append({"step": "Final cache statistics", "stats": cache.get_stats()})
    return {
        "demo_results": results,
        "summary": "Demonstrates how repeated calls with the same parameters are served from cache",
# Resources
@mcp.resource("cache://stats")
def get_cache_stats_resource() -> str:
    """Get cache statistics as a resource"""
    return json.dumps(get_cache_stats(), indent=2)
# Middleware to log cache activity
async def cache_stats_middleware(message, next_handler):
    """Middleware to track cache usage"""
    # Process the message normally
    # Track cache stats for tool calls
    ):
        if isinstance(tool_result, dict) and "cached" in tool_result:
            # Log cache hit/miss
            sys.stderr.write(f"CACHE {cache_status} [{timestamp}]: {tool_name}\n")
    return response
# Explain what this demo does when run with MCP CLI
sys.stderr.write("This example demonstrates MCP with in-memory caching:\n")
# Schedule periodic cache cleanup (every 60 seconds)
import threading
def periodic_cleanup():
    """Run cache cleanup periodically"""
    while True:
        if removed > 0:
            sys.stderr.write(f"Cache cleanup: removed {removed} expired items\n")
# Start cleanup thread
# This server demonstrates MCP with in-memory caching
# Run with: uv run mcp dev 56-memory-cache-integration.py

if __name__ == "__main__":
    print("MCP Server ready to run!")
    # The server will be run by MCP CLI
    
# Run with: uv run mcp dev simplified-56-memory-cache-integration.py
