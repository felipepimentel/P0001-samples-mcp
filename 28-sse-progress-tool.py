import asyncio

from mcp.server.fastmcp import FastMCP
from sse_starlette.sse import EventSourceResponse

mcp = FastMCP("SSE Progress Tool Example")


@mcp.resource("sse://progress/{steps}")
async def sse_progress(steps: int = 10) -> EventSourceResponse:
    """Send incremental progress updates via SSE"""

    async def event_generator():
        for i in range(steps):
            await asyncio.sleep(0.5)
            yield {"data": f"Progress: {i + 1}/{steps}"}
        yield {"data": "Done!"}

    return EventSourceResponse(event_generator())
