import asyncio

import websockets
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WebSocket Tool Example")

WS_CLIENTS = set()


async def ws_handler(websocket, path):
    WS_CLIENTS.add(websocket)
    try:
        async for message in websocket:
            # Broadcast received message to all clients
            for ws in WS_CLIENTS:
                if ws != websocket:
                    await ws.send(f"Broadcast: {message}")
    finally:
        WS_CLIENTS.remove(websocket)


@mcp.tool()
def start_websocket_server(host: str = "localhost", port: int = 8765) -> str:
    """Start a WebSocket server for real-time messaging"""
    asyncio.get_event_loop().create_task(websockets.serve(ws_handler, host, port))
    return f"WebSocket server started at ws://{host}:{port}"


@mcp.tool()
def send_websocket_message(message: str) -> str:
    """Broadcast a message to all connected WebSocket clients"""
    for ws in list(WS_CLIENTS):
        asyncio.get_event_loop().create_task(ws.send(f"Server: {message}"))
    return f"Broadcasted: {message}"
