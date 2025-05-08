#!/bin/bash

# This script runs all MCP examples in background with timeouts

# Set the timeout in seconds
TIMEOUT=30

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

# Run all examples
run_example "55-sqlite-persistence.py"
run_example "56-memory-cache-integration.py"
run_example "57-cross-server-bridge.py"
run_example "58-json-schema-validation.py"
run_example "59-llm-sampling-proxy.py"

echo "All examples started in background with ${TIMEOUT}s timeout"
echo "To check logs: cat <example-name>.log"
echo "To stop examples: ./stop_mcp_examples.sh (create this script if needed)" 