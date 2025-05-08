import getpass
import json
import os
import subprocess
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# Handle potential getlogin issues
os.getlogin = getpass.getuser

from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, TextContent

# Initialize MCP server for developer onboarding
mcp = FastMCP("Developer Onboarding")

# Directory for storing onboarding data
DATA_DIR = Path(os.path.expanduser("~")) / "mcp_onboarding"
REPOS_DIR = DATA_DIR / "repos"
ENV_DIR = DATA_DIR / "environments"
DOCS_DIR = DATA_DIR / "documentation"
GUIDES_DIR = DATA_DIR / "guides"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
REPOS_DIR.mkdir(exist_ok=True)
ENV_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
GUIDES_DIR.mkdir(exist_ok=True)


# Define environment types
class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# Define repository types
class RepoType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    MICROSERVICE = "microservice"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"


# Helper function to safely run commands
def run_command(command: List[str], cwd: Optional[str] = None) -> tuple:
    """Run a shell command and return stdout, stderr and return code"""
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
        )
        stdout, stderr = process.communicate(timeout=60)
        return stdout, stderr, process.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 60 seconds", 1
    except Exception as e:
        return "", f"Error executing command: {str(e)}", 1


# MCP Tool: Setup developer environment
@mcp.tool()
def setup_environment(
    env_name: str, env_type: str = "development", technologies: List[str] = None
) -> str:
    """
    Set up a developer environment with required tools and configurations

    Args:
        env_name: Name for the environment
        env_type: Type of environment (development, staging, production, testing)
        technologies: List of technologies to install (e.g., python, node, docker)

    Returns:
        Summary of environment setup
    """
    # Validate environment type
    try:
        env_type_enum = EnvironmentType(env_type)
    except ValueError:
        return f"Invalid environment type: {env_type}. Valid options are: {', '.join([t.value for t in EnvironmentType])}"

    # Use default technologies if none provided
    if not technologies:
        technologies = ["git", "python", "node"]

    # Create environment directory
    env_dir = ENV_DIR / env_name
    env_dir.mkdir(exist_ok=True)

    # Track setup process
    setup_log = []
    setup_log.append(f"Setting up {env_type} environment: {env_name}")
    setup_log.append(f"Timestamp: {datetime.now().isoformat()}")
    setup_log.append(f"Technologies: {', '.join(technologies)}")
    setup_log.append("\nInstallation log:")

    # Check and install required technologies
    for tech in technologies:
        setup_log.append(f"\nChecking {tech}...")

        # Check if technology is already installed
        check_cmd = []
        if tech == "git":
            check_cmd = ["git", "--version"]
        elif tech == "python":
            check_cmd = ["python", "--version"]
        elif tech == "node":
            check_cmd = ["node", "--version"]
        elif tech == "docker":
            check_cmd = ["docker", "--version"]
        elif tech == "java":
            check_cmd = ["java", "--version"]

        if check_cmd:
            stdout, stderr, return_code = run_command(check_cmd)

            if return_code == 0:
                setup_log.append(f"✓ {tech} is already installed: {stdout.strip()}")
                continue
            else:
                setup_log.append(f"✗ {tech} not found, installation required")

        # Simulate installation (in a real implementation, this would actually install the software)
        setup_log.append(f"Installing {tech}...")
        time.sleep(1)  # Simulate installation time
        setup_log.append(f"✓ {tech} installed successfully")

    # Create environment configuration file
    config = {
        "name": env_name,
        "type": env_type,
        "created_at": datetime.now().isoformat(),
        "technologies": technologies,
        "ready": True,
    }

    with open(env_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    setup_log.append("\nEnvironment setup completed successfully!")
    setup_log.append(f"Configuration saved to: {env_dir / 'config.json'}")

    return "\n".join(setup_log)


# MCP Tool: Clone repositories
@mcp.tool()
def clone_repositories(
    repos: List[Dict[str, str]], target_dir: Optional[str] = None
) -> str:
    """
    Clone multiple repositories for a new developer

    Args:
        repos: List of repository objects with 'url' and 'name' fields
        target_dir: Optional target directory (defaults to ~/mcp_onboarding/repos)

    Returns:
        Summary of cloning operations
    """
    # Use default directory if not specified
    if target_dir:
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True, parents=True)
    else:
        target_path = REPOS_DIR

    # Clone each repository
    results = []
    results.append(f"Cloning {len(repos)} repositories to {target_path}...")

    successful = 0
    failed = 0

    for repo in repos:
        if "url" not in repo or "name" not in repo:
            results.append(
                f"Error: Repository must have 'url' and 'name' fields: {repo}"
            )
            failed += 1
            continue

        url = repo["url"]
        name = repo["name"]
        repo_path = target_path / name

        results.append(f"\nCloning {name} from {url}...")

        if repo_path.exists():
            results.append(f"✓ Repository {name} already exists at {repo_path}")
            successful += 1
            continue

        # In a real implementation, this would actually clone the repo
        # Here we simulate successful cloning
        time.sleep(1)  # Simulate clone time
        repo_path.mkdir(exist_ok=True)

        # Create a placeholder file to simulate successful clone
        with open(repo_path / "README.md", "w") as f:
            f.write(
                f"# {name}\n\nThis is a simulated repository for demonstration purposes."
            )

        results.append(f"✓ Repository {name} cloned successfully to {repo_path}")
        successful += 1

    results.append(f"\nCloning completed: {successful} successful, {failed} failed")

    return "\n".join(results)


# MCP Tool: Generate onboarding guide
@mcp.tool()
def generate_onboarding_guide(
    developer_name: str,
    role: str,
    team: str,
    repositories: List[str] = None,
    technologies: List[str] = None,
) -> str:
    """
    Generate a personalized onboarding guide for a new developer

    Args:
        developer_name: Name of the new developer
        role: Developer's role (e.g., Frontend, Backend, Full Stack)
        team: Team the developer is joining
        repositories: List of repositories the developer will work with
        technologies: List of technologies the developer should learn

    Returns:
        Personalized onboarding guide
    """
    # Use default values if not provided
    if not repositories:
        repositories = ["main-app", "api-service", "documentation"]

    if not technologies:
        technologies = ["git", "python", "node"]

    # Create guide
    guide_id = f"guide_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    guide_path = GUIDES_DIR / f"{guide_id}.md"

    guide_content = []
    guide_content.append(f"# Onboarding Guide for {developer_name}")
    guide_content.append(f"## {role} on {team} Team")
    guide_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d')}")

    guide_content.append("\n## Welcome!")
    guide_content.append(
        f"Welcome to the team, {developer_name}! This guide will help you get started in your role as a {role} on the {team} team."
    )

    guide_content.append("\n## First Week Checklist")
    guide_content.append("- [ ] Setup development environment")
    guide_content.append("- [ ] Clone repositories")
    guide_content.append("- [ ] Review architecture documentation")
    guide_content.append("- [ ] Meet with team members")
    guide_content.append("- [ ] Complete security training")
    guide_content.append("- [ ] Submit first PR")

    guide_content.append("\n## Key Repositories")
    for repo in repositories:
        guide_content.append(f"- **{repo}**: `git clone [repo-url]/{repo}.git`")

    guide_content.append("\n## Required Technologies")
    for tech in technologies:
        guide_content.append(
            f"- **{tech}**: [Installation Guide](https://docs.example.com/{tech}/install)"
        )

    guide_content.append("\n## Team Information")
    guide_content.append(f"- **Team**: {team}")
    guide_content.append("- **Meetings**: Daily standup at 10:00 AM")
    guide_content.append("- **Sprint Cycle**: 2 weeks")
    guide_content.append(
        "- **Documentation**: [Team Wiki](https://wiki.example.com/teams/{team})"
    )

    guide_content.append("\n## Getting Help")
    guide_content.append("- Technical questions: Ask in the #dev-help channel")
    guide_content.append("- HR/Onboarding: Contact onboarding@example.com")
    guide_content.append("- IT Support: Submit a ticket to help@example.com")

    guide_content.append("\n## Next Steps")
    guide_content.append(
        "1. Set up your development environment using `setup_environment` tool"
    )
    guide_content.append(
        "2. Clone the repositories listed above using `clone_repositories` tool"
    )
    guide_content.append("3. Start with small tasks labeled 'good-first-issue'")
    guide_content.append("4. Schedule 1:1s with team members")

    # Write guide to file
    with open(guide_path, "w") as f:
        f.write("\n".join(guide_content))

    return "\n".join(guide_content)


# MCP Tool: Configure IDE settings
@mcp.tool()
def configure_ide(ide: str, settings: Dict[str, any] = None) -> str:
    """
    Configure IDE settings according to team standards

    Args:
        ide: IDE to configure (e.g., vscode, intellij, pycharm)
        settings: Dictionary of settings to configure (optional)

    Returns:
        Summary of IDE configuration
    """
    # Default settings if none provided
    if not settings:
        settings = {
            "editor.formatOnSave": True,
            "editor.tabSize": 2,
            "files.insertFinalNewline": True,
            "files.trimTrailingWhitespace": True,
        }

    # Create IDE settings directory
    ide_dir = ENV_DIR / "ide_settings" / ide
    ide_dir.mkdir(exist_ok=True, parents=True)

    # Generate settings file
    if ide.lower() == "vscode":
        settings_file = ide_dir / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
    elif ide.lower() in ["intellij", "pycharm"]:
        settings_file = ide_dir / "settings.xml"
        # Simplified XML for demonstration purposes
        xml_content = "<settings>\n"
        for key, value in settings.items():
            xml_content += f"  <{key}>{value}</{key}>\n"
        xml_content += "</settings>"

        with open(settings_file, "w") as f:
            f.write(xml_content)
    else:
        return f"Unsupported IDE: {ide}. Supported IDEs are: vscode, intellij, pycharm"

    # Create instructions file
    instructions_file = ide_dir / "README.md"
    instructions = [
        f"# {ide.upper()} Configuration",
        "",
        "## Installation",
        f"1. Install {ide}",
        "2. Apply these settings for team consistency",
        "",
        "## Settings",
        "Copy these settings to your IDE configuration:",
        "",
        "```",
        json.dumps(settings, indent=2) if ide.lower() == "vscode" else xml_content,
        "```",
        "",
        "## Extensions/Plugins",
        "- ESLint",
        "- Prettier",
        "- GitLens",
        "- Code Spell Checker",
    ]

    with open(instructions_file, "w") as f:
        f.write("\n".join(instructions))

    return f"""
IDE configuration for {ide} created successfully!

Settings file: {settings_file}
Instructions: {instructions_file}

Key settings:
{json.dumps(settings, indent=2)}

To apply these settings:
1. Open your {ide}
2. Import the settings file
3. Install recommended extensions/plugins
"""


# MCP Tool: Create first task
@mcp.tool()
def create_first_task(
    developer_name: str, task_type: str = "documentation", repo: str = None
) -> str:
    """
    Create a first task for a new developer

    Args:
        developer_name: Name of the new developer
        task_type: Type of task (documentation, bug-fix, feature, test)
        repo: Name of the repository for the task

    Returns:
        Task description and instructions
    """
    # Default repository if not provided
    if not repo:
        repo = "main-app"

    # Create task based on type
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if task_type == "documentation":
        task = {
            "id": task_id,
            "title": "Update README with setup instructions",
            "description": f"Add detailed setup instructions to the {repo} README.md file",
            "complexity": "Low",
            "estimated_time": "1-2 hours",
            "steps": [
                f"Clone the {repo} repository",
                "Review existing README.md",
                "Add installation instructions",
                "Add configuration details",
                "Add troubleshooting section",
                "Create pull request",
            ],
        }
    elif task_type == "bug-fix":
        task = {
            "id": task_id,
            "title": "Fix logger initialization error",
            "description": f"Fix the logger initialization error in {repo} that occurs on startup",
            "complexity": "Low",
            "estimated_time": "2-3 hours",
            "steps": [
                f"Clone the {repo} repository",
                "Reproduce the error locally",
                "Debug logger initialization process",
                "Implement fix",
                "Add unit test",
                "Create pull request",
            ],
        }
    elif task_type == "feature":
        task = {
            "id": task_id,
            "title": "Add user preference toggle",
            "description": f"Add a user preference toggle for theme selection in {repo}",
            "complexity": "Medium",
            "estimated_time": "4-6 hours",
            "steps": [
                f"Clone the {repo} repository",
                "Locate user preference component",
                "Add theme toggle feature",
                "Implement theme change functionality",
                "Add unit and integration tests",
                "Update documentation",
                "Create pull request",
            ],
        }
    elif task_type == "test":
        task = {
            "id": task_id,
            "title": "Add tests for authentication module",
            "description": f"Increase test coverage for the authentication module in {repo}",
            "complexity": "Medium",
            "estimated_time": "3-4 hours",
            "steps": [
                f"Clone the {repo} repository",
                "Review existing tests",
                "Identify missing test cases",
                "Implement unit tests",
                "Implement integration tests",
                "Update test documentation",
                "Create pull request",
            ],
        }
    else:
        return f"Invalid task type: {task_type}. Valid types are: documentation, bug-fix, feature, test"

    # Save task
    task_dir = REPOS_DIR / repo
    task_dir.mkdir(exist_ok=True, parents=True)

    with open(task_dir / f"{task_id}.json", "w") as f:
        json.dump(task, f, indent=2)

    # Create formatted task description
    task_description = [
        f"# First Task: {task['title']}",
        "",
        f"**Task ID**: {task['id']}",
        f"**Repository**: {repo}",
        f"**Assigned to**: {developer_name}",
        f"**Complexity**: {task['complexity']}",
        f"**Estimated Time**: {task['estimated_time']}",
        "",
        "## Description",
        task["description"],
        "",
        "## Steps",
        "\n".join([f"1. {step}" for step in task["steps"]]),
        "",
        "## Pull Request Guidelines",
        "- Create a branch with format: `{developer_name.lower().replace(' ', '-')}/{task_type}/{task_id}`",
        "- Keep changes focused on the task scope",
        "- Include tests for your changes",
        "- Update relevant documentation",
        "- Request review from your mentor",
        "",
        "## Resources",
        f"- Repository: {repo}",
        "- Documentation: https://docs.example.com/",
        "- Team channel: #team-help",
    ]

    return "\n".join(task_description)


# MCP Tool: Generate project architecture diagram
@mcp.tool()
def generate_architecture_diagram(project_name: str) -> str:
    """
    Generate a text-based architecture diagram for a project

    Args:
        project_name: Name of the project

    Returns:
        Text-based architecture diagram
    """
    # Create a simplified architecture diagram
    diagram = f"""
# {project_name} Architecture

```
┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │
│  Frontend App   │◄────►│    API Gateway  │
│                 │      │                 │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │
│  Auth Service   │◄────►│ Business Logic  │
│                 │      │    Service      │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │
│  User Database  │      │  Data Storage   │
│                 │      │                 │
└─────────────────┘      └─────────────────┘
```

## Component Descriptions

### Frontend App
- User interface built with React/Vue
- Communicates with backend via API Gateway
- Handles user interactions and data display

### API Gateway
- Routes requests to appropriate microservices
- Handles authentication/authorization
- Implements rate limiting and request validation

### Auth Service
- Manages user authentication
- Issues and validates JWT tokens
- Integrates with identity providers

### Business Logic Service
- Implements core business rules
- Processes data and transactions
- Communicates with data storage

### User Database
- Stores user profiles and credentials
- Secured with encryption and access controls

### Data Storage
- Persistent storage for application data
- Implements backup and recovery mechanisms
- Optimized for read/write patterns
"""

    # Save the diagram
    docs_dir = DOCS_DIR / project_name
    docs_dir.mkdir(exist_ok=True, parents=True)

    diagram_path = docs_dir / "architecture.md"
    with open(diagram_path, "w") as f:
        f.write(diagram)

    return diagram


# MCP Resource: Get available environments
@mcp.resource("onboarding://environments")
def get_environments() -> str:
    """Get list of available development environments"""
    environments = []

    for env_dir in ENV_DIR.glob("*"):
        config_file = env_dir / "config.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                environments.append(config)

    return json.dumps(environments, indent=2)


# MCP Resource: Get onboarding guide template
@mcp.resource("onboarding://guide_template")
def get_guide_template() -> str:
    """Get template for onboarding guides"""
    template = {
        "sections": [
            {"title": "Welcome", "required": True},
            {"title": "First Week Checklist", "required": True},
            {"title": "Key Repositories", "required": True},
            {"title": "Required Technologies", "required": True},
            {"title": "Team Information", "required": True},
            {"title": "Getting Help", "required": True},
            {"title": "Next Steps", "required": True},
            {"title": "Company Policies", "required": False},
            {"title": "FAQ", "required": False},
        ],
        "placeholders": [
            "{developer_name}",
            "{role}",
            "{team}",
            "{repositories}",
            "{technologies}",
        ],
    }
    return json.dumps(template, indent=2)


# MCP Prompt for developer introduction
@mcp.prompt()
def developer_introduction_prompt(
    developer_name: str, role: str, team: str, experience_level: str
) -> List[SamplingMessage]:
    """
    Generate a prompt for creating a developer introduction message

    Args:
        developer_name: Name of the new developer
        role: Developer's role (e.g., Frontend, Backend, Full Stack)
        team: Team the developer is joining
        experience_level: Developer's experience level
    """
    system_prompt = """
    You are an Onboarding Specialist responsible for welcoming new developers to the team.
    Create a personalized, friendly introduction message that helps the new team member feel welcome.
    Include practical next steps and offer support for their onboarding journey.
    """

    user_content = f"""
    Please create an introduction message for a new developer joining our team with the following details:
    
    - Name: {developer_name}
    - Role: {role}
    - Team: {team}
    - Experience Level: {experience_level}
    
    The message should:
    1. Welcome them to the team
    2. Briefly explain what the team does
    3. Outline their first week expectations
    4. Introduce key team members
    5. Provide resources they should check out
    6. Offer support channels for questions
    
    Keep the tone friendly, supportive, and encouraging. The message will be posted in our team channel.
    """

    return [
        SamplingMessage(role="system", content=TextContent(text=system_prompt)),
        SamplingMessage(role="user", content=TextContent(text=user_content)),
    ]
