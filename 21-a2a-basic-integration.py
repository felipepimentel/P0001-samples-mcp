import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import Message, SystemMessage, UserMessage

# Initialize MCP server with both MCP tools and A2A capabilities
mcp = FastMCP("MCP-A2A Bridge")

# Directory for storing agent information and communication logs
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_a2a_bridge"
AGENT_REGISTRY_DIR = DATA_DIR / "agent_registry"
LOGS_DIR = DATA_DIR / "logs"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
AGENT_REGISTRY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# A2A Agent Card file (JSON descriptor of this agent's capabilities)
AGENT_CARD_PATH = DATA_DIR / "agent_card.json"


class AgentType(str, Enum):
    """Types of agents this bridge can communicate with"""

    RESEARCH = "research"
    CODING = "coding"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"


@dataclass
class AgentInfo:
    """Information about a registered agent"""

    id: str
    name: str
    agent_type: AgentType
    endpoint: str
    description: str
    capabilities: List[str]
    api_key: Optional[str] = None
    last_active: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# In-memory storage for registered agents
registered_agents: Dict[str, AgentInfo] = {}

# In-memory conversation history
conversation_history: Dict[str, List[Dict[str, Any]]] = {}


def load_agents_from_disk() -> None:
    """Load registered agents from disk"""
    for agent_file in AGENT_REGISTRY_DIR.glob("*.json"):
        try:
            with open(agent_file, "r") as f:
                agent_data = json.load(f)
                agent_id = agent_file.stem

                agent_info = AgentInfo(
                    id=agent_id,
                    name=agent_data["name"],
                    agent_type=AgentType(agent_data["agent_type"]),
                    endpoint=agent_data["endpoint"],
                    description=agent_data["description"],
                    capabilities=agent_data["capabilities"],
                    api_key=agent_data.get("api_key"),
                    last_active=agent_data.get("last_active"),
                    metadata=agent_data.get("metadata", {}),
                )

                registered_agents[agent_id] = agent_info
        except Exception as e:
            print(f"Error loading agent {agent_file}: {e}")


def save_agent_to_disk(agent: AgentInfo) -> None:
    """Save agent information to disk"""
    agent_file = AGENT_REGISTRY_DIR / f"{agent.id}.json"

    agent_data = {
        "name": agent.name,
        "agent_type": agent.agent_type,
        "endpoint": agent.endpoint,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "api_key": agent.api_key,
        "last_active": agent.last_active,
        "metadata": agent.metadata,
    }

    with open(agent_file, "w") as f:
        json.dump(agent_data, f, indent=2)


def create_agent_card() -> Dict[str, Any]:
    """Create an A2A Agent Card for this bridge agent"""
    agent_card = {
        "schemaVersion": "1.0.0",
        "name": "MCP-A2A Bridge",
        "description": "A bridge agent that connects MCP tools with other A2A agents",
        "capabilities": ["task-delegation", "information-retrieval", "collaboration"],
        "contact": {
            "name": "MCP-A2A Bridge Administrator",
            "email": "admin@example.com",
        },
        "endpoints": {
            "textExchange": {
                "url": "http://localhost:8000/a2a/text",
                "contentType": "application/json",
                "authentication": {"type": "api_key", "headerName": "X-API-Key"},
            },
            "discovery": {
                "url": "http://localhost:8000/a2a/discover",
                "contentType": "application/json",
            },
        },
        "authentication": {"type": "api_key", "headerName": "X-API-Key"},
    }

    with open(AGENT_CARD_PATH, "w") as f:
        json.dump(agent_card, f, indent=2)

    return agent_card


# Initialize by loading agents and creating agent card
load_agents_from_disk()
create_agent_card()


# A2A Communication Functions
async def send_message_to_agent(agent_id: str, message: str) -> Dict[str, Any]:
    """Send a message to another agent using the A2A protocol"""
    if agent_id not in registered_agents:
        return {"error": f"Agent with ID {agent_id} not found"}

    agent = registered_agents[agent_id]

    # Create a unique conversation ID if not already in history
    if agent_id not in conversation_history:
        conversation_id = str(uuid.uuid4())
        conversation_history[agent_id] = []
    else:
        # Use existing conversation
        conversation_id = conversation_history[agent_id][0].get(
            "conversation_id", str(uuid.uuid4())
        )

    # A2A protocol message format
    a2a_message = {
        "message": message,
        "conversation_id": conversation_id,
        "sender": {"name": "MCP-A2A Bridge", "id": "mcp-a2a-bridge"},
        "timestamp": time.time(),
    }

    headers = {}
    if agent.api_key:
        headers["X-API-Key"] = agent.api_key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                agent.endpoint, json=a2a_message, headers=headers, timeout=30.0
            )

            if response.status_code == 200:
                response_data = response.json()

                # Store conversation history
                conversation_history.setdefault(agent_id, []).append(
                    {
                        "conversation_id": conversation_id,
                        "timestamp": time.time(),
                        "message": message,
                        "response": response_data.get("message", ""),
                        "metadata": response_data.get("metadata", {}),
                    }
                )

                # Update agent's last_active timestamp
                agent.last_active = time.time()
                save_agent_to_disk(agent)

                return response_data
            else:
                error_msg = f"Error communicating with agent: {response.status_code} - {response.text}"
                return {"error": error_msg}
    except Exception as e:
        return {"error": f"Communication error: {str(e)}"}


async def discover_agent_capabilities(
    endpoint: str, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Discover another agent's capabilities using A2A discovery endpoint"""
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, headers=headers, timeout=10.0)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Discovery failed: {response.status_code} - {response.text}"
                }
    except Exception as e:
        return {"error": f"Discovery error: {str(e)}"}


# MCP Tools for Agent Registry
@mcp.tool()
def list_registered_agents() -> str:
    """List all registered A2A agents"""
    if not registered_agents:
        return "No agents registered."

    agents_list = []
    for agent_id, agent in registered_agents.items():
        agents_list.append(
            {
                "id": agent_id,
                "name": agent.name,
                "type": agent.agent_type,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "last_active": agent.last_active,
            }
        )

    return json.dumps(agents_list, indent=2)


@mcp.tool()
def register_agent(
    name: str,
    agent_type: str,
    endpoint: str,
    description: str,
    capabilities: List[str],
    api_key: Optional[str] = None,
) -> str:
    """
    Register a new A2A agent

    Args:
        name: Agent name
        agent_type: Type of agent (research, coding, data_analysis, general)
        endpoint: A2A endpoint URL
        description: Brief description of the agent's purpose
        capabilities: List of capabilities the agent provides
        api_key: Optional API key for authentication
    """
    # Validate agent type
    try:
        validated_type = AgentType(agent_type)
    except ValueError:
        valid_types = [t.value for t in AgentType]
        return f"Error: Invalid agent type. Choose from: {', '.join(valid_types)}"

    # Generate unique ID
    agent_id = str(uuid.uuid4())[:8]

    # Create agent info
    agent = AgentInfo(
        id=agent_id,
        name=name,
        agent_type=validated_type,
        endpoint=endpoint,
        description=description,
        capabilities=capabilities,
        api_key=api_key,
        last_active=time.time(),
    )

    # Save to registry
    registered_agents[agent_id] = agent
    save_agent_to_disk(agent)

    return json.dumps(
        {"message": f"Agent '{name}' registered successfully", "agent_id": agent_id},
        indent=2,
    )


@mcp.tool()
def get_agent_details(agent_id: str) -> str:
    """
    Get detailed information about a registered agent

    Args:
        agent_id: ID of the agent to retrieve
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    agent = registered_agents[agent_id]

    # Include conversation history if available
    conversation = conversation_history.get(agent_id, [])

    return json.dumps(
        {
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type,
            "endpoint": agent.endpoint,
            "description": agent.description,
            "capabilities": agent.capabilities,
            "last_active": agent.last_active,
            "metadata": agent.metadata,
            "conversations": len(conversation),
        },
        indent=2,
    )


# MCP Tools for A2A Communication
@mcp.tool()
async def send_query_to_agent(agent_id: str, query: str) -> str:
    """
    Send a query to another agent using A2A protocol

    Args:
        agent_id: ID of the agent to query
        query: The question or instruction to send
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    response = await send_message_to_agent(agent_id, query)

    if "error" in response:
        return f"Error: {response['error']}"

    result = {
        "agent": registered_agents[agent_id].name,
        "response": response.get("message", ""),
        "metadata": response.get("metadata", {}),
    }

    return json.dumps(result, indent=2)


@mcp.tool()
async def discover_and_register_agent(
    discovery_endpoint: str, api_key: Optional[str] = None
) -> str:
    """
    Discover and register an agent using its A2A discovery endpoint

    Args:
        discovery_endpoint: URL of the agent's discovery endpoint
        api_key: Optional API key for authentication
    """
    # Discover agent capabilities
    discovery_result = await discover_agent_capabilities(discovery_endpoint, api_key)

    if "error" in discovery_result:
        return f"Error: {discovery_result['error']}"

    # Extract agent information from discovery response
    try:
        agent_card = discovery_result.get("agent_card", discovery_result)

        # Determine the messaging endpoint
        endpoint = None
        if "endpoints" in agent_card:
            if "textExchange" in agent_card["endpoints"]:
                endpoint = agent_card["endpoints"]["textExchange"]["url"]

        if not endpoint:
            return "Error: Could not determine the agent's messaging endpoint"

        # Extract capabilities
        capabilities = agent_card.get("capabilities", [])

        # Register the agent
        agent_name = agent_card.get("name", "Unknown Agent")
        agent_description = agent_card.get("description", "No description available")

        # Determine agent type based on capabilities
        agent_type = AgentType.GENERAL.value
        if "research" in " ".join(capabilities).lower():
            agent_type = AgentType.RESEARCH.value
        elif (
            "code" in " ".join(capabilities).lower()
            or "programming" in " ".join(capabilities).lower()
        ):
            agent_type = AgentType.CODING.value
        elif (
            "data" in " ".join(capabilities).lower()
            or "analysis" in " ".join(capabilities).lower()
        ):
            agent_type = AgentType.DATA_ANALYSIS.value

        # Generate agent ID
        agent_id = str(uuid.uuid4())[:8]

        # Create agent info
        agent = AgentInfo(
            id=agent_id,
            name=agent_name,
            agent_type=AgentType(agent_type),
            endpoint=endpoint,
            description=agent_description,
            capabilities=capabilities,
            api_key=api_key,
            last_active=time.time(),
            metadata={"agent_card": agent_card},
        )

        # Save to registry
        registered_agents[agent_id] = agent
        save_agent_to_disk(agent)

        return json.dumps(
            {
                "message": f"Agent '{agent_name}' discovered and registered successfully",
                "agent_id": agent_id,
                "capabilities": capabilities,
                "endpoint": endpoint,
            },
            indent=2,
        )

    except Exception as e:
        return f"Error processing discovery response: {str(e)}"


@mcp.tool()
async def delegate_task_to_agent(
    agent_id: str, task: str, context: Optional[str] = None
) -> str:
    """
    Delegate a task to another agent with optional context

    Args:
        agent_id: ID of the agent to delegate to
        task: The task description or instruction
        context: Optional context information to help the agent
    """
    if agent_id not in registered_agents:
        return f"Error: Agent with ID {agent_id} not found"

    # Format the message with context if provided
    if context:
        message = f"Task: {task}\n\nContext: {context}"
    else:
        message = f"Task: {task}"

    response = await send_message_to_agent(agent_id, message)

    if "error" in response:
        return f"Error delegating task: {response['error']}"

    result = {
        "agent": registered_agents[agent_id].name,
        "task": task,
        "response": response.get("message", ""),
        "metadata": response.get("metadata", {}),
    }

    return json.dumps(result, indent=2)


# MCP Resources
@mcp.resource("a2a://agents")
def get_agents_resource() -> str:
    """Get a list of all registered A2A agents"""
    agents_list = []
    for agent_id, agent in registered_agents.items():
        agents_list.append(
            {
                "id": agent_id,
                "name": agent.name,
                "type": agent.agent_type,
                "description": agent.description,
                "capabilities": agent.capabilities,
            }
        )

    return json.dumps(agents_list, indent=2)


@mcp.resource("a2a://agent/{agent_id}")
def get_agent_resource(agent_id: str) -> str:
    """Get details about a specific agent"""
    if agent_id not in registered_agents:
        return json.dumps({"error": f"Agent with ID {agent_id} not found"})

    agent = registered_agents[agent_id]

    return json.dumps(
        {
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type,
            "description": agent.description,
            "capabilities": agent.capabilities,
            "last_active": agent.last_active,
        },
        indent=2,
    )


@mcp.resource("a2a://conversations/{agent_id}")
def get_conversation_history_resource(agent_id: str) -> str:
    """Get conversation history with a specific agent"""
    if agent_id not in registered_agents:
        return json.dumps({"error": f"Agent with ID {agent_id} not found"})

    if agent_id not in conversation_history or not conversation_history[agent_id]:
        return json.dumps({"message": f"No conversation history with agent {agent_id}"})

    # Format conversation for readability
    formatted_history = []
    for entry in conversation_history[agent_id]:
        formatted_history.append(
            {
                "timestamp": entry["timestamp"],
                "message": entry["message"],
                "response": entry["response"],
            }
        )

    return json.dumps(formatted_history, indent=2)


# Enhanced Prompts
@mcp.prompt()
def agent_delegation_prompt(
    task: str, agent_type: Optional[str] = None
) -> List[Message]:
    """Generate a structured prompt for delegating a task to an appropriate agent"""

    system_message = "You are a task delegation assistant that helps format tasks for other AI agents."

    if agent_type:
        user_message = f"""I need to delegate the following task to a {agent_type} agent:

Task: {task}

Please help me format this task in a clear, structured way that a {agent_type} agent would understand.
Include any relevant instructions, constraints, and expected output format.
"""
    else:
        user_message = f"""I need to delegate the following task to another AI agent:

Task: {task}

Please help me format this task in a clear, structured way that would be appropriate for an agent to process.
Include any relevant instructions, constraints, and expected output format.
"""

    return [SystemMessage(system_message), UserMessage(user_message)]


@mcp.prompt()
def agent_collaboration_prompt(task: str, agents: List[str]) -> List[Message]:
    """Generate a prompt for orchestrating collaboration between multiple agents"""

    agents_str = ", ".join(agents)

    return [
        SystemMessage(
            "You are a collaboration coordinator specializing in multi-agent task orchestration."
        ),
        UserMessage(f"""I need to coordinate the following task across multiple agents: {agents_str}

Task: {task}

Please help me:
1. Break down this task into components suitable for each agent
2. Suggest a workflow for how these agents should collaborate
3. Define what each agent should contribute
4. Identify any potential coordination challenges

This will help me effectively delegate work across these specialized agents."""),
    ]
