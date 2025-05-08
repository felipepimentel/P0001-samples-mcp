import getpass
import json

# Workaround for os.getlogin issues in some environments
import os
import random
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("ProgressTrackingDemo")

# Simulate a database of tasks
tasks_db = {}


class Task:
    """Represents a long-running task with progress tracking"""

    def __init__(self, name: str, steps: int):
        self.id = str(uuid.uuid4())
        self.name = name
        self.total_steps = steps
        self.current_step = 0
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.error = None
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.progress_token = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress": round(self.current_step / self.total_steps * 100)
            if self.total_steps > 0
            else 0,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


# Tools for creating and managing long-running tasks
@mcp.tool()
def start_data_processing(
    dataset_size: int, processing_time: float = 10.0
) -> Dict[str, Any]:
    """
    Start a simulated data processing task with progress tracking

    Args:
        dataset_size: Number of data points to process
        processing_time: Total processing time in seconds

    Returns:
        Task information including the task ID for tracking progress
    """
    # Create a new task
    task = Task(f"Data Processing ({dataset_size} items)", dataset_size)
    tasks_db[task.id] = task

    # Start processing in a background thread
    thread = threading.Thread(
        target=process_data_with_progress, args=(task, processing_time)
    )
    thread.daemon = True
    thread.start()

    return task.to_dict()


@mcp.tool()
def start_complex_analysis(
    complexity: int = 5, failure_chance: float = 0.0
) -> Dict[str, Any]:
    """
    Start a complex analysis task with multiple phases and progress tracking

    Args:
        complexity: Number of analysis phases (more phases = longer runtime)
        failure_chance: Probability of random failure (0.0 to 1.0)

    Returns:
        Task information including the task ID for tracking progress
    """
    # Total steps = sum of steps in all phases
    total_steps = sum(range(1, complexity + 1))

    # Create a new task
    task = Task(f"Complex Analysis (Complexity {complexity})", total_steps)
    tasks_db[task.id] = task

    # Start analysis in a background thread
    thread = threading.Thread(
        target=run_complex_analysis, args=(task, complexity, failure_chance)
    )
    thread.daemon = True
    thread.start()

    return task.to_dict()


@mcp.tool()
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the current status of a task

    Args:
        task_id: The ID of the task to check

    Returns:
        Current task status and progress information
    """
    if task_id not in tasks_db:
        return {"error": "Task not found"}

    return tasks_db[task_id].to_dict()


@mcp.tool()
def list_all_tasks() -> Dict[str, Any]:
    """
    List all tasks in the system

    Returns:
        Dictionary of all tasks with their current status
    """
    return {"tasks": [task.to_dict() for task in tasks_db.values()]}


@mcp.resource("tasks://{task_id}")
def get_task_resource(task_id: str) -> str:
    """Get detailed information about a specific task"""
    if task_id not in tasks_db:
        return json.dumps({"error": "Task not found"})

    return json.dumps(tasks_db[task_id].to_dict(), indent=2)


@mcp.resource("tasks://all")
def get_all_tasks_resource() -> str:
    """Get information about all tasks"""
    return json.dumps(
        {
            "tasks": [task.to_dict() for task in tasks_db.values()],
            "count": len(tasks_db),
            "pending": sum(1 for task in tasks_db.values() if task.status == "pending"),
            "running": sum(1 for task in tasks_db.values() if task.status == "running"),
            "completed": sum(
                1 for task in tasks_db.values() if task.status == "completed"
            ),
            "failed": sum(1 for task in tasks_db.values() if task.status == "failed"),
        },
        indent=2,
    )


# Progress tracking implementation functions
def process_data_with_progress(task: Task, processing_time: float):
    """Simulate data processing with progress updates"""
    try:
        # Start the task with progress tracking
        task.status = "running"
        progress_token = start_progress_tracking(task.id)
        task.progress_token = progress_token

        # Simulate processing steps
        step_time = processing_time / task.total_steps

        for i in range(task.total_steps):
            # Update progress
            task.current_step = i + 1
            update_progress(
                progress_token,
                task.current_step / task.total_steps,
                f"Processing item {task.current_step} of {task.total_steps}",
            )

            # Log progress
            if (i + 1) % max(1, task.total_steps // 10) == 0:  # Log every ~10% progress
                sys.stderr.write(
                    f"Task {task.id}: {task.current_step}/{task.total_steps} ({task.current_step / task.total_steps * 100:.1f}%)\n"
                )

            # Simulate work
            time.sleep(step_time)

        # Complete the task
        task.status = "completed"
        task.completed_at = datetime.now().isoformat()
        task.result = {
            "processed_items": task.total_steps,
            "success_rate": random.uniform(0.95, 1.0),
            "processing_time": processing_time,
        }

        # Final progress update
        update_progress(
            progress_token, 1.0, f"Successfully processed {task.total_steps} items"
        )
        end_progress_tracking(progress_token, success=True)

    except Exception as e:
        # Handle failures
        task.status = "failed"
        task.completed_at = datetime.now().isoformat()
        task.error = str(e)

        if task.progress_token:
            update_progress(
                task.progress_token,
                task.current_step / task.total_steps,
                f"Failed: {str(e)}",
            )
            end_progress_tracking(task.progress_token, success=False)


def run_complex_analysis(task: Task, complexity: int, failure_chance: float):
    """Simulate a complex multi-phase analysis with progress tracking"""
    try:
        # Start the task with progress tracking
        task.status = "running"
        progress_token = start_progress_tracking(task.id)
        task.progress_token = progress_token

        steps_completed = 0
        phase_results = {}

        # Run each analysis phase
        for phase in range(1, complexity + 1):
            phase_steps = phase  # Each phase has more steps than the previous

            # Phase description
            phase_name = f"Phase {phase}"
            update_progress(
                progress_token,
                steps_completed / task.total_steps,
                f"Starting {phase_name} ({phase_steps} steps)",
            )
            sys.stderr.write(f"Task {task.id}: Starting {phase_name}\n")

            # Simulate phase steps
            for step in range(1, phase_steps + 1):
                # Check for random failure
                if random.random() < failure_chance:
                    raise Exception(f"Random failure in {phase_name}, step {step}")

                # Update progress
                steps_completed += 1
                task.current_step = steps_completed
                update_progress(
                    progress_token,
                    steps_completed / task.total_steps,
                    f"{phase_name}: Step {step}/{phase_steps}",
                )

                # Simulate work
                time.sleep(0.5)  # Half-second per step

            # Record phase completion
            phase_results[phase_name] = {
                "duration": phase_steps * 0.5,
                "quality_score": random.uniform(0.7, 1.0),
            }

            sys.stderr.write(
                f"Task {task.id}: Completed {phase_name}, total progress: {steps_completed}/{task.total_steps}\n"
            )

        # Complete the task
        task.status = "completed"
        task.completed_at = datetime.now().isoformat()
        task.result = {
            "phases_completed": complexity,
            "total_steps": task.total_steps,
            "phase_results": phase_results,
            "overall_quality": sum(p["quality_score"] for p in phase_results.values())
            / len(phase_results),
        }

        # Final progress update
        update_progress(
            progress_token,
            1.0,
            f"Analysis completed successfully with {complexity} phases",
        )
        end_progress_tracking(progress_token, success=True)

    except Exception as e:
        # Handle failures
        task.status = "failed"
        task.completed_at = datetime.now().isoformat()
        task.error = str(e)

        if task.progress_token:
            update_progress(
                task.progress_token,
                task.current_step / task.total_steps,
                f"Analysis failed: {str(e)}",
            )
            end_progress_tracking(task.progress_token, success=False)


# Progress tracking API wrappers
def start_progress_tracking(task_id: str) -> str:
    """Start progress tracking for a task and return the progress token"""
    progress_token = f"task_{task_id}"

    # Initialize progress tracking with the MCP server
    mcp.start_progress_tracking(
        token=progress_token, title=f"Task {task_id[:8]}", message="Initializing..."
    )

    return progress_token


def update_progress(token: str, progress: float, message: str) -> None:
    """Update progress for a task"""
    mcp.update_progress_tracking(token=token, progress=progress, message=message)


def end_progress_tracking(token: str, success: bool) -> None:
    """End progress tracking for a task"""
    mcp.end_progress_tracking(token=token, success=success)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP PROGRESS TRACKING DEMO ===\n")
sys.stderr.write(
    "This example demonstrates MCP's progress tracking for long-running operations:\n"
)
sys.stderr.write(
    "1. Use start_data_processing to begin a task with progress tracking\n"
)
sys.stderr.write(
    "2. Use start_complex_analysis to run a multi-phase task (try setting failure_chance)\n"
)
sys.stderr.write("3. Watch progress updates appear in the client\n")
sys.stderr.write(
    "4. Use get_task_status or check the tasks:// resources to monitor tasks\n\n"
)
sys.stderr.write("MCP progress tracking allows servers to provide real-time updates\n")
sys.stderr.write("for long-running operations, enhancing the user experience.\n")
sys.stderr.write("=== END PROGRESS TRACKING INFO ===\n\n")

# This server demonstrates MCP progress tracking
# Run with: uv run mcp dev 47-progress-tracking.py
