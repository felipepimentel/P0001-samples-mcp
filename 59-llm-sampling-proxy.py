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
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("LLMSamplingProxyMCP")

# In-memory storage for sampling history
sampling_history = {}
model_registry = {
    "claude-3-opus": {
        "provider": "anthropic",
        "version": "Claude 3 Opus",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "is_available": True,
    },
    "claude-3-sonnet": {
        "provider": "anthropic",
        "version": "Claude 3 Sonnet",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "is_available": True,
    },
    "claude-3-haiku": {
        "provider": "anthropic",
        "version": "Claude 3 Haiku",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 200000,
        "max_output_tokens": 4096,
        "is_available": True,
    },
    "gpt-4o": {
        "provider": "openai",
        "version": "GPT-4o",
        "capabilities": ["text", "vision", "tool_use"],
        "max_input_tokens": 128000,
        "max_output_tokens": 4096,
        "is_available": True,
    },
}


# Simulated LLM sampling (in real implementation, this would call actual LLM APIs)
async def simulate_llm_response(
    prompt: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 500,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    Simulate an LLM API call

    Args:
        prompt: The text prompt
        model: LLM model to use
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
        stream: Whether to stream the response

    Returns a simulated response
    """
    # Check if model exists
    if model not in model_registry:
        raise ValueError(f"Model '{model}' not found in registry")

    # Check if model is available
    if not model_registry[model]["is_available"]:
        raise ValueError(f"Model '{model}' is currently unavailable")

    # Simulated thinking time based on prompt length and model
    base_thinking_time = 0.5  # Base time in seconds
    prompt_factor = len(prompt) / 1000  # Longer prompts take more time
    model_speed = {
        "claude-3-opus": 1.5,
        "claude-3-sonnet": 1.2,
        "claude-3-haiku": 0.8,
        "gpt-4o": 1.0,
    }

    thinking_time = base_thinking_time + (prompt_factor * model_speed.get(model, 1.0))

    # Cap thinking time to be reasonable for demo
    thinking_time = min(thinking_time, 2.0)

    # Simulate "thinking"
    await asyncio.sleep(thinking_time)

    # Generate a response based on the prompt - this is where a real
    # implementation would call the actual LLM API
    if "weather" in prompt.lower():
        response = "The weather is currently sunny with a temperature of 72°F (22°C). There's a slight breeze and no chance of precipitation for the next 8 hours."
    elif "time" in prompt.lower():
        current_time = datetime.now().strftime("%H:%M:%S")
        response = f"The current time is {current_time}."
    elif "help" in prompt.lower():
        response = "I'm an AI assistant and can help with various tasks like answering questions, explaining concepts, writing content, and much more. What would you like assistance with today?"
    elif "code" in prompt.lower() or "python" in prompt.lower():
        response = """Here's a simple Python function that calculates the Fibonacci sequence:

```python
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
    print(f"fibonacci({i}) = {fibonacci(i)}")
```

This implementation is simple but inefficient for large values of n due to repeated calculations. A more efficient approach would use memoization or an iterative solution."""
    else:
        response = "Thank you for your prompt. I'm a simulated LLM response in this MCP demonstration. This response is generated to show how the MCP sampling proxy works. In a real implementation, this would be an actual response from the specified LLM API."

    # Simulate token count based on response length
    tokens_generated = len(response) // 4  # Rough estimate

    # Calculate simulated cost based on model and tokens
    cost_per_1k_input = {
        "claude-3-opus": 15.0,
        "claude-3-sonnet": 7.5,
        "claude-3-haiku": 0.25,
        "gpt-4o": 10.0,
    }
    cost_per_1k_output = {
        "claude-3-opus": 75.0,
        "claude-3-sonnet": 24.0,
        "claude-3-haiku": 1.25,
        "gpt-4o": 30.0,
    }

    input_tokens = len(prompt) // 4  # Rough estimate
    input_cost = (input_tokens / 1000) * cost_per_1k_input.get(model, 5.0)
    output_cost = (tokens_generated / 1000) * cost_per_1k_output.get(model, 15.0)
    total_cost = input_cost + output_cost

    # If streaming is requested, simulate streaming behavior
    if stream:
        # Create a queue to send chunks of the response
        queue = asyncio.Queue()

        # Break response into chunks
        words = response.split()
        chunks = []
        current_chunk = ""

        for word in words:
            current_chunk += word + " "
            if len(current_chunk) >= 10 or word == words[-1]:
                chunks.append(current_chunk.strip())
                current_chunk = ""

        # Put all chunks in the queue
        for chunk in chunks:
            queue.put_nowait(chunk)

        # Signal end of streaming
        queue.put_nowait(None)

        return {
            "model": model,
            "stream": True,
            "queue": queue,
            "total_tokens": input_tokens + tokens_generated,
            "input_tokens": input_tokens,
            "output_tokens": tokens_generated,
            "cost": total_cost,
            "finish_reason": "stop",
        }

    # Non-streaming response
    return {
        "model": model,
        "response": response,
        "total_tokens": input_tokens + tokens_generated,
        "input_tokens": input_tokens,
        "output_tokens": tokens_generated,
        "cost": total_cost,
        "finish_reason": "stop",
    }


# Record sampling history
def record_sampling(
    sampling_id: str,
    prompt: str,
    model: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    """Record a sampling event in history"""
    timestamp = datetime.now().isoformat()

    sampling_history[sampling_id] = {
        "sampling_id": sampling_id,
        "timestamp": timestamp,
        "prompt": prompt,
        "model": model,
        "parameters": parameters,
        "result": {
            k: v
            for k, v in result.items()
            if k != "queue"  # Don't store the queue
        },
        "duration": result.get("duration", None),
    }


# MCP server capabilities
@mcp.initialize
def handle_initialize(params):
    """Handle server initialization with sampling capabilities"""
    # Advertise sampling capabilities in server response
    return {
        "capabilities": {
            "tools": True,
            "resources": True,
            "sampling": True,  # Indicate this server supports sampling
        }
    }


# Sampling handler
@mcp.sample
async def handle_sample(params):
    """Handle MCP sampling requests by proxying to LLM API"""
    sampling_id = str(uuid4())
    start_time = time.time()

    # Extract parameters
    prompt = params.get("prompt", "")
    model = params.get("model", "claude-3-haiku")  # Default to fastest model
    parameters = params.get("parameters", {})

    # Extract specific parameters with defaults
    temperature = parameters.get("temperature", 0.7)
    max_tokens = parameters.get("max_tokens", 500)
    stream = parameters.get("stream", False)

    try:
        # Call LLM API (simulated in this example)
        result = await simulate_llm_response(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        # Calculate duration
        duration = time.time() - start_time
        result["duration"] = duration

        # Record this sampling event
        record_sampling(sampling_id, prompt, model, parameters, result)

        # If streaming was requested, handle differently
        if stream and "queue" in result:
            queue = result["queue"]

            # Create an async generator to stream responses
            async def response_generator():
                while True:
                    chunk = await queue.get()
                    if chunk is None:  # End of stream
                        break
                    yield {"type": "content", "content": chunk}

                # End with completion message
                yield {
                    "type": "completion",
                    "sampling_id": sampling_id,
                    "total_tokens": result["total_tokens"],
                    "duration": duration,
                }

            # Return a streaming response
            return {"sampling_id": sampling_id, "stream": response_generator()}

        # Non-streaming response
        return {
            "sampling_id": sampling_id,
            "response": result["response"],
            "total_tokens": result["total_tokens"],
            "duration": duration,
        }

    except Exception as e:
        # Record error in history
        error_result = {"error": str(e), "duration": time.time() - start_time}
        record_sampling(sampling_id, prompt, model, parameters, error_result)

        # Re-raise as MCP error
        raise ValueError(f"Sampling failed: {str(e)}")


# Tools for LLM management
@mcp.tool()
def list_models() -> Dict[str, Any]:
    """
    List available LLM models

    Returns a list of all models in the registry
    """
    models = []

    for model_id, details in model_registry.items():
        models.append(
            {
                "id": model_id,
                "provider": details["provider"],
                "version": details["version"],
                "capabilities": details["capabilities"],
                "max_input_tokens": details["max_input_tokens"],
                "max_output_tokens": details["max_output_tokens"],
                "is_available": details["is_available"],
            }
        )

    return {"total": len(models), "models": models}


@mcp.tool()
def get_model_details(model_id: str) -> Dict[str, Any]:
    """
    Get details about a specific model

    Args:
        model_id: ID of the model to retrieve

    Returns detailed information about the model
    """
    if model_id not in model_registry:
        return {"error": "Model not found", "model_id": model_id}

    return {"model_id": model_id, **model_registry[model_id]}


@mcp.tool()
def set_model_availability(model_id: str, available: bool) -> Dict[str, Any]:
    """
    Set the availability of a model

    Args:
        model_id: ID of the model to update
        available: Whether the model should be available

    Returns the updated model details
    """
    if model_id not in model_registry:
        return {"error": "Model not found", "model_id": model_id}

    model_registry[model_id]["is_available"] = available

    return {"updated": True, "model_id": model_id, "is_available": available}


# Sampling history tools
@mcp.tool()
def get_sampling_history(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Get history of sampling events

    Args:
        limit: Optional maximum number of events to return

    Returns a list of sampling events
    """
    events = list(sampling_history.values())

    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x["timestamp"], reverse=True)

    # Apply limit if specified
    if limit and limit > 0:
        events = events[:limit]

    return {"total": len(sampling_history), "returned": len(events), "events": events}


@mcp.tool()
def get_sampling_details(sampling_id: str) -> Dict[str, Any]:
    """
    Get details of a specific sampling event

    Args:
        sampling_id: ID of the sampling event

    Returns detailed information about the sampling event
    """
    if sampling_id not in sampling_history:
        return {"error": "Sampling event not found", "sampling_id": sampling_id}

    return sampling_history[sampling_id]


@mcp.tool()
def get_sampling_stats() -> Dict[str, Any]:
    """
    Get statistics about sampling history

    Returns aggregated stats about sampling events
    """
    if not sampling_history:
        return {"total_events": 0, "message": "No sampling events recorded"}

    # Calculate stats
    total_events = len(sampling_history)
    total_tokens = sum(
        event["result"].get("total_tokens", 0)
        for event in sampling_history.values()
        if "result" in event
    )
    total_cost = sum(
        event["result"].get("cost", 0)
        for event in sampling_history.values()
        if "result" in event
    )

    # Model usage counts
    model_usage = {}
    for event in sampling_history.values():
        model = event["model"]
        model_usage[model] = model_usage.get(model, 0) + 1

    # Calculate average response time
    durations = [
        event["result"].get("duration", 0)
        for event in sampling_history.values()
        if "result" in event and "duration" in event["result"]
    ]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "total_events": total_events,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "average_duration": avg_duration,
        "model_usage": model_usage,
    }


# Demo tools
@mcp.tool()
async def sampling_demo() -> Dict[str, Any]:
    """
    Run a demonstration of the sampling proxy

    This tool performs several sample calls to demonstrate functionality
    """
    results = []

    # Clear any existing history for a clean demo
    sampling_history.clear()

    # Sample 1: Basic question
    results.append(
        {
            "step": "Basic question",
            "prompt": "What is the current weather?",
            "model": "claude-3-haiku",
            "result": await handle_sample(
                {
                    "prompt": "What is the current weather?",
                    "model": "claude-3-haiku",
                    "parameters": {"temperature": 0.7, "max_tokens": 100},
                }
            ),
        }
    )

    # Sample 2: Code generation
    results.append(
        {
            "step": "Code generation",
            "prompt": "Write a Python function to check if a number is prime",
            "model": "claude-3-sonnet",
            "result": await handle_sample(
                {
                    "prompt": "Write a Python function to check if a number is prime",
                    "model": "claude-3-sonnet",
                    "parameters": {"temperature": 0.2, "max_tokens": 300},
                }
            ),
        }
    )

    # Sample 3: Streaming response (only metadata shown in results)
    stream_result = await handle_sample(
        {
            "prompt": "Tell me about the benefits of exercise",
            "model": "claude-3-opus",
            "parameters": {"temperature": 0.7, "max_tokens": 200, "stream": True},
        }
    )

    # For demo purposes, we can't actually stream the response here,
    # so we just record that a streaming request was made
    results.append(
        {
            "step": "Streaming response",
            "prompt": "Tell me about the benefits of exercise",
            "model": "claude-3-opus",
            "result": {
                "sampling_id": stream_result["sampling_id"],
                "message": "Streaming response initiated (not shown in results)",
            },
        }
    )

    # Get stats after all samples
    stats = get_sampling_stats()

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
sys.stderr.write("\n=== MCP LLM SAMPLING PROXY ===\n")
sys.stderr.write(
    "This example demonstrates an MCP server that acts as a proxy for LLM sampling:\n"
)
sys.stderr.write("1. Implements the MCP sampling protocol\n")
sys.stderr.write("2. Simulates calls to LLM APIs with realistic behavior\n")
sys.stderr.write("3. Provides streaming and non-streaming responses\n")
sys.stderr.write("4. Tracks sampling history and statistics\n")
sys.stderr.write("5. Manages a registry of available models\n\n")
sys.stderr.write("Try the sampling_demo tool to see the proxy in action!\n")
sys.stderr.write("=== END LLM SAMPLING PROXY INFO ===\n\n")

# This server demonstrates MCP as an LLM sampling proxy
# Run with: uv run mcp dev 59-llm-sampling-proxy.py
