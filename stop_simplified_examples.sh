#!/bin/bash

# This script stops all simplified MCP examples started by run_simplified_examples.sh

# Find all PID files for simplified examples
pid_files=$(find . -name "simplified-*.pid")

if [ -z "$pid_files" ]; then
    echo "No running simplified MCP examples found"
    exit 0
fi

# Kill each process
for pid_file in $pid_files; do
    example_name=$(basename "$pid_file" .pid)
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        
        # Check if process is still running
        if ps -p $pid > /dev/null; then
            echo "Stopping $example_name (PID: $pid)"
            kill $pid 2>/dev/null || true
        else
            echo "$example_name (PID: $pid) is not running"
        fi
        
        # Remove PID file
        rm -f "$pid_file"
    fi
done

echo "All simplified MCP examples have been stopped" 