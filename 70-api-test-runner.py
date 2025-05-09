import getpass
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Template for API test script
API_TEST_SCRIPT = """
import requests
import json
import sys
import time

def test_api(url, method="GET", headers=None, params=None, data=None, timeout=10):
    start_time = time.time()
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            params=params or {},
            json=data,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        result = {
            "status": response.status_code,
            "elapsed_ms": int(elapsed * 1000),
            "headers": dict(response.headers),
            "content_type": response.headers.get("Content-Type", "unknown"),
            "size_bytes": len(response.content),
            "body": None
        }
        
        # Try to parse JSON response
        try:
            if response.content:
                result["body"] = response.json()
        except ValueError:
            # Not JSON, include first 1000 chars of text response
            if response.content:
                result["body"] = response.text[:1000]
                if len(response.text) > 1000:
                    result["body"] += "... (truncated)"
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        elapsed = time.time() - start_time
        error = {
            "error": str(e),
            "type": type(e).__name__,
            "elapsed_ms": int(elapsed * 1000)
        }
        print(json.dumps(error, indent=2))
        sys.exit(1)

# Test parameters
test_api(
    url="{url}",
    method="{method}",
    headers={headers},
    params={params},
    data={data},
    timeout={timeout}
)
"""

mcp = FastMCP("API Test Runner")


@mcp.tool()
def test_api(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
) -> str:
    """Test an API endpoint in an isolated environment.

    Args:
        url: The complete URL to test
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: HTTP headers to include
        params: Query parameters
        data: JSON body data
        timeout: Request timeout in seconds

    Returns:
        API test results report
    """
    headers = headers or {}
    params = params or {}

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        script = API_TEST_SCRIPT.format(
            url=url,
            method=method,
            headers=json.dumps(headers),
            params=json.dumps(params),
            data=json.dumps(data) if data else "None",
            timeout=timeout,
        )
        f.write(script)
        script_path = f.name

    try:
        # Run the test script using Python directly (not Docker to keep it simple)
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=timeout + 5,  # Add buffer for script execution
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                status_class = output.get("status", 0) // 100
                status_emoji = {2: "✅", 3: "↩️", 4: "❌", 5: "💥"}.get(
                    status_class, "❓"
                )

                report = f"""# API Test: {method} {url}

{status_emoji} **Status**: {output.get("status", "N/A")}
⏱️ **Response Time**: {output.get("elapsed_ms", "N/A")}ms
📦 **Size**: {output.get("size_bytes", "N/A")} bytes
🔤 **Content Type**: {output.get("content_type", "N/A")}

## Response Headers:
```json
{json.dumps(output.get("headers", {}), indent=2)}
```

## Response Body:
```
{json.dumps(output.get("body", "No content"), indent=2)}
```

## Analysis:
"""

                # Add analysis based on status code
                if status_class == 2:
                    report += "- Request successful\n"
                    if output.get("elapsed_ms", 0) > 1000:
                        report += "- Response time is high (> 1000ms)\n"
                elif status_class == 4:
                    report += "- Client error (check your request parameters)\n"
                    if output.get("status") == 401:
                        report += "- Authentication failed (check your credentials)\n"
                    elif output.get("status") == 403:
                        report += "- Authorization failed (check your permissions)\n"
                    elif output.get("status") == 404:
                        report += "- Resource not found (check your URL)\n"
                    elif output.get("status") == 429:
                        report += "- Rate limit exceeded (slow down your requests)\n"
                elif status_class == 5:
                    report += "- Server error (try again later)\n"

                return report
            except json.JSONDecodeError:
                return f"❌ Error parsing response:\n```\n{result.stdout}\n```"
        else:
            return f"❌ Test failed:\n```\n{result.stderr}\n```"

    except subprocess.TimeoutExpired:
        return f"❌ Timeout: Test took longer than {timeout + 5} seconds"
    except Exception as e:
        return f"❌ Error running test: {str(e)}"
    finally:
        # Clean up temp file
        try:
            os.unlink(script_path)
        except:
            pass
