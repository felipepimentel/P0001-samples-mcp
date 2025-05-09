import getpass
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Sample API metrics and logs for demonstration
SAMPLE_API_METRICS = {
    "response_times": {
        "/v1/users": {
            "GET": {
                "p50": 45,  # milliseconds
                "p90": 120,
                "p99": 350,
                "samples": 3420,
            },
            "POST": {"p50": 120, "p90": 280, "p99": 540, "samples": 842},
        },
        "/v1/users/{id}": {
            "GET": {"p50": 35, "p90": 95, "p99": 210, "samples": 2876},
            "PUT": {"p50": 110, "p90": 245, "p99": 490, "samples": 516},
        },
        "/v1/products": {"GET": {"p50": 150, "p90": 320, "p99": 850, "samples": 6241}},
    },
    "error_rates": {
        "4xx": {
            "rate": 0.023,  # 2.3%
            "count": 320,
            "top_endpoints": [
                {
                    "path": "/v1/users",
                    "method": "POST",
                    "count": 126,
                    "most_common_code": 400,
                },
                {
                    "path": "/v1/products/{id}",
                    "method": "GET",
                    "count": 84,
                    "most_common_code": 404,
                },
            ],
        },
        "5xx": {
            "rate": 0.004,  # 0.4%
            "count": 56,
            "top_endpoints": [
                {
                    "path": "/v1/products",
                    "method": "GET",
                    "count": 35,
                    "most_common_code": 503,
                },
                {
                    "path": "/v1/orders",
                    "method": "POST",
                    "count": 21,
                    "most_common_code": 500,
                },
            ],
        },
    },
    "throughput": {
        "total_requests": 13924,
        "avg_rps": 16.2,
        "peak_rps": 42.8,
        "peak_time": "2023-05-10T14:35:00Z",
    },
}

# Sample alert configurations
ALERT_CONFIGURATIONS = [
    {
        "id": "high-error-rate",
        "name": "High Error Rate",
        "description": "Triggers when 5xx error rate exceeds threshold",
        "metric": "error_rate_5xx",
        "threshold": 0.01,  # 1%
        "duration": 300,  # 5 minutes
        "severity": "critical",
        "notification_channels": ["slack", "email"],
    },
    {
        "id": "high-latency",
        "name": "High Latency",
        "description": "Triggers when p90 latency exceeds threshold",
        "metric": "response_time_p90",
        "threshold": 500,  # ms
        "duration": 300,  # 5 minutes
        "severity": "warning",
        "notification_channels": ["slack"],
    },
    {
        "id": "low-throughput",
        "name": "Low Throughput",
        "description": "Triggers when RPS falls below threshold",
        "metric": "requests_per_second",
        "threshold": 5.0,
        "duration": 600,  # 10 minutes
        "severity": "warning",
        "notification_channels": ["slack", "email"],
    },
]

# Sample triggered alerts
TRIGGERED_ALERTS = [
    {
        "alert_id": "high-error-rate",
        "timestamp": "2023-05-10T14:32:00Z",
        "value": 0.023,
        "threshold": 0.01,
        "status": "firing",
        "duration": 420,  # seconds
        "affected_endpoints": ["/v1/products", "/v1/orders"],
    },
    {
        "alert_id": "high-latency",
        "timestamp": "2023-05-10T14:30:00Z",
        "value": 652,
        "threshold": 500,
        "status": "resolved",
        "duration": 780,  # seconds
        "affected_endpoints": ["/v1/products"],
    },
]

mcp = FastMCP("API Monitoring & Alerts")


@mcp.tool()
def get_api_performance_metrics(
    time_range: str = "24h",
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
) -> str:
    """Get API performance metrics.

    Args:
        time_range: Time range for metrics (1h, 6h, 24h, 7d)
        endpoint: Specific endpoint to filter (e.g., /v1/users)
        method: HTTP method to filter (GET, POST, PUT, DELETE)

    Returns:
        API performance metrics report
    """
    # In a real implementation, this would query a metrics database
    # For demo, we'll use the sample data

    # Apply filters if provided
    filtered_response_times = {}
    if endpoint:
        for path, methods in SAMPLE_API_METRICS["response_times"].items():
            if path == endpoint:
                filtered_response_times[path] = methods
    else:
        filtered_response_times = SAMPLE_API_METRICS["response_times"]

    if method:
        for path, methods in list(filtered_response_times.items()):
            filtered_methods = {}
            for m, metrics in methods.items():
                if m == method:
                    filtered_methods[m] = metrics
            filtered_response_times[path] = filtered_methods

    # Build the report
    report = "# API Performance Metrics\n\n"

    report += f"## Time Range: {time_range}\n\n"

    # Overall metrics
    report += "## Overall Metrics\n\n"
    report += (
        f"- **Total Requests**: {SAMPLE_API_METRICS['throughput']['total_requests']}\n"
    )
    report += f"- **Average RPS**: {SAMPLE_API_METRICS['throughput']['avg_rps']}\n"
    report += f"- **Peak RPS**: {SAMPLE_API_METRICS['throughput']['peak_rps']} at {SAMPLE_API_METRICS['throughput']['peak_time']}\n"
    report += f"- **4xx Error Rate**: {SAMPLE_API_METRICS['error_rates']['4xx']['rate'] * 100:.2f}%\n"
    report += f"- **5xx Error Rate**: {SAMPLE_API_METRICS['error_rates']['5xx']['rate'] * 100:.2f}%\n\n"

    # Response times by endpoint
    report += "## Response Times by Endpoint\n\n"

    for path, methods in filtered_response_times.items():
        report += f"### {path}\n\n"
        for method, metrics in methods.items():
            report += f"**{method}** ({metrics['samples']} requests):\n"
            report += f"- p50: {metrics['p50']} ms\n"
            report += f"- p90: {metrics['p90']} ms\n"
            report += f"- p99: {metrics['p99']} ms\n\n"

    # Top errors
    report += "## Top Errors\n\n"

    # 4xx errors
    report += "### 4xx Errors\n\n"
    for endpoint in SAMPLE_API_METRICS["error_rates"]["4xx"]["top_endpoints"]:
        report += f"- {endpoint['method']} {endpoint['path']}: {endpoint['count']} errors (most common: {endpoint['most_common_code']})\n"

    # 5xx errors
    report += "\n### 5xx Errors\n\n"
    for endpoint in SAMPLE_API_METRICS["error_rates"]["5xx"]["top_endpoints"]:
        report += f"- {endpoint['method']} {endpoint['path']}: {endpoint['count']} errors (most common: {endpoint['most_common_code']})\n"

    # Recommendations
    report += "\n## Recommendations\n\n"

    # Check for high error rates
    if SAMPLE_API_METRICS["error_rates"]["5xx"]["rate"] > 0.001:  # > 0.1%
        report += (
            "- 🔴 **High 5xx error rate detected**. Investigate server-side issues.\n"
        )

    # Check for high latency
    high_latency_endpoints = []
    for path, methods in filtered_response_times.items():
        for method, metrics in methods.items():
            if metrics["p90"] > 300:  # > 300ms
                high_latency_endpoints.append((path, method, metrics["p90"]))

    if high_latency_endpoints:
        report += "- 🟠 **High latency detected** for these endpoints:\n"
        for path, method, p90 in high_latency_endpoints:
            report += f"  - {method} {path}: p90 latency of {p90} ms\n"

    return report


@mcp.tool()
def get_active_alerts() -> str:
    """Get currently active monitoring alerts.

    Returns:
        Active monitoring alerts report
    """
    # Filter for active alerts
    active_alerts = [alert for alert in TRIGGERED_ALERTS if alert["status"] == "firing"]

    # Build the report
    report = "# Active API Monitoring Alerts\n\n"

    if not active_alerts:
        report += "✅ **All systems operational.** No active alerts.\n\n"
    else:
        report += f"🔴 **{len(active_alerts)} active alerts detected.**\n\n"

        for alert in active_alerts:
            # Get alert configuration
            alert_config = next(
                (
                    config
                    for config in ALERT_CONFIGURATIONS
                    if config["id"] == alert["alert_id"]
                ),
                {},
            )

            # Calculate time since alert firing
            alert_time = datetime.fromisoformat(
                alert["timestamp"].replace("Z", "+00:00")
            )
            now = datetime.now().astimezone()
            time_since = now - alert_time

            report += f"## {alert_config.get('name', alert['alert_id'])}\n\n"
            report += (
                f"**Severity**: {alert_config.get('severity', 'unknown').upper()}\n"
            )
            report += f"**Started**: {alert['timestamp']} ({format_timedelta(time_since)} ago)\n"
            report += f"**Metric**: {alert_config.get('metric', 'unknown')} = {alert['value']} (threshold: {alert['threshold']})\n"
            report += f"**Duration**: {format_seconds(alert['duration'])}\n"

            if "affected_endpoints" in alert and alert["affected_endpoints"]:
                report += "\n**Affected Endpoints**:\n"
                for endpoint in alert["affected_endpoints"]:
                    report += f"- {endpoint}\n"

            report += "\n"

    # Recent alerts (resolved)
    resolved_alerts = [
        alert for alert in TRIGGERED_ALERTS if alert["status"] == "resolved"
    ]
    if resolved_alerts:
        report += "## Recently Resolved Alerts\n\n"

        for alert in resolved_alerts:
            alert_config = next(
                (
                    config
                    for config in ALERT_CONFIGURATIONS
                    if config["id"] == alert["alert_id"]
                ),
                {},
            )
            alert_time = datetime.fromisoformat(
                alert["timestamp"].replace("Z", "+00:00")
            )
            now = datetime.now().astimezone()
            time_since = now - alert_time

            report += f"- **{alert_config.get('name', alert['alert_id'])}**: Resolved after {format_seconds(alert['duration'])} ({format_timedelta(time_since)} ago)\n"

    return report


@mcp.tool()
def configure_alert(
    name: str,
    metric: str,
    threshold: float,
    duration_seconds: int = 300,
    severity: str = "warning",
    notification_channels: List[str] = ["slack"],
) -> str:
    """Configure a new monitoring alert.

    Args:
        name: Alert name
        metric: Metric to monitor (error_rate_5xx, response_time_p90, etc.)
        threshold: Alert threshold value
        duration_seconds: Duration in seconds before alert fires
        severity: Alert severity (critical, warning, info)
        notification_channels: Notification channels to use

    Returns:
        Alert configuration details
    """
    # Generate a simple ID
    alert_id = name.lower().replace(" ", "-")

    # Create alert configuration (in real implementation, this would persist to storage)
    alert_config = {
        "id": alert_id,
        "name": name,
        "description": f"Alert for {metric} exceeding {threshold}",
        "metric": metric,
        "threshold": threshold,
        "duration": duration_seconds,
        "severity": severity,
        "notification_channels": notification_channels,
    }

    # In a real implementation, would save to a database here

    # Build response
    response = f"""# Alert Configuration Created

## {name}

- **ID**: {alert_id}
- **Metric**: {metric}
- **Threshold**: {threshold}
- **Duration**: {format_seconds(duration_seconds)}
- **Severity**: {severity}
- **Notifications**: {", ".join(notification_channels)}

## Example Alert Payload

```json
{{
  "alert_id": "{alert_id}",
  "name": "{name}",
  "metric": "{metric}",
  "threshold": {threshold},
  "value": {threshold * 1.2},
  "timestamp": "{datetime.now().isoformat()}Z",
  "status": "firing"
}}
```

## Next Steps

1. Test the alert by simulating a threshold breach
2. Verify notifications are received on configured channels
3. Add this alert to your monitoring dashboard
"""

    return response


@mcp.tool()
def generate_monitoring_dashboard_config(api_name: str) -> str:
    """Generate a monitoring dashboard configuration for an API.

    Args:
        api_name: Name of the API

    Returns:
        Monitoring dashboard configuration template
    """
    # This would typically generate a configuration for a monitoring system
    # like Grafana, Datadog, New Relic, etc.

    # For demo, we'll return a generic template
    dashboard_config = {
        "title": f"{api_name} API Monitoring",
        "description": f"Performance and reliability monitoring for {api_name}",
        "refresh_interval": "30s",
        "panels": [
            {
                "title": "Request Volume",
                "type": "graph",
                "data_source": "prometheus",
                "query": f'sum(rate(http_requests_total{{service="{api_name.lower()}"}}[5m])) by (path, method)',
                "unit": "requests/sec",
            },
            {
                "title": "Response Time",
                "type": "graph",
                "data_source": "prometheus",
                "query": f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{api_name.lower()}"}}[5m])) by (le, path, method))',
                "unit": "seconds",
            },
            {
                "title": "Error Rate",
                "type": "graph",
                "data_source": "prometheus",
                "query": f'sum(rate(http_requests_total{{service="{api_name.lower()}", status=~"5.."}}[5m])) by (path, method) / sum(rate(http_requests_total{{service="{api_name.lower()}"}}[5m])) by (path, method)',
                "unit": "percentage",
            },
            {
                "title": "Saturation",
                "type": "graph",
                "data_source": "prometheus",
                "query": f'process_cpu_seconds_total{{service="{api_name.lower()}"}}',
                "unit": "percentage",
            },
        ],
        "alerts": [
            {
                "name": "High Error Rate",
                "query": f'sum(rate(http_requests_total{{service="{api_name.lower()}", status=~"5.."}}[5m])) / sum(rate(http_requests_total{{service="{api_name.lower()}"}}[5m])) > 0.01',
                "description": "5xx error rate is above 1%",
                "severity": "critical",
            },
            {
                "name": "High Latency",
                "query": f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{api_name.lower()}"}}[5m])) by (le)) > 0.5',
                "description": "95th percentile latency is above 500ms",
                "severity": "warning",
            },
            {
                "name": "Low Throughput",
                "query": f'sum(rate(http_requests_total{{service="{api_name.lower()}"}}[5m])) < 5',
                "description": "Request rate is below 5 RPS",
                "severity": "warning",
            },
        ],
    }

    # Convert to formatted JSON
    dashboard_json = json.dumps(dashboard_config, indent=2)

    # Build response
    response = f"""# Monitoring Dashboard for {api_name}

## Dashboard Configuration

```json
{dashboard_json}
```

## Implementation Guide

1. Create a new dashboard in your monitoring system
2. Import the JSON configuration
3. Ensure your API is emitting metrics with the correct service name (`{api_name.lower()}`)
4. Customize panels and alerts as needed

## Key Metrics Included

- **Request Volume**: Tracks overall API usage and patterns
- **Response Time**: Monitors API performance (p95 latency)
- **Error Rate**: Tracks percentage of 5xx responses
- **Saturation**: Monitors resource usage to detect capacity issues

## Recommended Alerts

- **High Error Rate**: Triggers when 5xx errors exceed 1%
- **High Latency**: Triggers when p95 latency exceeds 500ms
- **Low Throughput**: Triggers when request rate falls below 5 RPS

## Integration Notes

This dashboard is compatible with Prometheus-based monitoring systems
including Grafana Cloud, Amazon Managed Grafana, and self-hosted Grafana.
"""

    return response


# Helper functions
def format_timedelta(delta: timedelta) -> str:
    """Format a timedelta in a human-readable way."""
    if delta.days > 0:
        return f"{delta.days}d {delta.seconds // 3600}h"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60}m"
    else:
        return f"{delta.seconds}s"


def format_seconds(seconds: int) -> str:
    """Format seconds in a human-readable way."""
    if seconds >= 86400:  # days
        return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"
    elif seconds >= 3600:  # hours
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
    elif seconds >= 60:  # minutes
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        return f"{seconds}s"
