#!/usr/bin/env python3
"""
76-mcp-devops-platform-demo.py - MCP DevOps Platform Demo

This script demonstrates how to interact with the MCP DevOps Platform
to perform common DevOps tasks through natural language.
"""

import time
from typing import Any, Dict

from mcp.client import MCPClient
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Initialize MCP client
mcp = MCPClient()
console = Console()

# Define demo prompt examples
DEMO_PROMPTS = [
    "Create a new recommendations API with rate limiting of 1000 requests per minute",
    "Deploy a new version of the payment service with zero downtime",
    "Investigate high latency in the user service over the last 30 minutes",
    "Run a chaos experiment to test resilience when the order service is unavailable",
    "Set up monitoring alerts for the payment service with SMS notifications",
    "Onboard me as a new developer to the platform team",
    "Show me the system resilience report for all services",
]


def connect_to_platform() -> bool:
    """Connect to the MCP DevOps Platform."""
    try:
        # Check if platform is running (try to connect to gateway)
        console.print("[bold blue]Connecting to MCP DevOps Platform...[/]")
        # In a real implementation, this would check if services are available
        time.sleep(1)
        return True
    except Exception as e:
        console.print(f"[bold red]Error connecting to platform: {e}[/]")
        console.print(
            "[yellow]Make sure the platform is running with './start-demo.sh'[/]"
        )
        return False


def show_available_tools() -> None:
    """Show available tools in the MCP DevOps Platform."""
    console.print("\n[bold cyan]Available DevOps Tools:[/]")

    tools = [
        {
            "name": "API Governance",
            "description": "Create and manage APIs with built-in best practices",
            "examples": ["Create a new users API", "Check API contract compliance"],
        },
        {
            "name": "Infrastructure Management",
            "description": "Deploy, scale, and monitor infrastructure",
            "examples": [
                "Scale the payment service to 5 replicas",
                "Deploy v2 of order service",
            ],
        },
        {
            "name": "Chaos Engineering",
            "description": "Test system resilience with controlled experiments",
            "examples": [
                "Test network latency resilience",
                "Run CPU pressure test on user service",
            ],
        },
        {
            "name": "Problem Investigation",
            "description": "Diagnose and fix issues with AI assistance",
            "examples": ["Investigate high error rate", "Debug slow database queries"],
        },
        {
            "name": "Developer Onboarding",
            "description": "Personalized setup for new team members",
            "examples": [
                "Onboard me to the platform team",
                "Set up local development environment",
            ],
        },
    ]

    for tool in tools:
        console.print(f"[bold green]{tool['name']}[/]")
        console.print(f"  {tool['description']}")
        console.print("  [italic]Examples:[/]")
        for example in tool["examples"]:
            console.print(f"    • {example}")
        console.print()


def process_devops_request(request: str) -> Dict[str, Any]:
    """Process a DevOps request using the MCP platform.

    In a real implementation, this would call the MCP server.
    For this demo, we simulate the response.
    """
    console.print(f"\n[bold cyan]Processing request:[/] {request}")
    console.print("[bold yellow]Sending to MCP DevOps Platform...[/]")

    # Simulate processing
    for i in range(5):
        console.print(f"[dim]Processing step {i + 1}/5...[/]")
        time.sleep(0.5)

    # Simulate response based on request type
    if "create" in request.lower() and "api" in request.lower():
        return {
            "success": True,
            "tool": "create_api",
            "result": """# 🚀 API Created Successfully!

## API: recommendations
**Type**: REST

### Creation Summary:
✅ Generated OpenAPI specification
✅ Configured in Kong Gateway
✅ Set up authentication
✅ Applied rate limiting
✅ Created Grafana dashboard
✅ Configured Jaeger tracing
✅ Made initial deployment

### Access Points:
- **Gateway URL**: http://localhost:8000/api/recommendations
- **Swagger UI**: http://localhost:8082/recommendations
- **Grafana Dashboard**: http://localhost:3000/d/recommendations

The API is ready for use and being monitored! 🎉
""",
        }
    elif "investigate" in request.lower() or "latency" in request.lower():
        return {
            "success": True,
            "tool": "investigate_problem",
            "result": """# 🔍 Investigation Report

## Problem: High latency in the user service

### Root Cause Analysis:
**Database connection pool exhaustion causing request queuing**

### Detected Impact:
- 🔴 Affected Services: user-service
- 📊 Error Rate: +5%
- ⏱️ Latency Impact: +300ms p99
- 👥 Affected Users: ~40%

### Recommended Solution:
1. Increase database connection pool size
2. Add connection timeout handling
3. Implement retry logic with exponential backoff
4. Add Redis caching layer for frequent queries

The fix has been applied and service is recovering.
""",
        }
    elif "chaos" in request.lower() or "resilience" in request.lower():
        return {
            "success": True,
            "tool": "run_chaos_experiment",
            "result": """# 🌪️ Chaos Engineering Experiment Report

## Experiment: Failure on order-service
**Duration**: 5m
**Intensity**: Medium

### Hypothesis:
"The system remains available when order-service experiences medium failure rate"

### Result:
**Hypothesis**: ✅ CONFIRMED
The system maintained acceptable performance within defined thresholds.

### Findings:
- Circuit breakers activated after 15% failures
- Retry mechanisms recovered 85% of failed requests
- User experience degraded by 25% during peak failure

### Resilience Score:
82 / 100

The system demonstrated strong resilience to failure! 🏆
""",
        }
    else:
        return {
            "success": True,
            "tool": "generic_devops",
            "result": f"""# ✅ Request Completed

Successfully processed: "{request}"

Check the dashboard at http://localhost:3001 for real-time updates.
""",
        }


def interactive_demo() -> None:
    """Run an interactive demo of the MCP DevOps Platform."""
    console.print(
        "\n[bold magenta]===== MCP DevOps Platform Interactive Demo =====\n[/]"
    )

    if not connect_to_platform():
        return

    show_available_tools()

    console.print("[bold blue]Example prompts:[/]")
    for i, prompt in enumerate(DEMO_PROMPTS, 1):
        console.print(f"  {i}. {prompt}")

    while True:
        console.print(
            "\n[bold green]Enter a DevOps request (or 'q' to quit, 'examples' to show examples):[/]"
        )
        user_input = input("> ").strip()

        if user_input.lower() in ("q", "quit", "exit"):
            break

        if user_input.lower() == "examples":
            console.print("[bold blue]Example prompts:[/]")
            for i, prompt in enumerate(DEMO_PROMPTS, 1):
                console.print(f"  {i}. {prompt}")
            continue

        try:
            # Try to handle numeric selection of examples
            if user_input.isdigit() and 1 <= int(user_input) <= len(DEMO_PROMPTS):
                user_input = DEMO_PROMPTS[int(user_input) - 1]
                console.print(f"[dim]Selected: {user_input}[/]")

            # Process the request
            response = process_devops_request(user_input)

            if response["success"]:
                # Display the markdown result
                md = Markdown(response["result"])
                console.print(
                    Panel(
                        md,
                        title=f"[bold green]{response['tool']}[/]",
                        border_style="green",
                        expand=False,
                    )
                )
            else:
                console.print(
                    f"[bold red]Error: {response.get('error', 'Unknown error')}[/]"
                )

        except Exception as e:
            console.print(f"[bold red]Error processing request: {str(e)}[/]")


def main() -> None:
    """Main function to run the demo."""
    try:
        interactive_demo()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Demo interrupted by user. Exiting...[/]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/]")
    finally:
        console.print(
            "\n[bold blue]Thank you for trying the MCP DevOps Platform Demo![/]"
        )
        console.print(
            "[italic]For more information, check out the README.md in the mcp-platform-demo directory.[/]"
        )


if __name__ == "__main__":
    main()
