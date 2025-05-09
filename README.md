# Model Context Protocol (MCP) Samples

This repository contains comprehensive examples of how to use the Model Context Protocol (MCP) for building intelligent agent applications.

## Overview

Model Context Protocol (MCP) is a protocol for connecting large language models (LLMs) to tools, enabling agents to interact with external systems. This repository demonstrates various MCP implementations from basic to advanced use cases.

## Getting Started

1. Clone this repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment: 
   - Linux/Mac: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. Install dependencies: `pip install -e .`

## Example Structure

The examples are organized by complexity, starting with basic implementations and progressing to advanced use cases:

### Basic Examples (01-10)
- Simple tool implementations
- Math operations
- Dynamic resources
- Prompt handling
- External API integration
- Stateful resources
- Asynchronous operations
- Error handling
- Multi-tool usage
- Advanced prompting techniques

### Intermediate Examples (11-30)
- Tool composition
- File operations
- Database integration
- API integration
- Complex data models
- Client usage
- Security and authentication
- Machine learning integration
- LLM sampling
- Complete application integration
- Agent-to-agent communication
- Websockets
- Telemetry
- OAuth implementation
- Multimodal tools
- SSE progress reporting
- Redis pub/sub
- File operations
- FastAPI integration

### Advanced Examples (31-65)
- Integration with various systems (GitHub, pandas, Docker, messaging platforms)
- PDF extraction
- Task scheduling
- Environment variable management
- Protocol inspection
- Session lifecycle management
- Capability negotiation
- Custom transports
- Client implementations
- Notification systems
- Sampling mechanisms
- Progress tracking
- Authorization flows
- Resource management
- Schema validation
- Protocol extensions
- Cross-server communication
- Persistence and caching
- Compliance automation
- Developer tooling
- Debugging tools
- Legacy system migration
- Browser automation
- Environmental data analysis
- Document analysis

### API Governance Suite (66-75)
- API discovery tools
- Context helpers
- Error analyzers
- Test runners
- Contract validators
- API-to-MCP transformers
- Security auditing
- Monitoring and alerts
- Versioning management

### Showcase Demos (76-77)
- **MCP DevOps Platform Demo (76 & mcp-platform-demo/)**: A comprehensive demo showcasing MCP in a DevOps environment, featuring intelligent API creation and governance, infrastructure management, problem investigation, and chaos engineering.
- **AI Code Companion (77)**: VSCode integration for AI-powered code generation, intelligent code review, and contextual debugging assistance.

## MCP DevOps Platform Demo

The `mcp-platform-demo/` directory contains a complete DevOps platform powered by MCP, allowing AI agents to perform complex DevOps tasks through natural language interaction.

To run the demo:
1. Navigate to the demo directory: `cd mcp-platform-demo`
2. Run the start script: `./start-demo.sh`
3. Access the dashboard at http://localhost:3001
4. Run the demo script: `python ../76-mcp-devops-platform-demo.py`

For more details, see the [platform README](mcp-platform-demo/README.md).

## AI Code Companion Demo

The AI Code Companion demonstrates how MCP can enhance VSCode and Copilot to provide more powerful AI-assisted development:

1. Run the interactive demo: `python 77-mcp-copilot-code-companion.py`
2. Explore the MCP server implementation in `mcp-platform-demo/mcp-servers/code_companion.py`
3. View the [VSCode Extension Documentation](mcp-platform-demo/VSCodeMCPExtension.md) and [Visual Demo](mcp-platform-demo/VSCodeMCPScreenshot.md)

Key features include:
- Smart code generation with contextual awareness
- Intelligent code review with security and quality checks
- AI-powered debugging assistance
- Architecture and design recommendations

## Documentation

For more information about MCP:
- [MCP Documentation](https://modelcontextprotocol.io)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol/modelcontextprotocol)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
