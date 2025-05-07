# MCP Hello World Server

A minimal Python MCP server exposing an `add` tool and a dynamic `greeting` resource, managed entirely with [uv](https://astral.sh/uv/) and the MCP CLI.

---

## Overview
- **Language:** Python 3.12.3+
- **Environment:** Managed with [uv](https://astral.sh/uv/)
- **Entrypoint:** `01-hello.py`
- **Features:**
  - Tool: `add(a: int, b: int)`
  - Resource: `greeting://{name}`
- **No manual startup or print statements—MCP CLI manages all execution.**

---

## Setup

```sh
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv sync
```

---

## Running the Server

### Development Mode (with Inspector)
- For interactive exploration, debugging, and live testing:

```sh
uv run mcp dev 01-hello.py
```
- Opens the MCP Inspector at [http://127.0.0.1:6274](http://127.0.0.1:6274)
- Inspector lets you:
  - List/test all tools, resources, and prompts
  - Send requests and see responses live
  - Debug server behavior interactively

### Production Mode (STDIO, for integration)
- For integration with Claude Desktop or other MCP clients:

```sh
uv run mcp run 01-hello.py
```
- No web dashboard or HTTP port
- All communication via STDIO (MCP protocol only)
- **Never print to stdout in your code**

---

## Using the MCP Inspector (Manual/Advanced)

You can run the Inspector manually for any MCP server (Python, Node, etc):

```sh
npx @modelcontextprotocol/inspector uv run mcp run 01-hello.py
```
- This opens the Inspector and connects to your server via STDIO.
- Useful for debugging, CI, or when not using the MCP CLI dev mode.
- If you see `PORT IS IN USE`, kill the process using the port (e.g. `lsof -i :6277` and `kill <pid>`).

---

## Best Practices
- **No `if __name__ == "__main__"` blocks or manual startup code.**
- **No print/log statements to stdout.** Use CLI flags (`--verbose`, `--debug`) for logs.
- Use only `uv` and `pyproject.toml` for environment and dependencies—never pip or requirements.txt.
- Place new examples in the project root or a clearly named subdirectory, following naming conventions.
- Avoid duplicate or confusing file names.
- Each example must be runnable via `uv run mcp run <filename>.py`.

---

## Error Handling & Troubleshooting
- For `os.getlogin` errors, patch with `os.getlogin = getpass.getuser` at the top of your script.
- Never add workaround prints or manual startup code.
- Common issues:
  - `FileNotFoundError`: Check your server path.
  - `Connection refused`: Ensure the server is running and the path is correct.
  - `Tool execution failed`: Verify required environment variables.
  - `Timeout error`: Increase client timeout if needed.
  - `PORT IS IN USE`: Find and kill the process using the port (e.g. `lsof -i :6277 | grep LISTEN` and `kill <pid>`).
- If Inspector shows only logs like `Processing request of type ...` but nothing is listed:
  - Check for prints/logs in your code (should be none)
  - Ensure your server is using the latest MCP Python SDK and follows the official example
  - Try running Inspector in the VS Code Simple Browser if Chrome/Edge fails ([issue #337](https://github.com/modelcontextprotocol/inspector/issues/337))
- For verbose logs, use:
  ```sh
  npx @modelcontextprotocol/inspector uv run mcp run 01-hello.py --verbose
  ```

---

## Inspector Tips
- Use Inspector (`mcp dev` or manual) for rapid iteration and debugging.
- Inspector shows all registered tools, resources, and prompts.
- Test tool calls, resource reads, and prompt invocations directly from the web UI.
- Inspector is only available in dev mode or via npx/manual.
- If Inspector does not connect, check for protocol errors, port conflicts, or browser issues.

---

## Useful Commands

- **Start dev mode with Inspector:**
  ```sh
  uv run mcp dev 01-hello.py
  ```
- **Start production mode (STDIO):**
  ```sh
  uv run mcp run 01-hello.py
  ```
- **Run Inspector manually:**
  ```sh
  npx @modelcontextprotocol/inspector uv run mcp run 01-hello.py
  ```
- **Check for process using port 6277:**
  ```sh
  lsof -i :6277 | grep LISTEN
  ```
- **Kill process by PID:**
  ```sh
  kill <pid>
  ```

---

## References
- [MCP Quickstart: Server](https://modelcontextprotocol.io/quickstart/server)
- [MCP Inspector Guide](https://modelcontextprotocol.io/docs/tools/inspector)
- [MCP Inspector Medium Example](https://thesof.medium.com/build-your-first-mcp-application-step-by-step-examples-for-stdio-and-sse-servers-integration-773b187aeaed)
- [MCP Python SDK Example](https://github.com/ruslanmv/Simple-MCP-Server-with-Python)
- [MCP Python SDK Docs](https://github.com/modelcontextprotocol/python-sdk/tree/45cea71d907cfabbcb359fe9e0b139126fc11edc)
- [Inspector Issue: Only works in VS Code browser](https://github.com/modelcontextprotocol/inspector/issues/337)
