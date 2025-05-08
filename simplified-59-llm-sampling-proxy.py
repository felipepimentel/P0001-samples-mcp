import getpass
import os
from typing import Dict, Any
import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("simplified-59-llm-sampling-proxy")

# Copy of tools and resources from 59-llm-sampling-proxy.py
# with lifecycle hooks and middleware removed
import asyncio
import getpass
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4
from mcp.server.fastmcp import FastMCP
# Workaround for os.getlogin issues in some environments
# Create an MCP server
# In-memory storage for sampling history
    "claude-3-opus": {
        "provider": "anthropic",
        "version": "Claude 3 Opus",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "is_available": True,
    "claude-3-sonnet": {
        "provider": "anthropic",
        "version": "Claude 3 Sonnet",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "is_available": True,
    "claude-3-haiku": {
        "provider": "anthropic",
        "version": "Claude 3 Haiku",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "is_available": True,
    "gpt-4o": {
        "provider": "openai",
        "version": "GPT-4o",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 128000,
        "max_output_tokens": 4096,
        "is_available": True,
# Simulated LLM sampling (in real implementation, this would call actual LLM APIs)
async def simulate_llm_response(
    prompt: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 500,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    Args:
        prompt: The text prompt
        model: LLM model to use
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
        stream: Whether to stream the response
    """
    # Check if model exists
    if model not in model_registry:
    # Check if model is available
    if not model_registry[model]["is_available"]:
    # Simulated thinking time based on prompt length and model
    base_thinking_time = 0.5  # Base time in seconds
    prompt_factor = len(prompt) / 1000  # Longer prompts take more time
        "claude-3-opus": 1.5,
        "claude-3-sonnet": 1.2,
        "claude-3-haiku": 0.8,
        "gpt-4o": 1.0,
    # Cap thinking time to be reasonable for demo
    # Simulate "thinking"
    # Generate a response based on the prompt - this is where a real
    # implementation would call the actual LLM API
    if "weather" in prompt.lower():
    elif "time" in prompt.lower():
        current_time = datetime.now().strftime("%H:%M:%S")
    elif "help" in prompt.lower():
    elif "code" in prompt.lower() or "python" in prompt.lower():
        response = """Here's a simple Python function that calculates the Fibonacci sequence:
def fibonacci(n):
    # Calculate the Fibonacci number at position n
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
# Test the function
for i in range(10):
This implementation is simple but inefficient for large values of n due to repeated calculations. A more efficient approach would use memoization or an iterative solution."""
    else:
    # Simulate token count based on response length
    tokens_generated = len(response) // 4  # Rough estimate
    # Calculate simulated cost based on model and tokens
        "claude-3-opus": 15.0,
        "claude-3-sonnet": 7.5,
        "claude-3-haiku": 0.25,
        "gpt-4o": 10.0,
        "claude-3-opus": 75.0,
        "claude-3-sonnet": 24.0,
        "claude-3-haiku": 1.25,
        "gpt-4o": 30.0,
    input_tokens = len(prompt) // 4  # Rough estimate
    # If streaming is requested, simulate streaming behavior
    if stream:
        # Create a queue to send chunks of the response
        # Break response into chunks
        for word in words:
            if len(current_chunk) >= 10 or word == words[-1]:
        # Put all chunks in the queue
        for chunk in chunks:
        # Signal end of streaming
        return {
            "model": model,
            "stream": True,
            "queue": queue,
            "total_tokens": input_tokens + tokens_generated,
            "input_tokens": input_tokens,
            "output_tokens": tokens_generated,
            "cost": total_cost,
            "finish_reason": "stop",
    # Non-streaming response
    return {
        "model": model,
        "response": response,
        "total_tokens": input_tokens + tokens_generated,
        "input_tokens": input_tokens,
        "output_tokens": tokens_generated,
        "cost": total_cost,
        "finish_reason": "stop",
# Record sampling history
def record_sampling(
    sampling_id: str,
    prompt: str,
    model: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    """Record a sampling event in history"""
        "sampling_id": sampling_id,
        "timestamp": timestamp,
        "prompt": prompt,
        "model": model,
        "parameters": parameters,
        "result": {
            k: v
            if k != "queue"  # Don't store the queue
        "duration": result.get("duration", None),
# MCP server capabilities
def handle_initialize(params):
    """Handle server initialization with sampling capabilities"""
    # Advertise sampling capabilities in server response
    return {
        "capabilities": {
            "tools": True,
            "resources": True,
            "sampling": True,  # Indicate this server supports sampling
# Sampling handler
async def handle_sample(params):
    """Handle MCP sampling requests by proxying to LLM API"""
    # Extract parameters
    model = params.get("model", "claude-3-haiku")  # Default to fastest model
    # Extract specific parameters with defaults
    try:
        # Call LLM API (simulated in this example)
        # Calculate duration
        # Record this sampling event
        # If streaming was requested, handle differently
        if stream and "queue" in result:
            # Create an async generator to stream responses
            async def response_generator():
                while True:
                    if chunk is None:  # End of stream
                    yield {"type": "content", "content": chunk}
                # End with completion message
                    "type": "completion",
                    "sampling_id": sampling_id,
                    "total_tokens": result["total_tokens"],
                    "duration": duration,
            # Return a streaming response
            return {"sampling_id": sampling_id, "stream": response_generator()}
        # Non-streaming response
        return {
            "sampling_id": sampling_id,
            "response": result["response"],
            "total_tokens": result["total_tokens"],
            "duration": duration,
    except Exception as e:
        # Record error in history
        error_result = {"error": str(e), "duration": time.time() - start_time}
        # Re-raise as MCP error
        raise ValueError(f"Sampling failed: {str(e)}")
# Tools for LLM management
@mcp.tool()
def list_models() -> Dict[str, Any]:
    """
    """
    for model_id, details in model_registry.items():
                "id": model_id,
                "provider": details["provider"],
                "version": details["version"],
                "capabilities": details["capabilities"],
                "max_input_tokens": details["max_input_tokens"],
                "max_output_tokens": details["max_output_tokens"],
                "is_available": details["is_available"],
    return {"total": len(models), "models": models}
@mcp.tool()
def get_model_details(model_id: str) -> Dict[str, Any]:
    """
    Args:
        model_id: ID of the model to retrieve
    """
    if model_id not in model_registry:
        return {"error": "Model not found", "model_id": model_id}
    return {"model_id": model_id, **model_registry[model_id]}
@mcp.tool()
def set_model_availability(model_id: str, available: bool) -> Dict[str, Any]:
    """
    Args:
        model_id: ID of the model to update
        available: Whether the model should be available
    """
    if model_id not in model_registry:
        return {"error": "Model not found", "model_id": model_id}
    return {"updated": True, "model_id": model_id, "is_available": available}
# Sampling history tools
@mcp.tool()
def get_sampling_history(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Args:
        limit: Optional maximum number of events to return
    """
    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    # Apply limit if specified
    if limit and limit > 0:
        events = events[:limit]
    return {"total": len(sampling_history), "returned": len(events), "events": events}
@mcp.tool()
def get_sampling_details(sampling_id: str) -> Dict[str, Any]:
    """
    Args:
        sampling_id: ID of the sampling event
    """
    if sampling_id not in sampling_history:
        return {"error": "Sampling event not found", "sampling_id": sampling_id}
    return sampling_history[sampling_id]
@mcp.tool()
def get_sampling_stats() -> Dict[str, Any]:
    """
    """
    if not sampling_history:
        return {"total_events": 0, "message": "No sampling events recorded"}
    # Calculate stats
    # Model usage counts
    for event in sampling_history.values():
    # Calculate average response time
    return {
        "total_events": total_events,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "average_duration": avg_duration,
        "model_usage": model_usage,
# Demo tools
@mcp.tool()
async def sampling_demo() -> Dict[str, Any]:
    """
    """
    # Clear any existing history for a clean demo
    # Sample 1: Basic question
            "step": "Basic question",
            "prompt": "What is the current weather?",
            "model": "claude-3-haiku",
            "result": await handle_sample(
                    "prompt": "What is the current weather?",
                    "model": "claude-3-haiku",
                    "parameters": {"temperature": 0.7, "max_tokens": 100},
    # Sample 2: Code generation
            "step": "Code generation",
            "prompt": "Write a Python function to check if a number is prime",
            "model": "claude-3-sonnet",
            "result": await handle_sample(
                    "prompt": "Write a Python function to check if a number is prime",
                    "model": "claude-3-sonnet",
                    "parameters": {"temperature": 0.2, "max_tokens": 300},
    # Sample 3: Streaming response (only metadata shown in results)
            "prompt": "Tell me about the benefits of exercise",
            "model": "claude-3-opus",
            "parameters": {"temperature": 0.7, "max_tokens": 200, "stream": True},
    # For demo purposes, we can't actually stream the response here,
    # so we just record that a streaming request was made
            "step": "Streaming response",
            "prompt": "Tell me about the benefits of exercise",
            "model": "claude-3-opus",
            "result": {
                "sampling_id": stream_result["sampling_id"],
                "message": "Streaming response initiated (not shown in results)",
    # Get stats after all samples
    return {"demo_steps": results, "stats": stats}
# Resources
@mcp.resource("sampling://models")
def models_resource() -> str:
    """Get all models as a resource"""
    return json.dumps(list_models(), indent=2)
@mcp.resource("sampling://history")
def history_resource() -> str:
    """Get sampling history as a resource"""
    return json.dumps(get_sampling_history(limit=10), indent=2)
@mcp.resource("sampling://stats")
def stats_resource() -> str:
    """Get sampling statistics as a resource"""
    return json.dumps(get_sampling_stats(), indent=2)
# Explain what this demo does when run with MCP CLI
    "This example demonstrates an MCP server that acts as a proxy for LLM sampling:\n"
# This server demonstrates MCP as an LLM sampling proxy
# Run with: uv run mcp dev 59-llm-sampling-proxy.py

if __name__ == "__main__":
    print("MCP Server ready to run!")
    # The server will be run by MCP CLI
    
# Run with: uv run mcp dev simplified-59-llm-sampling-proxy.py
