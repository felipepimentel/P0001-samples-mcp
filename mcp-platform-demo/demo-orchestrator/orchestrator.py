#!/usr/bin/env python3
"""
Demo Orchestrator

This script orchestrates demo scenarios for the MCP DevOps Platform,
generating realistic traffic patterns, simulating issues, and creating
a dynamic environment for the demo.
"""

import argparse
import asyncio
import datetime
import json
import logging
import os
import random
import signal
import sys
import time
from typing import Any, Dict

import docker
import redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("demo-orchestrator")

# Initialize Docker client
docker_client = docker.from_env()

# Initialize Redis client
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)

# Prometheus metrics
REQUESTS_TOTAL = Counter(
    "demo_requests_total",
    "Total number of requests",
    ["service", "endpoint", "method", "status"],
)
LATENCY = Histogram(
    "demo_request_latency_seconds",
    "Request latency in seconds",
    ["service", "endpoint"],
)
ERROR_RATE = Gauge("demo_error_rate", "Current error rate percentage", ["service"])
MEMORY_USAGE = Gauge("demo_memory_usage_mb", "Memory usage in MB", ["service"])
CPU_USAGE = Gauge("demo_cpu_usage_percent", "CPU usage percentage", ["service"])

# Demo scenarios
SCENARIOS = [
    "traffic_patterns",
    "service_failures",
    "memory_leaks",
    "deployments",
    "scaling",
    "chaos_engineering",
]

# Services to generate traffic for
SERVICES = {
    "user-service": {
        "endpoints": [
            {"path": "/api/users", "methods": ["GET", "POST"]},
            {"path": "/api/users/{id}", "methods": ["GET", "PUT", "DELETE"]},
            {"path": "/api/auth/login", "methods": ["POST"]},
            {"path": "/api/auth/logout", "methods": ["POST"]},
            {"path": "/health", "methods": ["GET"]},
        ],
        "base_rps": 20,
        "error_rate": 0.02,
    },
    "payment-service": {
        "endpoints": [
            {"path": "/api/payments", "methods": ["GET", "POST"]},
            {"path": "/api/payments/{id}", "methods": ["GET"]},
            {"path": "/api/transactions", "methods": ["GET"]},
            {"path": "/api/refunds", "methods": ["POST"]},
            {"path": "/health", "methods": ["GET"]},
        ],
        "base_rps": 10,
        "error_rate": 0.01,
    },
    "order-service": {
        "endpoints": [
            {"path": "/api/orders", "methods": ["GET", "POST"]},
            {"path": "/api/orders/{id}", "methods": ["GET", "PUT", "DELETE"]},
            {"path": "/api/cart", "methods": ["GET", "POST", "PUT"]},
            {"path": "/api/checkout", "methods": ["POST"]},
            {"path": "/health", "methods": ["GET"]},
        ],
        "base_rps": 15,
        "error_rate": 0.03,
    },
}

# Current active scenarios
active_scenarios = {}
running = True


async def generate_traffic(service_name: str, endpoint: Dict[str, Any]) -> None:
    """Generate artificial traffic for a service endpoint."""
    path = endpoint["path"]
    methods = endpoint["methods"]

    # Replace path parameters with random values
    if "{id}" in path:
        path = path.replace("{id}", str(random.randint(1, 1000)))

    method = random.choice(methods)
    status = 200

    # Simulate errors based on service error rate
    if random.random() < SERVICES[service_name]["error_rate"]:
        status = random.choice([400, 401, 403, 404, 500])

    # Record metrics
    start_time = time.time()
    REQUESTS_TOTAL.labels(service_name, path, method, status).inc()

    # Simulate latency
    latency = random.uniform(0.01, 0.5)
    if "payment" in service_name and active_scenarios.get("service_failures"):
        # Increase latency during service_failures scenario for payment service
        latency *= 3

    await asyncio.sleep(latency)
    LATENCY.labels(service_name, path).observe(latency)

    # Log request (verbose)
    logger.debug(f"{method} {service_name}{path} - {status} - {latency:.3f}s")

    # Update current error rate for service
    if status >= 400:
        current_error_rate = random.uniform(
            SERVICES[service_name]["error_rate"] * 0.5,
            SERVICES[service_name]["error_rate"] * 1.5,
        )
        ERROR_RATE.labels(service_name).set(current_error_rate * 100)  # as percentage


async def traffic_generator() -> None:
    """Generate traffic for all services based on RPS settings."""
    logger.info("Starting traffic generator")

    while running:
        for service_name, service_config in SERVICES.items():
            # Calculate actual RPS based on time of day and active scenarios
            base_rps = service_config["base_rps"]
            current_rps = base_rps

            # Apply time-of-day pattern (busier during "business hours")
            hour = datetime.datetime.now().hour
            if 9 <= hour <= 17:  # 9 AM to 5 PM
                current_rps = base_rps * random.uniform(1.0, 1.5)
            elif 0 <= hour <= 5:  # Late night/early morning
                current_rps = base_rps * random.uniform(0.3, 0.7)

            # Apply traffic_patterns scenario effect if active
            if active_scenarios.get("traffic_patterns"):
                # Create spike or drop in traffic
                if random.random() < 0.2:  # 20% chance of anomaly
                    if random.random() < 0.7:  # 70% chance of spike vs drop
                        current_rps *= random.uniform(1.5, 3.0)  # Traffic spike
                    else:
                        current_rps *= random.uniform(0.2, 0.5)  # Traffic drop

            # Calculate how many requests to generate this second
            requests_this_second = int(current_rps)
            if random.random() < (current_rps - requests_this_second):
                requests_this_second += 1

            # Generate the traffic
            tasks = []
            for _ in range(requests_this_second):
                endpoint = random.choice(service_config["endpoints"])
                tasks.append(generate_traffic(service_name, endpoint))

            if tasks:
                await asyncio.gather(*tasks)

        # Sleep before next batch
        await asyncio.sleep(1)


async def simulate_resource_usage() -> None:
    """Simulate and report resource usage metrics."""
    logger.info("Starting resource usage simulator")

    while running:
        for service_name in SERVICES.keys():
            # Simulate memory usage (MB)
            base_memory = random.uniform(100, 300)
            if active_scenarios.get("memory_leaks") and service_name == "order-service":
                # Simulated memory leak in order service
                elapsed_time = time.time() - active_scenarios["memory_leaks"].get(
                    "start_time", time.time()
                )
                # Increase memory usage by 10MB per minute
                additional_memory = (elapsed_time / 60) * 10
                base_memory += additional_memory

            MEMORY_USAGE.labels(service_name).set(base_memory)

            # Simulate CPU usage (%)
            base_cpu = random.uniform(10, 30)
            if (
                active_scenarios.get("service_failures")
                and service_name == "payment-service"
            ):
                # Simulated high CPU during service failures
                base_cpu = random.uniform(70, 95)

            CPU_USAGE.labels(service_name).set(base_cpu)

        await asyncio.sleep(5)


async def activate_scenario(scenario_name: str, duration_seconds: int) -> None:
    """Activate a specific demo scenario."""
    if scenario_name not in SCENARIOS:
        logger.error(f"Unknown scenario: {scenario_name}")
        return

    if scenario_name in active_scenarios:
        logger.info(f"Scenario {scenario_name} already active, skipping")
        return

    logger.info(f"Activating scenario: {scenario_name} for {duration_seconds}s")

    # Record scenario start
    active_scenarios[scenario_name] = {
        "start_time": time.time(),
        "duration": duration_seconds,
    }

    # Redis notification for dashboard
    scenario_data = {
        "type": "scenario_start",
        "scenario": scenario_name,
        "start_time": datetime.datetime.now().isoformat(),
        "duration_seconds": duration_seconds,
    }
    redis_client.publish("demo:events", json.dumps(scenario_data))

    # Apply scenario-specific effects
    if scenario_name == "service_failures":
        # Increase error rate for payment service
        SERVICES["payment-service"]["error_rate"] = 0.15

    # Sleep for the scenario duration
    await asyncio.sleep(duration_seconds)

    # Deactivate the scenario
    if scenario_name in active_scenarios:
        del active_scenarios[scenario_name]

        # Reset effects
        if scenario_name == "service_failures":
            SERVICES["payment-service"]["error_rate"] = 0.01

        # Redis notification for dashboard
        end_data = {
            "type": "scenario_end",
            "scenario": scenario_name,
            "end_time": datetime.datetime.now().isoformat(),
        }
        redis_client.publish("demo:events", json.dumps(end_data))

        logger.info(f"Scenario {scenario_name} completed")


async def scenario_scheduler() -> None:
    """Schedule random scenarios periodically."""
    logger.info("Starting scenario scheduler")

    # Wait for initial delay before starting scenarios
    await asyncio.sleep(60)

    while running:
        # Randomly select a scenario that isn't already active
        available_scenarios = [s for s in SCENARIOS if s not in active_scenarios]
        if not available_scenarios:
            await asyncio.sleep(30)
            continue

        scenario = random.choice(available_scenarios)
        duration = random.randint(3 * 60, 10 * 60)  # 3-10 minutes

        # Start the scenario
        asyncio.create_task(activate_scenario(scenario, duration))

        # Wait before scheduling next scenario
        interval = int(os.environ.get("SCENARIO_INTERVAL", "300"))
        wait_time = random.randint(interval, interval * 2)
        await asyncio.sleep(wait_time)


async def manual_scenario_api() -> None:
    """Start a simple API server for manually triggering scenarios."""
    from aiohttp import web

    app = web.Application()
    routes = web.RouteTableDef()

    @routes.get("/scenarios")
    async def get_scenarios(request):
        """Get list of available and active scenarios."""
        return web.json_response(
            {"available": SCENARIOS, "active": list(active_scenarios.keys())}
        )

    @routes.post("/scenarios/{name}")
    async def trigger_scenario(request):
        """Trigger a specific scenario."""
        scenario_name = request.match_info["name"]
        if scenario_name not in SCENARIOS:
            return web.json_response(
                {"error": f"Unknown scenario: {scenario_name}"}, status=400
            )

        data = await request.json()
        duration = data.get("duration", 300)  # Default 5 minutes

        asyncio.create_task(activate_scenario(scenario_name, duration))
        return web.json_response(
            {"status": "started", "scenario": scenario_name, "duration": duration}
        )

    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8090)
    await site.start()
    logger.info("Manual scenario API listening on http://0.0.0.0:8090")


def handle_signals() -> None:
    """Setup signal handling for graceful shutdown."""

    def shutdown_handler(signum, frame):
        global running
        logger.info(f"Received signal {signum}, shutting down...")
        running = False

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP DevOps Platform Demo Orchestrator"
    )
    parser.add_argument(
        "--init-all", action="store_true", help="Initialize all demo components"
    )
    parser.add_argument(
        "--start-scenarios",
        action="store_true",
        help="Start automatic scenario scheduling",
    )
    parser.add_argument(
        "--metrics-port",
        type=int,
        default=8091,
        help="Port for Prometheus metrics server",
    )
    args = parser.parse_args()

    # Start Prometheus metrics server
    start_http_server(args.metrics_port)
    logger.info(f"Prometheus metrics available on port {args.metrics_port}")

    # Set up signal handlers
    handle_signals()

    # Start core tasks
    tasks = [traffic_generator(), simulate_resource_usage(), manual_scenario_api()]

    # Conditionally start scenario scheduler
    if args.start_scenarios or os.environ.get("AUTO_START_SCENARIOS") == "true":
        tasks.append(scenario_scheduler())

    # If initializing all components
    if args.init_all:
        logger.info("Initializing demo environment")
        # In a real implementation, this would set up example data, configs, etc.

    # Run all tasks concurrently
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Demo orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Error in demo orchestrator: {e}", exc_info=True)
        sys.exit(1)
