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
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("MemoryCachedMCP")


# Simple in-memory cache implementation
class MemoryCache:
    def __init__(self, default_ttl_seconds=300):
        """Initialize cache with default time-to-live"""
        self.cache = {}
        self.default_ttl = default_ttl_seconds
        self.hits = 0
        self.misses = 0
        self.stores = 0
        self.evictions = 0

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store a value in the cache

        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time to live in seconds (optional, uses default if not specified)
        """
        expiry = datetime.now() + timedelta(seconds=ttl_seconds or self.default_ttl)
        self.cache[key] = {"value": value, "expiry": expiry}
        self.stores += 1

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache

        Args:
            key: Cache key

        Returns:
            The stored value or None if not found or expired
        """
        if key not in self.cache:
            self.misses += 1
            return None

        cache_item = self.cache[key]

        # Check if item has expired
        if datetime.now() > cache_item["expiry"]:
            # Evict expired item
            del self.cache[key]
            self.evictions += 1
            self.misses += 1
            return None

        self.hits += 1
        return cache_item["value"]

    def delete(self, key: str) -> bool:
        """
        Delete an item from the cache

        Args:
            key: Cache key

        Returns:
            True if item was deleted, False if it didn't exist
        """
        if key in self.cache:
            del self.cache[key]
            self.evictions += 1
            return True
        return False

    def clear(self) -> int:
        """
        Clear all items from the cache

        Returns:
            Number of items cleared
        """
        count = len(self.cache)
        self.cache = {}
        self.evictions += count
        return count

    def cleanup(self) -> int:
        """
        Remove all expired items from the cache

        Returns:
            Number of items removed
        """
        now = datetime.now()
        keys_to_remove = [
            key for key, item in self.cache.items() if now > item["expiry"]
        ]

        for key in keys_to_remove:
            del self.cache[key]

        self.evictions += len(keys_to_remove)
        return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict containing cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "items": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2%}",
            "stores": self.stores,
            "evictions": self.evictions,
        }


# Create a cache instance
cache = MemoryCache(default_ttl_seconds=60)


# Function to create a cache key from tool name and parameters
def create_cache_key(tool_name: str, params: Dict) -> str:
    """Create a deterministic cache key from tool name and parameters"""
    params_str = json.dumps(params, sort_keys=True)
    key_data = f"{tool_name}:{params_str}"
    return hashlib.md5(key_data.encode()).hexdigest()


# Decorator for caching tool results
def cached_tool(ttl_seconds=None):
    """
    Decorator to cache tool results

    Args:
        ttl_seconds: Time to live in seconds (uses cache default if not specified)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = create_cache_key(func.__name__, kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return {"result": cached_result, "cached": True}

            # Call the function if not in cache
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Store result in cache
            cache.set(cache_key, result, ttl_seconds)

            return {
                "result": result,
                "cached": False,
                "execution_time": f"{execution_time:.6f} seconds",
            }

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
@cached_tool(ttl_seconds=30)
def calculate_sum_of_squares(n: int) -> Dict[str, Any]:
    """
    Calculate sum of squares from 1 to n (cached for 30 seconds)

    Args:
        n: Upper limit for calculation

    This function demonstrates caching a computationally expensive operation
    """
    result = slow_calculation(n)
    return {
        "n": n,
        "sum_of_squares": result,
        "formula": "sum(i^2) for i in range(1, n+1)",
    }


@mcp.tool()
@cached_tool(ttl_seconds=60)
def fetch_data(query: str) -> Dict[str, Any]:
    """
    Fetch data from a simulated database (cached for 60 seconds)

    Args:
        query: Database query string

    This function demonstrates caching an expensive I/O operation
    """
    result = slow_database_query(query)
    return {"query_result": result, "fetched_at": datetime.now().isoformat()}


@mcp.tool()
def invalidate_cache(
    tool_name: Optional[str] = None, params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Invalidate cache entries

    Args:
        tool_name: Optional specific tool name to invalidate
        params: Optional parameters to create a specific cache key

    Returns status of the invalidation operation
    """
    if tool_name and params:
        # Invalidate specific cache entry
        cache_key = create_cache_key(tool_name, params)
        deleted = cache.delete(cache_key)
        return {
            "invalidated": deleted,
            "key": cache_key,
            "tool": tool_name,
            "params": params,
        }
    elif tool_name:
        # We can't easily invalidate by tool name only, so inform the user
        return {
            "invalidated": False,
            "error": "Cannot invalidate by tool name only, parameters required",
            "tool": tool_name,
        }
    else:
        # Clear entire cache
        cleared_count = cache.clear()
        return {
            "invalidated": True,
            "cleared_count": cleared_count,
            "message": "Entire cache cleared",
        }


@mcp.tool()
def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics

    Returns information about cache performance and utilization
    """
    # Run cleanup to remove expired items first
    expired_removed = cache.cleanup()

    stats = cache.get_stats()
    stats["expired_removed"] = expired_removed
    stats["timestamp"] = datetime.now().isoformat()

    return stats


# Tool to demonstrate the cache system
@mcp.tool()
def cache_demo() -> Dict[str, Any]:
    """
    Run a demonstration of the cache system

    This tool performs a sequence of operations to show how caching works
    """
    results = []

    # Clear the cache to start fresh
    cache.clear()
    results.append({"step": "Cache cleared", "stats": cache.get_stats()})

    # First call - should be a cache miss
    start = time.time()
    result1 = calculate_sum_of_squares(100)
    time1 = time.time() - start
    results.append(
        {
            "step": "First call (cache miss)",
            "time": f"{time1:.3f} seconds",
            "result": result1,
        }
    )

    # Second call - should be a cache hit
    start = time.time()
    result2 = calculate_sum_of_squares(100)
    time2 = time.time() - start
    results.append(
        {
            "step": "Second call (cache hit)",
            "time": f"{time2:.3f} seconds",
            "result": result2,
            "speedup": f"{time1 / time2:.1f}x faster",
        }
    )

    # Call with different parameters - should be a cache miss
    start = time.time()
    result3 = calculate_sum_of_squares(200)
    time3 = time.time() - start
    results.append(
        {
            "step": "Different parameter (cache miss)",
            "time": f"{time3:.3f} seconds",
            "result": result3,
        }
    )

    # Final cache stats
    results.append({"step": "Final cache statistics", "stats": cache.get_stats()})

    return {
        "demo_results": results,
        "summary": "Demonstrates how repeated calls with the same parameters are served from cache",
    }


# Resources
@mcp.resource("cache://stats")
def get_cache_stats_resource() -> str:
    """Get cache statistics as a resource"""
    return json.dumps(get_cache_stats(), indent=2)


# Middleware to log cache activity
@mcp.middleware
async def cache_stats_middleware(message, next_handler):
    """Middleware to track cache usage"""
    # Process the message normally
    response = await next_handler(message)

    # Track cache stats for tool calls
    if (
        "method" in message
        and message.get("method") == "tools/call"
        and "result" in response
    ):
        tool_result = response["result"]
        if isinstance(tool_result, dict) and "cached" in tool_result:
            is_cached = tool_result.get("cached", False)
            timestamp = datetime.now().isoformat()
            tool_name = message.get("params", {}).get("name", "unknown")

            # Log cache hit/miss
            cache_status = "HIT" if is_cached else "MISS"
            sys.stderr.write(f"CACHE {cache_status} [{timestamp}]: {tool_name}\n")

    return response


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP WITH MEMORY CACHE INTEGRATION ===\n")
sys.stderr.write("This example demonstrates MCP with in-memory caching:\n")
sys.stderr.write(
    "1. Tool results are cached in memory based on tool name and parameters\n"
)
sys.stderr.write("2. Cached results dramatically speed up repeated calls\n")
sys.stderr.write("3. Cache statistics show hits, misses, and hit rate\n")
sys.stderr.write("4. Cache entries expire after their TTL (time-to-live)\n")
sys.stderr.write("5. Try the cache_demo tool to see the cache in action\n\n")
sys.stderr.write(
    "This example shows how to optimize MCP performance without external dependencies\n"
)
sys.stderr.write("=== END MEMORY CACHE INFO ===\n\n")

# Schedule periodic cache cleanup (every 60 seconds)
import threading


def periodic_cleanup():
    """Run cache cleanup periodically"""
    while True:
        time.sleep(60)
        removed = cache.cleanup()
        if removed > 0:
            sys.stderr.write(f"Cache cleanup: removed {removed} expired items\n")


# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

# This server demonstrates MCP with in-memory caching
# Run with: uv run mcp dev 56-memory-cache-integration.py
