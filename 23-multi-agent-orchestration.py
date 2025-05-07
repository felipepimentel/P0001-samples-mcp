import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import Message, SystemMessage, UserMessage

# Initialize MCP server for multi-agent orchestration
mcp = FastMCP("Multi-Agent Orchestration")

# Directory for storing agent states and workflow history
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_multi_agent"
WORKFLOWS_DIR = DATA_DIR / "workflows"
AGENT_STATES_DIR = DATA_DIR / "agent_states"
RESULTS_DIR = DATA_DIR / "results"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
WORKFLOWS_DIR.mkdir(exist_ok=True)
AGENT_STATES_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


# Agent types
class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    WRITER = "writer"
    CRITIC = "critic"


# Task states
class TaskState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Agent data structure
@dataclass
class Agent:
    id: str
    name: str
    role: AgentRole
    skills: List[str]
    current_task: Optional[str] = None
    state: Dict[str, Any] = field(default_factory=dict)


# Task data structure
@dataclass
class Task:
    id: str
    title: str
    description: str
    assigned_agent_id: Optional[str] = None
    state: TaskState = TaskState.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)


# Workflow data structure
@dataclass
class Workflow:
    id: str
    name: str
    description: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    agents: Dict[str, Agent] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed: bool = False


# In-memory storage
workflows: Dict[str, Workflow] = {}


def load_workflows_from_disk() -> None:
    """Load all workflows from disk"""
    for workflow_file in WORKFLOWS_DIR.glob("*.json"):
        try:
            with open(workflow_file, "r") as f:
                data = json.load(f)
                workflow_id = workflow_file.stem

                # Create tasks
                tasks = {}
                for task_id, task_data in data.get("tasks", {}).items():
                    tasks[task_id] = Task(
                        id=task_id,
                        title=task_data["title"],
                        description=task_data["description"],
                        assigned_agent_id=task_data.get("assigned_agent_id"),
                        state=TaskState(task_data["state"]),
                        created_at=task_data["created_at"],
                        updated_at=task_data["updated_at"],
                        result=task_data.get("result"),
                        depends_on=task_data.get("depends_on", []),
                    )

                # Create agents
                agents = {}
                for agent_id, agent_data in data.get("agents", {}).items():
                    agents[agent_id] = Agent(
                        id=agent_id,
                        name=agent_data["name"],
                        role=AgentRole(agent_data["role"]),
                        skills=agent_data["skills"],
                        current_task=agent_data.get("current_task"),
                        state=agent_data.get("state", {}),
                    )

                # Create workflow
                workflow = Workflow(
                    id=workflow_id,
                    name=data["name"],
                    description=data["description"],
                    tasks=tasks,
                    agents=agents,
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    completed=data["completed"],
                )

                workflows[workflow_id] = workflow
        except Exception as e:
            print(f"Error loading workflow {workflow_file}: {e}")


def save_workflow_to_disk(workflow: Workflow) -> None:
    """Save a workflow to disk"""
    workflow_file = WORKFLOWS_DIR / f"{workflow.id}.json"

    # Convert to JSON-serializable dict
    tasks_dict = {}
    for task_id, task in workflow.tasks.items():
        tasks_dict[task_id] = {
            "title": task.title,
            "description": task.description,
            "assigned_agent_id": task.assigned_agent_id,
            "state": task.state,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "result": task.result,
            "depends_on": task.depends_on,
        }

    agents_dict = {}
    for agent_id, agent in workflow.agents.items():
        agents_dict[agent_id] = {
            "name": agent.name,
            "role": agent.role,
            "skills": agent.skills,
            "current_task": agent.current_task,
            "state": agent.state,
        }

    workflow_data = {
        "name": workflow.name,
        "description": workflow.description,
        "tasks": tasks_dict,
        "agents": agents_dict,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "completed": workflow.completed,
    }

    with open(workflow_file, "w") as f:
        json.dump(workflow_data, f, indent=2)


# Load workflows at startup
load_workflows_from_disk()


# Multi-agent orchestration utilities
def get_next_tasks(workflow_id: str) -> List[str]:
    """Get IDs of tasks that are ready to be processed"""
    if workflow_id not in workflows:
        return []

    workflow = workflows[workflow_id]
    ready_tasks = []

    for task_id, task in workflow.tasks.items():
        # Skip tasks that are not pending
        if task.state != TaskState.PENDING:
            continue

        # Check if all dependencies are completed
        dependencies_met = True
        for dep_id in task.depends_on:
            if (
                dep_id not in workflow.tasks
                or workflow.tasks[dep_id].state != TaskState.COMPLETED
            ):
                dependencies_met = False
                break

        if dependencies_met:
            ready_tasks.append(task_id)

    return ready_tasks


def assign_task_to_agent(workflow_id: str, task_id: str, agent_id: str) -> bool:
    """Assign a task to an agent"""
    if workflow_id not in workflows:
        return False

    workflow = workflows[workflow_id]

    if task_id not in workflow.tasks or agent_id not in workflow.agents:
        return False

    task = workflow.tasks[task_id]
    agent = workflow.agents[agent_id]

    # Check if agent is already busy
    if agent.current_task is not None:
        return False

    # Assign task to agent
    task.assigned_agent_id = agent_id
    task.state = TaskState.IN_PROGRESS
    task.updated_at = time.time()

    # Update agent
    agent.current_task = task_id

    # Save changes
    workflow.updated_at = time.time()
    save_workflow_to_disk(workflow)

    return True


async def simulate_agent_work(
    workflow_id: str, agent_id: str, prompt: str
) -> Optional[str]:
    """Simulate an agent working on a task by querying an LLM"""
    if workflow_id not in workflows:
        return None

    workflow = workflows[workflow_id]

    if agent_id not in workflow.agents:
        return None

    agent = workflow.agents[agent_id]

    if agent.current_task is None or agent.current_task not in workflow.tasks:
        return None

    task = workflow.tasks[agent.current_task]

    # Create agent-specific system message based on role
    role_descriptions = {
        AgentRole.COORDINATOR: "You are a coordinator agent responsible for planning and managing tasks.",
        AgentRole.RESEARCHER: "You are a researcher agent responsible for gathering and synthesizing information.",
        AgentRole.ANALYZER: "You are an analyzer agent responsible for examining data and extracting insights.",
        AgentRole.WRITER: "You are a writer agent responsible for creating well-written content.",
        AgentRole.CRITIC: "You are a critic agent responsible for reviewing and providing constructive feedback.",
    }

    system_message = f"{role_descriptions.get(agent.role, 'You are an AI agent.')} \
                       You have these skills: {', '.join(agent.skills)}. \
                       Complete the assigned task to the best of your abilities."

    # Create user message with task description and any additional prompt
    user_message = f"Task: {task.title}\n\nDescription: {task.description}\n\n{prompt}"

    # Use LLM to simulate agent's work
    messages = [SystemMessage(system_message), UserMessage(user_message)]

    try:
        # Sample from LLM
        completion = await mcp.sample(messages=messages)
        result = completion.content

        # Store result in task
        task.result = result
        task.state = TaskState.COMPLETED
        task.updated_at = time.time()

        # Free up the agent
        agent.current_task = None

        # Save changes
        workflow.updated_at = time.time()
        save_workflow_to_disk(workflow)

        # Check if all tasks are completed
        all_completed = all(
            t.state == TaskState.COMPLETED for t in workflow.tasks.values()
        )
        if all_completed:
            workflow.completed = True
            save_workflow_to_disk(workflow)

        return result
    except Exception as e:
        # Mark task as failed
        task.state = TaskState.FAILED
        task.result = f"Error: {str(e)}"
        task.updated_at = time.time()

        # Free up the agent
        agent.current_task = None

        # Save changes
        workflow.updated_at = time.time()
        save_workflow_to_disk(workflow)

        return None


# MCP Tools for Workflow Management
@mcp.tool()
def create_workflow(name: str, description: str) -> str:
    """
    Create a new multi-agent workflow

    Args:
        name: Name of the workflow
        description: Description of the workflow
    """
    workflow_id = str(uuid.uuid4())[:8]

    workflow = Workflow(id=workflow_id, name=name, description=description)

    workflows[workflow_id] = workflow
    save_workflow_to_disk(workflow)

    return json.dumps(
        {
            "message": f"Workflow '{name}' created successfully",
            "workflow_id": workflow_id,
        },
        indent=2,
    )


@mcp.tool()
def add_agent_to_workflow(
    workflow_id: str, name: str, role: str, skills: List[str]
) -> str:
    """
    Add an agent to a workflow

    Args:
        workflow_id: ID of the workflow
        name: Name of the agent
        role: Role of the agent (coordinator, researcher, analyzer, writer, critic)
        skills: List of agent skills
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    # Validate role
    try:
        agent_role = AgentRole(role)
    except ValueError:
        valid_roles = [r.value for r in AgentRole]
        return f"Error: Invalid role. Choose from: {', '.join(valid_roles)}"

    workflow = workflows[workflow_id]

    # Create agent
    agent_id = str(uuid.uuid4())[:8]
    agent = Agent(id=agent_id, name=name, role=agent_role, skills=skills)

    # Add to workflow
    workflow.agents[agent_id] = agent
    workflow.updated_at = time.time()
    save_workflow_to_disk(workflow)

    return json.dumps(
        {
            "message": f"Agent '{name}' added to workflow '{workflow.name}'",
            "agent_id": agent_id,
        },
        indent=2,
    )


@mcp.tool()
def add_task_to_workflow(
    workflow_id: str, title: str, description: str, depends_on: List[str] = None
) -> str:
    """
    Add a task to a workflow

    Args:
        workflow_id: ID of the workflow
        title: Title of the task
        description: Description of the task
        depends_on: List of task IDs this task depends on
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]

    # Validate dependencies
    if depends_on:
        for dep_id in depends_on:
            if dep_id not in workflow.tasks:
                return f"Error: Dependency task with ID {dep_id} not found"

    # Create task
    task_id = str(uuid.uuid4())[:8]
    task = Task(
        id=task_id, title=title, description=description, depends_on=depends_on or []
    )

    # Add to workflow
    workflow.tasks[task_id] = task
    workflow.updated_at = time.time()
    save_workflow_to_disk(workflow)

    return json.dumps(
        {
            "message": f"Task '{title}' added to workflow '{workflow.name}'",
            "task_id": task_id,
        },
        indent=2,
    )


@mcp.tool()
def list_workflows() -> str:
    """List all workflows"""
    if not workflows:
        return "No workflows found."

    result = []
    for workflow_id, workflow in workflows.items():
        result.append(
            {
                "id": workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "tasks_count": len(workflow.tasks),
                "agents_count": len(workflow.agents),
                "completed": workflow.completed,
                "created_at": workflow.created_at,
            }
        )

    return json.dumps(result, indent=2)


@mcp.tool()
def get_workflow_details(workflow_id: str) -> str:
    """
    Get detailed information about a workflow

    Args:
        workflow_id: ID of the workflow
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]

    # Format tasks
    tasks = []
    for task_id, task in workflow.tasks.items():
        tasks.append(
            {
                "id": task_id,
                "title": task.title,
                "state": task.state,
                "assigned_agent_id": task.assigned_agent_id,
                "depends_on": task.depends_on,
            }
        )

    # Format agents
    agents = []
    for agent_id, agent in workflow.agents.items():
        agents.append(
            {
                "id": agent_id,
                "name": agent.name,
                "role": agent.role,
                "skills": agent.skills,
                "current_task": agent.current_task,
            }
        )

    result = {
        "id": workflow_id,
        "name": workflow.name,
        "description": workflow.description,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "completed": workflow.completed,
        "tasks": tasks,
        "agents": agents,
    }

    return json.dumps(result, indent=2)


# MCP Tools for Task and Agent Management
@mcp.tool()
def get_next_available_tasks(workflow_id: str) -> str:
    """
    Get tasks that are ready to be assigned to agents

    Args:
        workflow_id: ID of the workflow
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    ready_task_ids = get_next_tasks(workflow_id)

    if not ready_task_ids:
        return (
            f"No tasks ready for assignment in workflow '{workflows[workflow_id].name}'"
        )

    workflow = workflows[workflow_id]
    ready_tasks = []

    for task_id in ready_task_ids:
        task = workflow.tasks[task_id]
        ready_tasks.append(
            {"id": task_id, "title": task.title, "description": task.description}
        )

    return json.dumps(ready_tasks, indent=2)


@mcp.tool()
def get_available_agents(workflow_id: str) -> str:
    """
    Get agents that are available for task assignment

    Args:
        workflow_id: ID of the workflow
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]
    available_agents = []

    for agent_id, agent in workflow.agents.items():
        if agent.current_task is None:
            available_agents.append(
                {
                    "id": agent_id,
                    "name": agent.name,
                    "role": agent.role,
                    "skills": agent.skills,
                }
            )

    if not available_agents:
        return f"No available agents in workflow '{workflow.name}'"

    return json.dumps(available_agents, indent=2)


@mcp.tool()
def assign_task(workflow_id: str, task_id: str, agent_id: str) -> str:
    """
    Assign a task to an agent

    Args:
        workflow_id: ID of the workflow
        task_id: ID of the task to assign
        agent_id: ID of the agent to assign the task to
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]

    if task_id not in workflow.tasks:
        return f"Error: Task with ID {task_id} not found"

    if agent_id not in workflow.agents:
        return f"Error: Agent with ID {agent_id} not found"

    if assign_task_to_agent(workflow_id, task_id, agent_id):
        task = workflow.tasks[task_id]
        agent = workflow.agents[agent_id]

        return json.dumps(
            {
                "message": f"Task '{task.title}' assigned to agent '{agent.name}'",
                "task_id": task_id,
                "agent_id": agent_id,
            },
            indent=2,
        )
    else:
        return "Error: Could not assign task. Agent might be busy or task dependencies are not satisfied."


@mcp.tool()
async def run_agent_task(workflow_id: str, agent_id: str, prompt: str = "") -> str:
    """
    Run an agent on its assigned task

    Args:
        workflow_id: ID of the workflow
        agent_id: ID of the agent
        prompt: Additional prompt to guide the agent
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]

    if agent_id not in workflow.agents:
        return f"Error: Agent with ID {agent_id} not found"

    agent = workflow.agents[agent_id]

    if agent.current_task is None:
        return f"Error: Agent '{agent.name}' has no assigned task"

    task_id = agent.current_task
    task = workflow.tasks[task_id]

    result = await simulate_agent_work(workflow_id, agent_id, prompt)

    if result is None:
        return f"Error: Failed to run agent '{agent.name}' on task '{task.title}'"

    return json.dumps(
        {
            "message": f"Agent '{agent.name}' completed task '{task.title}'",
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result,
        },
        indent=2,
    )


@mcp.tool()
def get_task_result(workflow_id: str, task_id: str) -> str:
    """
    Get the result of a completed task

    Args:
        workflow_id: ID of the workflow
        task_id: ID of the task
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]

    if task_id not in workflow.tasks:
        return f"Error: Task with ID {task_id} not found"

    task = workflow.tasks[task_id]

    if task.state != TaskState.COMPLETED:
        return f"Error: Task '{task.title}' is not completed yet (current state: {task.state})"

    return json.dumps(
        {"task_id": task_id, "title": task.title, "result": task.result}, indent=2
    )


@mcp.tool()
async def run_full_workflow(workflow_id: str) -> str:
    """
    Run a complete workflow from start to finish

    Args:
        workflow_id: ID of the workflow
    """
    if workflow_id not in workflows:
        return f"Error: Workflow with ID {workflow_id} not found"

    workflow = workflows[workflow_id]

    if workflow.completed:
        return f"Workflow '{workflow.name}' is already completed"

    if not workflow.tasks:
        return f"Error: Workflow '{workflow.name}' has no tasks"

    if not workflow.agents:
        return f"Error: Workflow '{workflow.name}' has no agents"

    # Keep track of completed tasks
    completed_tasks = set()
    result_log = [f"Starting workflow '{workflow.name}'..."]

    # Keep running until all tasks are completed or no progress is made
    progress_made = True
    while progress_made and not workflow.completed:
        progress_made = False

        # Get next tasks
        ready_task_ids = get_next_tasks(workflow_id)
        if not ready_task_ids:
            if len(completed_tasks) < len(workflow.tasks):
                result_log.append(
                    "No more tasks are ready, but not all tasks are completed. There might be a dependency cycle."
                )
            break

        # For each ready task, find an available agent and run the task
        for task_id in ready_task_ids:
            # Get available agents
            available_agents = []
            for agent_id, agent in workflow.agents.items():
                if agent.current_task is None:
                    available_agents.append(agent_id)

            if not available_agents:
                result_log.append(
                    "No available agents. Waiting for current tasks to complete..."
                )
                break

            # Pick best agent for task (simplified logic - just pick first available)
            agent_id = available_agents[0]

            # Assign task to agent
            if assign_task_to_agent(workflow_id, task_id, agent_id):
                task = workflow.tasks[task_id]
                agent = workflow.agents[agent_id]
                result_log.append(
                    f"Assigned task '{task.title}' to agent '{agent.name}'"
                )

                # Run the task
                prompt = "Complete this task while collaborating with other agents in this workflow."
                result = await simulate_agent_work(workflow_id, agent_id, prompt)

                if result is not None:
                    progress_made = True
                    completed_tasks.add(task_id)
                    result_log.append(
                        f"Agent '{agent.name}' completed task '{task.title}'"
                    )
                else:
                    result_log.append(
                        f"Agent '{agent.name}' failed to complete task '{task.title}'"
                    )
            else:
                result_log.append(
                    f"Could not assign task {task_id} to agent {agent_id}"
                )

        # Check if workflow is completed
        workflow = workflows[workflow_id]  # Refresh from in-memory storage

    # Final report
    if workflow.completed:
        result_log.append(f"Workflow '{workflow.name}' completed successfully!")
        result_log.append(
            f"Completed {len(completed_tasks)} out of {len(workflow.tasks)} tasks."
        )

        # Save final results
        final_results = {}
        for task_id, task in workflow.tasks.items():
            if task.state == TaskState.COMPLETED:
                final_results[task.title] = task.result

        result_file = RESULTS_DIR / f"{workflow_id}_results.json"
        with open(result_file, "w") as f:
            json.dump(final_results, f, indent=2)

        result_log.append(f"Results saved to {result_file}")
    else:
        result_log.append(f"Workflow '{workflow.name}' did not complete.")
        result_log.append(
            f"Completed {len(completed_tasks)} out of {len(workflow.tasks)} tasks."
        )

    return "\n".join(result_log)


# MCP Resources
@mcp.resource("workflows://list")
def get_workflows_resource() -> str:
    """Get a list of all workflows"""
    workflows_list = []
    for workflow_id, workflow in workflows.items():
        workflows_list.append(
            {
                "id": workflow_id,
                "name": workflow.name,
                "completed": workflow.completed,
                "tasks_count": len(workflow.tasks),
                "agents_count": len(workflow.agents),
            }
        )

    return json.dumps(workflows_list, indent=2)


@mcp.resource("workflows://workflow/{workflow_id}")
def get_workflow_resource(workflow_id: str) -> str:
    """Get summary of a specific workflow"""
    if workflow_id not in workflows:
        return json.dumps({"error": f"Workflow with ID {workflow_id} not found"})

    workflow = workflows[workflow_id]

    # Count tasks by state
    task_counts = {state.value: 0 for state in TaskState}
    for task in workflow.tasks.values():
        task_counts[task.state] += 1

    # Count agents by role
    agent_counts = {role.value: 0 for role in AgentRole}
    for agent in workflow.agents.values():
        agent_counts[agent.role] += 1

    return json.dumps(
        {
            "id": workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
            "completed": workflow.completed,
            "task_summary": task_counts,
            "agent_summary": agent_counts,
        },
        indent=2,
    )


@mcp.resource("workflows://results/{workflow_id}")
def get_workflow_results_resource(workflow_id: str) -> str:
    """Get results of a completed workflow"""
    if workflow_id not in workflows:
        return json.dumps({"error": f"Workflow with ID {workflow_id} not found"})

    workflow = workflows[workflow_id]

    if not workflow.completed:
        return json.dumps(
            {"message": f"Workflow '{workflow.name}' is not completed yet"}
        )

    results = {}
    for task_id, task in workflow.tasks.items():
        if task.state == TaskState.COMPLETED:
            results[task.title] = task.result

    return json.dumps(results, indent=2)


# Enhanced Prompts
@mcp.prompt()
def collaborative_task_prompt(
    task_description: str, agent_role: str, previous_results: Dict[str, str] = None
) -> List[Message]:
    """Generate a structured prompt for a collaborative task"""

    role_specializations = {
        AgentRole.COORDINATOR: "organizing, planning, and tracking progress",
        AgentRole.RESEARCHER: "gathering information, exploring options, and synthesizing knowledge",
        AgentRole.ANALYZER: "examining data critically, finding patterns, and generating insights",
        AgentRole.WRITER: "creating well-structured, clear, and engaging content",
        AgentRole.CRITIC: "evaluating work objectively, finding improvements, and ensuring quality",
    }

    system_message = f"""You are a specialized {agent_role} agent working in a multi-agent team. 
Your role focuses on {role_specializations.get(agent_role, "completing tasks")}.
You should approach the task from your specialized perspective while maintaining awareness that 
you are part of a collaborative workflow where other agents will build upon your work."""

    user_message = f"Your task: {task_description}\n\n"

    if previous_results:
        user_message += "Previous results from other agents:\n"
        for task_name, result in previous_results.items():
            user_message += f"\n--- {task_name} ---\n{result}\n"
        user_message += "\nUse these previous results in your work as appropriate."

    user_message += "\nComplete your part of this collaborative task, focusing on your role as a specialized agent."

    return [SystemMessage(system_message), UserMessage(user_message)]


@mcp.prompt()
def workflow_design_prompt(
    objective: str, available_agent_roles: List[str]
) -> List[Message]:
    """Generate a prompt for designing a multi-agent workflow"""

    roles_str = ", ".join(available_agent_roles)

    return [
        SystemMessage(
            "You are a workflow design specialist experienced in creating effective multi-agent systems."
        ),
        UserMessage(f"""Help me design a multi-agent workflow to achieve this objective: {objective}

Available agent roles: {roles_str}

Please provide:
1. A structured breakdown of the workflow (3-6 sequential steps)
2. Which agent roles should handle each step
3. The specific tasks each agent should complete
4. How information should flow between agents
5. How to evaluate the final output

Focus on creating a workflow where agents with different specializations collaborate efficiently."""),
    ]
