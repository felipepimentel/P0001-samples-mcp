#!/bin/bash

# This script runs the minimal MCP example in background with timeout

# Set the timeout in seconds
TIMEOUT=30

# Function to run the MCP example with timeout
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

# Run the minimal example
run_example "minimal-mcp-examples.py"

echo "Minimal MCP example started in background with ${TIMEOUT}s timeout"
echo "To check logs: cat minimal-mcp-examples.log"
echo "To stop example: ./stop_minimal_mcp_example.sh" 