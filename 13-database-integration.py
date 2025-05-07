import os
import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Database Integration")

# Setup a SQLite database in a safe location
DB_DIR = Path(os.path.expanduser("~")) / "mcp_db"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "example.db"


# Initialize the database
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0
        )
        """)
        conn.commit()


init_db()


@mcp.tool()
def get_all_tasks() -> str:
    """Get all tasks from the database"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, description, completed FROM tasks")
            tasks = cursor.fetchall()

            if not tasks:
                return "No tasks found."

            result = []
            for task in tasks:
                task_id, title, description, completed = task
                status = "Completed" if completed else "Pending"
                result.append(f"Task #{task_id}: {title} - {status}")
                if description:
                    result.append(f"  Description: {description}")

            return "\n".join(result)
    except Exception as e:
        return f"Error retrieving tasks: {str(e)}"


@mcp.tool()
def add_task(title: str, description: str = "") -> str:
    """
    Add a new task to the database

    Args:
        title: The task title
        description: Optional task description
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, description) VALUES (?, ?)",
                (title, description),
            )
            conn.commit()
            task_id = cursor.lastrowid
            return f"Task added successfully with ID: {task_id}"
    except Exception as e:
        return f"Error adding task: {str(e)}"


@mcp.tool()
def complete_task(task_id: int) -> str:
    """
    Mark a task as completed

    Args:
        task_id: The ID of the task to mark as completed
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                return f"Task with ID {task_id} not found."

            cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
            conn.commit()
            return f"Task #{task_id} marked as completed."
    except Exception as e:
        return f"Error completing task: {str(e)}"


@mcp.tool()
def delete_task(task_id: int) -> str:
    """
    Delete a task from the database

    Args:
        task_id: The ID of the task to delete
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                return f"Task with ID {task_id} not found."

            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return f"Task #{task_id} deleted successfully."
    except Exception as e:
        return f"Error deleting task: {str(e)}"


@mcp.resource("tasks://list")
def get_tasks_resource() -> str:
    """Get all tasks as a resource"""
    return get_all_tasks()
