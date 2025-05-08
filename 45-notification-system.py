import getpass
import json

# Workaround for os.getlogin issues in some environments
import os
import sys
import threading
import time
from datetime import datetime

from mcp.server.fastmcp import FastMCP

os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("NotificationDemo")

# Shared state
live_data = {
    "temperature": 20.0,
    "humidity": 50.0,
    "updated_at": datetime.now().isoformat(),
    "counter": 0,
}

# Track active subscriptions
active_subscriptions = set()


@mcp.on_subscription_created
def handle_subscription_created(params):
    """Handle a new subscription to a resource"""
    uri = params.get("uri")
    sys.stderr.write(f"Subscription created for: {uri}\n")
    active_subscriptions.add(uri)


@mcp.on_subscription_canceled
def handle_subscription_canceled(params):
    """Handle a canceled subscription"""
    uri = params.get("uri")
    sys.stderr.write(f"Subscription canceled for: {uri}\n")
    active_subscriptions.discard(uri)


# Dynamic resources that change over time
@mcp.resource("sensor://temperature")
def get_temperature():
    """Get the current temperature"""
    return json.dumps(
        {
            "value": live_data["temperature"],
            "unit": "°C",
            "updated_at": live_data["updated_at"],
        }
    )


@mcp.resource("sensor://humidity")
def get_humidity():
    """Get the current humidity"""
    return json.dumps(
        {
            "value": live_data["humidity"],
            "unit": "%",
            "updated_at": live_data["updated_at"],
        }
    )


@mcp.resource("sensor://dashboard")
def get_dashboard():
    """Get all sensor data in one resource"""
    return json.dumps(
        {
            "temperature": {"value": live_data["temperature"], "unit": "°C"},
            "humidity": {"value": live_data["humidity"], "unit": "%"},
            "updated_at": live_data["updated_at"],
            "counter": live_data["counter"],
        }
    )


# Tools to interact with the resources
@mcp.tool()
def update_temperature(value: float) -> str:
    """Update the temperature sensor value"""
    old_value = live_data["temperature"]
    live_data["temperature"] = value
    live_data["updated_at"] = datetime.now().isoformat()
    live_data["counter"] += 1

    # Send notifications for all related resources
    notify_resource_change("sensor://temperature")
    notify_resource_change("sensor://dashboard")

    return f"Temperature updated from {old_value}°C to {value}°C"


@mcp.tool()
def update_humidity(value: float) -> str:
    """Update the humidity sensor value"""
    old_value = live_data["humidity"]
    live_data["humidity"] = value
    live_data["updated_at"] = datetime.now().isoformat()
    live_data["counter"] += 1

    # Send notifications for all related resources
    notify_resource_change("sensor://humidity")
    notify_resource_change("sensor://dashboard")

    return f"Humidity updated from {old_value}% to {value}%"


@mcp.tool()
def list_active_subscriptions() -> dict:
    """Get a list of active subscriptions"""
    return {"subscriptions": list(active_subscriptions)}


@mcp.tool()
def simulate_continuous_updates(
    duration_sec: int = 30, interval_sec: float = 1.0
) -> str:
    """
    Simulate continuous updates to sensors for a specified duration.
    This demonstrates how notifications work with fast-changing data.
    """

    def run_simulation():
        start_time = time.time()
        update_count = 0

        while time.time() - start_time < duration_sec:
            # Generate simulated sensor readings
            live_data["temperature"] = 20 + 5 * (
                0.5 - (time.time() % 10) / 10
            )  # Oscillation
            live_data["humidity"] = 50 + 10 * (
                0.5 - (time.time() % 15) / 15
            )  # Different oscillation
            live_data["updated_at"] = datetime.now().isoformat()
            live_data["counter"] += 1
            update_count += 1

            # Send notifications for all related resources
            notify_resource_change("sensor://temperature")
            notify_resource_change("sensor://humidity")
            notify_resource_change("sensor://dashboard")

            # Log update (visible in the server's stderr)
            if update_count % 5 == 0:  # Log every 5 updates to reduce noise
                sys.stderr.write(
                    f"Update #{update_count}: T={live_data['temperature']:.2f}°C, H={live_data['humidity']:.2f}%\n"
                )

            time.sleep(interval_sec)

        sys.stderr.write(
            f"Simulation complete: {update_count} updates sent over {duration_sec} seconds\n"
        )

    # Run the simulation in a background thread
    thread = threading.Thread(target=run_simulation)
    thread.daemon = True
    thread.start()

    return f"Started sensor simulation for {duration_sec} seconds with updates every {interval_sec} seconds"


def notify_resource_change(uri):
    """Send a notification if the resource is being subscribed to"""
    if uri in active_subscriptions:
        sys.stderr.write(
            f"Sending notification for {uri} (counter: {live_data['counter']})\n"
        )
        mcp.notify_resource_changed(uri)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP NOTIFICATION SYSTEM DEMO ===\n")
sys.stderr.write("This example demonstrates MCP's resource notification system:\n")
sys.stderr.write(
    "1. Subscribe to resources: sensor://temperature, sensor://humidity, or sensor://dashboard\n"
)
sys.stderr.write(
    "2. Use update_temperature/update_humidity tools to trigger notifications\n"
)
sys.stderr.write("3. Use simulate_continuous_updates to see real-time notifications\n")
sys.stderr.write(
    "4. Use list_active_subscriptions to see what resources are being watched\n\n"
)
sys.stderr.write("MCP servers can send notifications when resources change, allowing\n")
sys.stderr.write("clients to keep their data up-to-date without constant polling.\n")
sys.stderr.write("=== END NOTIFICATION SYSTEM INFO ===\n\n")

# This server demonstrates the MCP notification system
# Run with: uv run mcp dev 45-notification-system.py
