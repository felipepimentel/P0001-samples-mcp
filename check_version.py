import inspect

from mcp.server.fastmcp import FastMCP

# Create a FastMCP instance
mcp = FastMCP("VersionCheck")

# Print all methods and attributes
print("All attributes and methods of FastMCP:")
for name in dir(mcp):
    if not name.startswith("__"):
        print(f"- {name}")

# Print decorator methods specifically
print("\nDecorator methods:")
for name in dir(mcp):
    if callable(getattr(mcp, name)) and not name.startswith("__"):
        # Check if it's likely a decorator
        attr = getattr(mcp, name)
        if inspect.ismethod(attr) and attr.__self__ is mcp:
            sig = inspect.signature(attr)
            print(f"- {name}{sig}")

print("\nVersion Info:")
try:
    import mcp

    print(f"MCP Package Version: {mcp.__version__}")
except (ImportError, AttributeError):
    print("MCP version not available")
