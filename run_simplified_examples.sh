#!/bin/bash

# This script creates simplified versions of our MCP examples that work with the current MCP version
# and runs them in the background with timeouts

# Set the timeout in seconds
TIMEOUT=30

# Function to create a simplified version of an example
create_simplified_example() {
    local original_file=$1
    local simplified_file="simplified-$(basename $original_file)"
    
    # Extract core functionality, removing lifecycle hooks
    cat > "$simplified_file" << EOF
import getpass
import os
from typing import Dict, Any
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("$(basename "$simplified_file" .py)")

# Copy of tools and resources from $original_file
# with lifecycle hooks and middleware removed
$(grep -v "@mcp.\(initialize\|shutdown\|middleware\|on_initialize\|on_shutdown\|on_sample\|sample\)" "$original_file" | grep -E "(@mcp.tool|@mcp.resource|def \w+\(|return|\"\"\"|\s+.*:|import|#)")

if __name__ == "__main__":
    print("MCP Server ready to run!")
    # The server will be run by MCP CLI
    
# Run with: uv run mcp dev $simplified_file
EOF
    
    echo "Created $simplified_file from $original_file"
    return 0
}

# Function to run an MCP example with timeout
run_example() {
    local example=$1
    local name=$(basename "$example" .py)
    local log_file="${name}.log"
    
    echo "Starting $name, logs in $log_file"
    
    # Run in background with timeout, output to log file
    timeout ${TIMEOUT}s uv run mcp dev "$example" > "$log_file" 2>&1 &
    
    # Store the PID
    echo "$!" > "${name}.pid"
}

# Create and run simplified examples
for example in 55-sqlite-persistence.py 56-memory-cache-integration.py 57-cross-server-bridge.py 58-json-schema-validation.py 59-llm-sampling-proxy.py; do
    echo "Processing $example..."
    create_simplified_example "$example"
    simplified_file="simplified-$(basename $example)"
    run_example "$simplified_file"
done

echo "All simplified examples started in background with ${TIMEOUT}s timeout"
echo "To check logs: cat simplified-*.log"
echo "To stop examples: ./stop_simplified_examples.sh (create this script if needed)" 