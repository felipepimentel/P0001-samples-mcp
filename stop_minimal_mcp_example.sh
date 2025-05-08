#!/bin/bash

# This script stops the minimal MCP example started by run_minimal_mcp_example.sh

# Check if PID file exists
if [ ! -f "minimal-mcp-examples.pid" ]; then
    echo "No running minimal MCP example found"
    exit 0
fi

# Get PID
pid=$(cat "minimal-mcp-examples.pid")

# Check if process is still running
if ps -p $pid > /dev/null; then
    echo "Stopping minimal-mcp-examples (PID: $pid)"
    kill $pid 2>/dev/null || true
else
    echo "minimal-mcp-examples (PID: $pid) is not running"
fi

# Remove PID file
rm -f "minimal-mcp-examples.pid"

echo "Minimal MCP example has been stopped" 