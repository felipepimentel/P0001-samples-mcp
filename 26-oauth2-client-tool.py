import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OAuth2 Client Tool Example")

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com/user"


@mcp.tool()
def github_oauth2_login(client_id: str, client_secret: str, code: str) -> str:
    """Exchange OAuth2 code for access token and fetch user info from GitHub"""
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }
    resp = httpx.post(GITHUB_TOKEN_URL, data=data, headers=headers)
    if resp.status_code != 200:
        return f"Error fetching token: {resp.text}"
    token = resp.json().get("access_token")
    if not token:
        return "No access token received."
    user_resp = httpx.get(GITHUB_API_URL, headers={"Authorization": f"Bearer {token}"})
    if user_resp.status_code != 200:
        return f"Error fetching user info: {user_resp.text}"
    return user_resp.text
