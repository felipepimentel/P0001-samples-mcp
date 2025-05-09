import getpass
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

os.getlogin = getpass.getuser
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Chaos Engineer")

# Available experiment types
EXPERIMENT_TYPES = {
    "latency": {
        "description": "Inject network latency between services",
        "parameters": ["target", "duration", "latency_ms"],
    },
    "failure": {
        "description": "Simulate service crashes or unavailability",
        "parameters": ["target", "duration", "failure_percentage"],
    },
    "cpu": {
        "description": "Consume CPU resources on target services",
        "parameters": ["target", "duration", "cpu_load"],
    },
    "memory": {
        "description": "Consume memory resources on target services",
        "parameters": ["target", "duration", "memory_mb"],
    },
    "network": {
        "description": "Simulate network issues like packet loss",
        "parameters": ["target", "duration", "packet_loss_percentage"],
    },
}

# Track running experiments
active_experiments = {}


@mcp.tool()
def run_chaos_experiment(
    experiment_type: str, target: str, duration: str = "5m", intensity: str = "medium"
) -> str:
    """Run a chaos engineering experiment on the platform.

    Args:
        experiment_type: Type of experiment (latency, failure, cpu, memory, network)
        target: Target service or component
        duration: Duration of experiment (e.g., 5m, 30s, 1h)
        intensity: Experiment intensity (low, medium, high)

    Returns:
        Detailed experiment report
    """
    # Validate experiment type
    if experiment_type not in EXPERIMENT_TYPES:
        return f"❌ Invalid experiment type: {experiment_type}. Available types: {', '.join(EXPERIMENT_TYPES.keys())}"

    # Convert duration to seconds
    duration_seconds = parse_duration(duration)

    # Convert intensity to actual values
    intensity_values = get_intensity_values(experiment_type, intensity)

    # Generate a hypothesis
    hypothesis = generate_hypothesis(experiment_type, target, intensity)

    # Check baseline (stable state)
    baseline = check_stable_state(target)

    # Create experiment ID
    experiment_id = f"chaos_{int(time.time())}"

    # Start experiment
    experiment = {
        "id": experiment_id,
        "type": experiment_type,
        "target": target,
        "duration": duration,
        "duration_seconds": duration_seconds,
        "intensity": intensity,
        "intensity_values": intensity_values,
        "hypothesis": hypothesis,
        "baseline": baseline,
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "metrics": [],
        "events": [],
    }

    # Record experiment start
    active_experiments[experiment_id] = experiment

    # Apply chaos (in a real implementation, this would interact with chaos tools)
    inject_chaos(experiment)

    # In a real implementation, we'd set up a background task to monitor and stop the experiment
    # For this demo, we'll simulate the experiment completion

    # Simulate experiment results
    experiment["metrics"] = generate_experiment_metrics(experiment)
    experiment["events"] = generate_experiment_events(experiment)

    # Complete experiment
    experiment["status"] = "completed"
    experiment["end_time"] = datetime.now().isoformat()

    # Analyze results
    analysis = analyze_experiment_results(experiment)

    # Generate experiment report
    return f"""# 🌪️ Chaos Engineering Experiment Report

## Experiment: {experiment_type.title()} on {target}
**ID**: {experiment_id}
**Duration**: {duration}
**Intensity**: {intensity.title()}

### Hypothesis:
"{hypothesis["statement"]}"

### Steady State (Baseline):
- Error Rate: {baseline["error_rate"]}%
- P99 Latency: {baseline["p99_latency"]}ms
- Throughput: {baseline["throughput"]} req/s

### Experiment Configuration:
```yaml
chaos_experiment:
  name: {experiment_id}
  target: {target}
  type: {experiment_type}
  parameters:
    {get_experiment_parameters_yaml(experiment)}
  steady_state:
    error_rate_threshold: {hypothesis["thresholds"]["error_rate"]}%
    latency_threshold: {hypothesis["thresholds"]["latency"]}ms
```

### Timeline of Execution:
{generate_timeline(experiment)}

### Observed Impact:
- Error Rate: {baseline["error_rate"]}% → {max([m["error_rate"] for m in experiment["metrics"]])}%
- P99 Latency: {baseline["p99_latency"]}ms → {max([m["p99_latency"] for m in experiment["metrics"]])}ms
- Throughput Degradation: {calculate_throughput_degradation(experiment)}%

### System Behavior:
{analysis["behavior_analysis"]}

### Result:
**Hypothesis**: {analysis["status"]}
{analysis["explanation"]}

### Findings:
{chr(10).join([f"- {d}" for d in analysis["findings"]])}

### Identified Improvements:
{chr(10).join([f"- {m}" for m in analysis["improvements"]])}

### Visualizations:
- [Experiment Dashboard](http://localhost:3000/d/chaos-{experiment_id})
- [Before/After Comparison](http://localhost:3000/d/chaos-comparison)
- [Resilience Analysis](http://localhost:3000/d/resilience-score)

### Suggested Follow-up Experiments:
{chr(10).join([f"- {e}" for e in analysis["next_experiments"]])}

### Resilience Score:
{analysis["resilience_score"]} / 100

The system demonstrated {analysis["resilience_level"]} resilience to {experiment_type}! 🏆
"""


@mcp.tool()
def list_experiment_types() -> str:
    """List all available chaos experiment types.

    Returns:
        List of available experiment types with descriptions
    """
    result = "# Available Chaos Experiment Types\n\n"

    for exp_type, details in EXPERIMENT_TYPES.items():
        result += f"## {exp_type.title()}\n\n"
        result += f"{details['description']}\n\n"
        result += "**Parameters:**\n"
        for param in details["parameters"]:
            result += f"- `{param}`\n"
        result += "\n"

    return result


@mcp.tool()
def get_active_experiments() -> str:
    """Get all currently running chaos experiments.

    Returns:
        List of active experiments with details
    """
    if not active_experiments:
        return "No active chaos experiments running."

    result = "# Active Chaos Experiments\n\n"

    for exp_id, exp in active_experiments.items():
        result += f"## {exp['type'].title()} on {exp['target']}\n\n"
        result += f"**ID**: {exp_id}\n"
        result += f"**Started**: {exp['start_time']}\n"
        result += f"**Duration**: {exp['duration']}\n"
        result += f"**Intensity**: {exp['intensity']}\n\n"

    return result


@mcp.tool()
def get_system_resilience_report() -> str:
    """Generate a comprehensive resilience report for the system.

    Returns:
        System resilience report with scores and recommendations
    """
    # In a real implementation, this would analyze past experiments
    # and system metrics to generate a meaningful report

    services = ["user-service", "payment-service", "order-service"]
    experiment_types = ["latency", "failure", "cpu", "memory", "network"]

    result = "# System Resilience Report\n\n"

    result += "## Overall Resilience Score\n\n"
    overall_score = random.randint(65, 85)
    result += f"**Score**: {overall_score}/100\n\n"

    result += "## Service Resilience Scores\n\n"
    for service in services:
        score = random.randint(50, 95)
        result += f"- **{service}**: {score}/100\n"

    result += "\n## Resilience by Failure Type\n\n"
    for exp_type in experiment_types:
        score = random.randint(50, 95)
        result += f"- **{exp_type.title()}**: {score}/100\n"

    result += "\n## Top Weaknesses\n\n"
    weaknesses = [
        "Network dependency between payment-service and order-service",
        "No circuit breaker for database connections",
        "Insufficient memory limits on user-service pods",
        "Missing retry logic in critical API calls",
        "No fallback mechanisms for recommendation service",
    ]
    for weakness in random.sample(weaknesses, 3):
        result += f"- {weakness}\n"

    result += "\n## Recommended Improvements\n\n"
    improvements = [
        "Implement circuit breakers for all database connections",
        "Add retry logic with exponential backoff for critical API calls",
        "Increase memory limits and implement graceful degradation",
        "Create fallback responses for non-critical services",
        "Implement bulkheads to isolate failure domains",
        "Add health checks and readiness probes to all services",
    ]
    for improvement in random.sample(improvements, 4):
        result += f"- {improvement}\n"

    result += "\n## Recent Learnings\n\n"
    learnings = [
        "The payment system can handle 30% of service failures with minimal impact",
        "Redis caching significantly improves resilience to database latency",
        "User-service requires better memory management under load",
        "Network partitioning between services causes cascading failures",
        "API rate limiting helps prevent system overload during traffic spikes",
    ]
    for learning in random.sample(learnings, 3):
        result += f"- {learning}\n"

    return result


# Helper functions
def parse_duration(duration_str: str) -> int:
    """Parse duration string to seconds."""
    unit = duration_str[-1]
    value = int(duration_str[:-1])

    if unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    else:
        return value  # Assume seconds if no unit


def get_intensity_values(experiment_type: str, intensity: str) -> Dict[str, Any]:
    """Convert intensity string to actual parameter values."""
    intensity_map = {
        "latency": {
            "low": {"latency_ms": 100},
            "medium": {"latency_ms": 250},
            "high": {"latency_ms": 500},
        },
        "failure": {
            "low": {"failure_percentage": 10},
            "medium": {"failure_percentage": 30},
            "high": {"failure_percentage": 50},
        },
        "cpu": {
            "low": {"cpu_load": 30},
            "medium": {"cpu_load": 60},
            "high": {"cpu_load": 85},
        },
        "memory": {
            "low": {"memory_mb": 256},
            "medium": {"memory_mb": 512},
            "high": {"memory_mb": 1024},
        },
        "network": {
            "low": {"packet_loss_percentage": 5},
            "medium": {"packet_loss_percentage": 15},
            "high": {"packet_loss_percentage": 30},
        },
    }

    return intensity_map[experiment_type][intensity]


def generate_hypothesis(
    experiment_type: str, target: str, intensity: str
) -> Dict[str, Any]:
    """Generate a hypothesis for the experiment."""
    statements = {
        "latency": f"The {target} can maintain acceptable performance with {intensity} network latency",
        "failure": f"The system remains available when {target} experiences {intensity} failure rate",
        "cpu": f"The {target} can maintain service quality under {intensity} CPU pressure",
        "memory": f"The {target} handles {intensity} memory constraints without data loss",
        "network": f"The system tolerates {intensity} network packet loss between services",
    }

    # Define thresholds based on intensity
    thresholds = {
        "low": {"error_rate": 1, "latency": 200},
        "medium": {"error_rate": 5, "latency": 500},
        "high": {"error_rate": 10, "latency": 1000},
    }

    return {
        "statement": statements[experiment_type],
        "thresholds": thresholds[intensity],
    }


def check_stable_state(target: str) -> Dict[str, Any]:
    """Check the stable state of the target before experiments."""
    # In a real implementation, this would get actual metrics
    return {
        "error_rate": round(random.uniform(0.1, 0.5), 2),
        "p99_latency": random.randint(50, 150),
        "throughput": random.randint(100, 300),
        "cpu_usage": random.randint(20, 40),
        "memory_usage": random.randint(30, 50),
    }


def inject_chaos(experiment: Dict[str, Any]) -> None:
    """Inject chaos based on experiment configuration."""
    # In a real implementation, this would use chaos tools
    # like Chaos Mesh, Litmus Chaos, or custom scripts
    pass


def generate_experiment_metrics(experiment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate simulated metrics for the experiment."""
    baseline = experiment["baseline"]
    intensity = experiment["intensity"]
    metrics = []

    # Generate metrics at different time points
    for i in range(5):
        # Simulate increasing impact over time
        impact_factor = (i + 1) / 5

        # Adjust metrics based on experiment type and intensity
        if experiment["type"] == "latency":
            error_rate = baseline["error_rate"] * (1 + impact_factor)
            p99_latency = baseline["p99_latency"] + (
                experiment["intensity_values"]["latency_ms"] * impact_factor
            )
            throughput = baseline["throughput"] * (1 - 0.2 * impact_factor)
        elif experiment["type"] == "failure":
            error_rate = baseline["error_rate"] + (
                experiment["intensity_values"]["failure_percentage"] * impact_factor / 2
            )
            p99_latency = baseline["p99_latency"] * (1 + 0.5 * impact_factor)
            throughput = baseline["throughput"] * (1 - 0.3 * impact_factor)
        else:
            error_rate = baseline["error_rate"] * (1 + 2 * impact_factor)
            p99_latency = baseline["p99_latency"] * (1 + impact_factor)
            throughput = baseline["throughput"] * (1 - 0.4 * impact_factor)

        metrics.append(
            {
                "timestamp": (
                    datetime.fromisoformat(experiment["start_time"])
                    + timedelta(seconds=i * experiment["duration_seconds"] / 5)
                ).isoformat(),
                "error_rate": round(error_rate, 2),
                "p99_latency": round(p99_latency, 2),
                "throughput": round(throughput, 2),
            }
        )

    return metrics


def generate_experiment_events(experiment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate simulated events during the experiment."""
    events = [
        {
            "timestamp": experiment["start_time"],
            "type": "experiment_start",
            "description": f"Started {experiment['type']} experiment on {experiment['target']}",
        }
    ]

    # Add some random events based on experiment type
    if experiment["type"] == "latency":
        events.append(
            {
                "timestamp": (
                    datetime.fromisoformat(experiment["start_time"])
                    + timedelta(seconds=experiment["duration_seconds"] * 0.3)
                ).isoformat(),
                "type": "threshold_exceeded",
                "description": f"Latency threshold exceeded: {int(experiment['intensity_values']['latency_ms'] * 1.2)}ms",
            }
        )
    elif experiment["type"] == "failure":
        events.append(
            {
                "timestamp": (
                    datetime.fromisoformat(experiment["start_time"])
                    + timedelta(seconds=experiment["duration_seconds"] * 0.2)
                ).isoformat(),
                "type": "service_impact",
                "description": f"Circuit breaker opened for {experiment['target']}",
            }
        )

    # Add experiment end event
    events.append(
        {
            "timestamp": (
                datetime.fromisoformat(experiment["start_time"])
                + timedelta(seconds=experiment["duration_seconds"])
            ).isoformat(),
            "type": "experiment_end",
            "description": f"Completed {experiment['type']} experiment on {experiment['target']}",
        }
    )

    return events


def analyze_experiment_results(experiment: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the results of the experiment."""
    baseline = experiment["baseline"]
    metrics = experiment["metrics"]

    # Calculate maximum impact
    max_error_rate = max([m["error_rate"] for m in metrics])
    max_latency = max([m["p99_latency"] for m in metrics])
    min_throughput = min([m["throughput"] for m in metrics])

    # Determine if hypothesis was validated
    hypothesis_thresholds = experiment["hypothesis"]["thresholds"]
    hypothesis_validated = (
        max_error_rate <= hypothesis_thresholds["error_rate"]
        and max_latency <= baseline["p99_latency"] + hypothesis_thresholds["latency"]
    )

    # Generate analysis based on results
    if hypothesis_validated:
        status = "✅ CONFIRMED"
        explanation = (
            "The system maintained acceptable performance within defined thresholds."
        )
        resilience_score = random.randint(75, 95)
        resilience_level = "strong"
    else:
        status = "❌ REJECTED"
        explanation = (
            "The system exceeded performance thresholds during the experiment."
        )
        resilience_score = random.randint(40, 70)
        resilience_level = "moderate"

    # Generate findings
    if experiment["type"] == "latency":
        findings = [
            f"System maintained {min_throughput / baseline['throughput'] * 100:.1f}% throughput during peak latency",
            f"Error rate increased by {(max_error_rate - baseline['error_rate']):.2f}% during the experiment",
            f"Response time degradation was {(max_latency - baseline['p99_latency']):.1f}ms at peak",
        ]
    elif experiment["type"] == "failure":
        findings = [
            f"Circuit breakers activated after {experiment['intensity_values']['failure_percentage'] / 2}% failures",
            f"Retry mechanisms recovered {random.randint(70, 95)}% of failed requests",
            f"User experience degraded by {random.randint(10, 40)}% during peak failure",
        ]
    else:
        findings = [
            f"System adaptation observed after {random.randint(30, 90)} seconds",
            "Resource limits prevented cascading failures",
            f"Recovery time was {random.randint(5, 30)} seconds after experiment",
        ]

    # Suggest improvements
    improvements = [
        f"Increase timeout for {experiment['target']} from 3s to 5s",
        "Add circuit breaker to prevent cascading failures",
        "Implement retry with exponential backoff for critical calls",
        "Add monitoring alerts for early detection",
        "Create fallback responses for degraded service",
        "Document recovery procedures for operations team",
    ]

    # Suggest next experiments
    next_experiments = []
    for exp_type in EXPERIMENT_TYPES:
        if exp_type != experiment["type"]:
            next_experiments.append(
                f"{exp_type.title()} test on {experiment['target']}"
            )

    next_experiments.append(f"Combined {experiment['type']} and failure test")
    next_experiments = random.sample(next_experiments, min(3, len(next_experiments)))

    # Return comprehensive analysis
    return {
        "status": status,
        "explanation": explanation,
        "findings": findings,
        "improvements": random.sample(improvements, 4),
        "next_experiments": next_experiments,
        "resilience_score": resilience_score,
        "resilience_level": resilience_level,
        "behavior_analysis": generate_behavior_analysis(
            experiment, max_error_rate, max_latency, min_throughput
        ),
    }


def get_experiment_parameters_yaml(experiment: Dict[str, Any]) -> str:
    """Format experiment parameters as YAML string."""
    params = []
    for key, value in experiment["intensity_values"].items():
        params.append(f"{key}: {value}")

    return "\n    ".join(params)


def generate_timeline(experiment: Dict[str, Any]) -> str:
    """Generate experiment timeline as formatted string."""
    timeline = []
    timeline.append("1. ✅ Steady state verified")
    timeline.append(
        f"2. 💉 Chaos injected: {experiment['type']} on {experiment['target']}"
    )
    timeline.append(f"3. 📊 Monitoring for {experiment['duration']}")
    timeline.append("4. 🔄 Chaos removed")
    timeline.append("5. ✅ Recovery verified")

    return "\n".join(timeline)


def calculate_throughput_degradation(experiment: Dict[str, Any]) -> float:
    """Calculate throughput degradation percentage."""
    baseline = experiment["baseline"]["throughput"]
    min_throughput = min([m["throughput"] for m in experiment["metrics"]])

    return round(((baseline - min_throughput) / baseline) * 100, 1)


def generate_behavior_analysis(
    experiment: Dict[str, Any],
    max_error_rate: float,
    max_latency: float,
    min_throughput: float,
) -> str:
    """Generate detailed behavior analysis."""
    exp_type = experiment["type"]
    target = experiment["target"]

    if exp_type == "latency":
        return f"""The system demonstrated {random.choice(["good", "moderate", "excellent"])} latency tolerance. 
        
When network latency increased to {experiment["intensity_values"]["latency_ms"]}ms, the system:
- Maintained request processing with increased response times
- Correctly applied timeouts to prevent resource exhaustion
- Continued to serve critical requests with {random.randint(80, 99)}% success rate
- Showed signs of queuing at {random.randint(70, 90)}% of max latency"""

    elif exp_type == "failure":
        return f"""The system demonstrated {random.choice(["resilient", "moderate", "robust"])} failure handling.

During {experiment["intensity_values"]["failure_percentage"]}% of failures in {target}, the system:
- Activated circuit breakers to prevent cascading failures
- Properly degraded non-critical functionality
- Maintained core business functions throughout the experiment
- Recovery mechanisms restored full functionality within {random.randint(10, 30)} seconds after chaos removal"""

    else:
        return f"""The system showed {random.choice(["acceptable", "good", "strong"])} resource pressure handling.

Under {exp_type} pressure on {target}, the system:
- Properly prioritized critical requests
- Gracefully degraded performance as resources became constrained
- Maintained data consistency throughout the experiment
- Showed {random.choice(["quick", "gradual", "immediate"])} recovery when pressure was removed"""


if __name__ == "__main__":
    # This will be executed when the server is run directly
    import os

    os.environ["MCP_INSPECTOR_URL"] = "http://127.0.0.1:6274"
    mcp.serve_stdio()
