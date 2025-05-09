# VSCode MCP Extension: AI Code Companion

## Overview

The VSCode MCP Extension connects the Model Context Protocol (MCP) to Visual Studio Code, enabling intelligent code generation, analysis, and debugging powered by large language models (LLMs) with access to your local development environment.

This document describes how to integrate the MCP DevOps Platform's AI Code Companion with VSCode.

## Features

### 1. Smart Code Generation

Generate high-quality code with full context awareness:

- **Code Templates**: Generate complete files like controllers, models, and tests
- **Function Implementation**: Complete function bodies based on signatures and docstrings
- **Type Annotations**: Add type hints to existing code
- **Documentation**: Generate docstrings and comments

### 2. Intelligent Code Review

Automated code quality feedback:

- **Issue Detection**: Identify bugs, security vulnerabilities, and code smells
- **Best Practices**: Suggestions for following language-specific best practices
- **Performance**: Identify potential performance bottlenecks
- **Style Enforcement**: Ensure code follows project conventions

### 3. Contextual Debugging

AI-powered debugging assistance:

- **Error Analysis**: Understand error messages and stack traces
- **Fix Suggestions**: Get suggested solutions for common errors
- **Debugging Strategies**: Recommendations for investigating complex issues
- **Root Cause Analysis**: Identify underlying issues causing bugs

### 4. Architecture Assistance

Get help with design decisions:

- **Pattern Suggestions**: Recommend appropriate design patterns
- **Architecture Reviews**: Evaluate architectural choices
- **Refactoring Plans**: Create step-by-step refactoring strategies
- **Technology Selection**: Get contextual advice on libraries and frameworks

## Setup

### Prerequisites

- Visual Studio Code (1.60+)
- MCP DevOps Platform running locally (via start-demo.sh)
- VSCode Copilot extension installed

### Installation

1. Install the VSCode MCP Extension:
   ```
   ext install mcp-code-companion
   ```

2. Configure the extension to connect to the MCP DevOps Platform:
   ```json
   {
     "mcp.codeCompanion.serverUrl": "http://localhost:8888",
     "mcp.codeCompanion.enabled": true,
     "mcp.codeCompanion.enableInlineActions": true
   }
   ```

3. Restart VSCode to apply the changes

## Usage Examples

### Code Generation

1. Select a section of code or place your cursor where you want to generate code
2. Open the command palette (Ctrl+Shift+P / Cmd+Shift+P)
3. Type "MCP: Generate Code" and select the command
4. Describe what you want to generate in natural language
5. Review and accept the generated code

Example prompts:
- "Generate a SQLAlchemy model for users table with fields for username, email, and password"
- "Create a unit test for the auth_service.verify_token function"
- "Implement a REST API endpoint for user authentication using FastAPI"

### Code Review

1. Open a file you want to review
2. Open the command palette
3. Type "MCP: Review Code" and select the command
4. Wait for the analysis to complete
5. Review findings in the "MCP Code Companion" panel

The extension will identify:
- Security vulnerabilities
- Code quality issues
- Performance concerns
- Style violations
- Potential bugs

### Debugging Assistance

1. When you encounter an error, select the error message
2. Right-click and select "MCP: Debug Error"
3. The extension will analyze the error and suggest potential fixes
4. Apply the suggested fix directly or use it as guidance

## Integration with Copilot

When using the MCP Code Companion alongside GitHub Copilot:

1. Copilot provides inline suggestions during coding
2. MCP Code Companion augments these with deeper contextual understanding
3. Use Copilot for quick completions and MCP for more complex operations
4. MCP can access your local environment, run tools, and provide project-specific help

## Advanced Configuration

Fine-tune the extension behavior:

```json
{
  "mcp.codeCompanion.reviewOnSave": true,
  "mcp.codeCompanion.inlineDebugSuggestions": true,
  "mcp.codeCompanion.enabledLanguages": ["python", "javascript", "typescript", "java"],
  "mcp.codeCompanion.securityAnalysisLevel": "high",
  "mcp.codeCompanion.performanceAnalysisEnabled": true,
  "mcp.codeCompanion.maxGeneratedLines": 200
}
```

## Keyboard Shortcuts

Customize your workflow with these default shortcuts:

- **Generate Code**: `Alt+G`
- **Review Current File**: `Alt+R`
- **Debug Selected Error**: `Alt+D`
- **Explain Selected Code**: `Alt+E`
- **Generate Test for Current File**: `Alt+T`

## Supported Languages

The MCP Code Companion works with:

- Python
- JavaScript/TypeScript
- Java
- C#
- Go
- Ruby
- PHP
- Rust
- C/C++

## Examples

### Python Service Implementation

Prompt:
```
Generate a Python service class for user authentication with JWT tokens, including methods for login, verify token, and refresh token.
```

Generated code includes:
- Complete UserAuthService class
- Proper JWT implementation with security best practices
- Type annotations and comprehensive docstrings
- Error handling and appropriate validation

### React Component Generation

Prompt:
```
Create a React data table component with pagination, sorting, and filtering capabilities
```

Generated code includes:
- Functional component with hooks
- TypeScript interfaces
- Proper state management
- Accessibility attributes
- Documentation comments

## FAQ

**Q: How is this different from GitHub Copilot?**
A: While Copilot focuses on inline code suggestions, MCP Code Companion provides deeper integration with your local environment, project-specific context, and more sophisticated code analysis and debugging capabilities.

**Q: Does it send my code to external servers?**
A: No, all analysis is performed locally through the MCP DevOps Platform running on your machine. No code is transmitted to external servers.

**Q: Can I use this in commercial projects?**
A: Yes, the MCP Code Companion is licensed for both personal and commercial use as part of the MCP DevOps Platform.

## Troubleshooting

If you encounter issues:

1. Ensure the MCP DevOps Platform is running (`./start-demo.sh`)
2. Check the MCP Code Companion output panel for error messages
3. Verify your VSCode settings match the recommended configuration
4. Restart VSCode if extensions were recently installed
5. Check the logs in the MCP DevOps Platform for server-side errors

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [VSCode Extension Marketplace](https://marketplace.visualstudio.com/items?itemName=mcp-code-companion)
- [GitHub Repository](https://github.com/example/mcp-code-companion)
- [Issue Tracker](https://github.com/example/mcp-code-companion/issues) 