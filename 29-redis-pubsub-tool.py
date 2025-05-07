import redis.asyncio as redis
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Redis PubSub Tool Example")

REDIS_URL = "redis://localhost:6379"
CHANNEL = "mcp_channel"


@mcp.tool()
async def redis_publish(message: str) -> str:
    """Publish a message to the Redis channel"""
    r = redis.from_url(REDIS_URL)
    await r.publish(CHANNEL, message)
    await r.close()
    return f"Published: {message}"


@mcp.resource("redis://subscribe")
async def redis_subscribe() -> str:
    """Subscribe to the Redis channel and return the first message received"""
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    async for msg in pubsub.listen():
        if msg["type"] == "message":
            await pubsub.unsubscribe(CHANNEL)
            await pubsub.close()
            await r.close()
            return f"Received: {msg['data'].decode()}"
