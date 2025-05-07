import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Slack/Discord Bot Tool Example")


@mcp.tool()
def send_slack_message(webhook_url: str, text: str) -> str:
    """Send a message to Slack via webhook"""
    resp = httpx.post(webhook_url, json={"text": text})
    if resp.status_code != 200:
        return f"Error: {resp.text}"
    return "Message sent to Slack."


@mcp.tool()
def send_discord_message(webhook_url: str, content: str) -> str:
    """Send a message to Discord via webhook"""
    resp = httpx.post(webhook_url, json={"content": content})
    if resp.status_code != 204:
        return f"Error: {resp.text}"
    return "Message sent to Discord."
