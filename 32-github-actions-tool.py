import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GitHub Actions Tool Example")

GITHUB_API = "https://api.github.com"


@mcp.tool()
def trigger_github_workflow(
    owner: str, repo: str, workflow_id: str, ref: str, token: str
) -> str:
    """Trigger a GitHub Actions workflow_dispatch event"""
    url = (
        f"{GITHUB_API}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"ref": ref}
    resp = httpx.post(url, json=data, headers=headers)
    if resp.status_code not in (201, 204):
        return f"Error: {resp.text}"
    return f"Workflow {workflow_id} triggered on {ref}"
