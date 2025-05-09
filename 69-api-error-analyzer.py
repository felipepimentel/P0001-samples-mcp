import getpass
import os
import re

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Common error patterns and solutions
ERROR_PATTERNS = {
    "timeout": {
        "pattern": r"timeout|timed out|TimeoutError",
        "solutions": [
            "Increase timeout in client configuration",
            "Implement retry with exponential backoff",
            "Check network/API latency",
            "Consider caching to reduce calls",
        ],
        "code_fix": """
# Add timeout and retry
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

response = session.get(url, timeout=10)
""",
    },
    "auth": {
        "pattern": r"401|403|unauthorized|forbidden|authentication",
        "solutions": [
            "Verify API key/token validity",
            "Confirm correct Authorization header format",
            "Check account/API key permissions",
            "Renew token if expired",
        ],
        "code_fix": """
# Configure authentication correctly
headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

# Or for Basic Auth
import base64
credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
headers = {
    'Authorization': f'Basic {credentials}'
}
""",
    },
    "rate_limit": {
        "pattern": r"429|rate limit|too many requests",
        "solutions": [
            "Implement client-side rate limiting",
            "Use exponential backoff",
            "Distribute requests over time",
            "Consider API plan upgrade",
        ],
        "code_fix": '''
# Implement rate limiting
import time
from functools import wraps

def rate_limited(max_calls, period):
    """Decorator to limit API calls"""
    calls = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove old calls
            while calls and calls[0] < now - period:
                calls.pop(0)
            # Check if we're over the limit
            if len(calls) >= max_calls:
                sleep_time = calls[0] + period - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
            # Add this call
            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limited(100, 60)  # 100 calls per minute
def call_api(url):
    response = requests.get(url)
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return call_api(url)
    return response
''',
    },
}

mcp = FastMCP("API Error Analyzer")


@mcp.tool()
def analyze_error(error_message: str, context: str = "") -> str:
    """Analyze an API error message and suggest solutions.

    Args:
        error_message: The error message to analyze
        context: Additional context (logs, stack trace)

    Returns:
        Analysis with suggested solutions
    """
    full_text = f"{error_message} {context}".lower()

    # Identify error type
    detected_issues = []
    for error_type, info in ERROR_PATTERNS.items():
        if re.search(info["pattern"], full_text, re.IGNORECASE):
            detected_issues.append((error_type, info))

    if not detected_issues:
        return "⚠️ No known error pattern detected. Manual analysis required."

    # Generate report
    report = "# Error Analysis\n\n"

    for issue_type, info in detected_issues:
        report += f"## 🔍 Detected Issue: {issue_type.upper()}\n\n"
        report += "### Recommended Solutions:\n"
        for solution in info["solutions"]:
            report += f"- {solution}\n"

        report += f"\n### Fix Implementation:\n```python{info['code_fix']}```\n\n"

    report += """## 📋 Resolution Checklist:

1. [ ] Implement suggested fix
2. [ ] Test in isolated environment
3. [ ] Add logs for monitoring
4. [ ] Document the solution
5. [ ] Create automated test to prevent regression
"""

    return report
