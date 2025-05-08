import getpass
import json

# Workaround for os.getlogin issues in some environments
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.shared.types import SamplingMessage, TextContent

os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("SamplingDemo")

# Sampling capability requires explicit configuration
mcp.server_capabilities["features"]["sampling"] = {
    "supported": True,
    "maxDepth": 3,
    "maxBranches": 2,
    "supportsBatching": True,
}

# Store a history of successful sampling operations
sampling_history = []


@mcp.on_initialize
def handle_initialize(params):
    """Check if client supports sampling during initialization"""
    client_caps = params.get("capabilities", {})
    client_features = client_caps.get("features", {})
    sampling_support = client_features.get("sampling", {}).get("supported", False)

    sys.stderr.write(
        f"\nClient sampling support: {'✅ YES' if sampling_support else '❌ NO'}\n"
    )
    if not sampling_support:
        sys.stderr.write(
            "⚠️ This demo requires a sampling-capable client to fully function\n"
        )

    return {"capabilities": mcp.server_capabilities}


# A tool that uses sampling to get LLM input
@mcp.tool()
def classify_text(text: str, categories: List[str]) -> Dict[str, Any]:
    """
    Classify the given text into one of the provided categories using LLM sampling

    This demonstrates how an MCP server can initiate an LLM interaction to process data
    """
    sys.stderr.write("\n=== CLASSIFYING TEXT ===\n")
    sys.stderr.write(f"Text: {text}\n")
    sys.stderr.write(f"Categories: {categories}\n")

    # Create a sampling request to ask the LLM to classify the text
    prompt_messages = [
        SamplingMessage(
            role="system",
            content=[
                TextContent(
                    text="You are a text classifier. You will be given a text and a list of categories. "
                    "Your task is to classify the text into exactly one of the provided categories. "
                    "Respond with just the category name, nothing else."
                )
            ],
        ),
        SamplingMessage(
            role="user",
            content=[
                TextContent(
                    text=f"Classify the following text into one of these categories: {', '.join(categories)}\n\nText: {text}"
                )
            ],
        ),
    ]

    # Sample from the LLM via the client
    sys.stderr.write("Sending sampling request to LLM via client...\n")
    try:
        # This is where the magic happens: the server asks the client to perform LLM sampling
        sampling_result = mcp.sample(prompt_messages)

        # Extract the classification from the LLM's response
        classification = sampling_result.content[0].text.strip()
        sys.stderr.write(f"LLM classified as: {classification}\n")

        # Store in history
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "categories": categories,
            "classification": classification,
        }
        sampling_history.append(record)

        return {
            "classification": classification,
            "confidence": 0.85,  # Placeholder confidence score
            "record_id": record["id"],
        }

    except Exception as e:
        sys.stderr.write(f"⚠️ Sampling failed: {str(e)}\n")
        return {"error": "Sampling failed", "message": str(e)}


@mcp.tool()
def multi_step_analysis(document: str) -> Dict[str, Any]:
    """
    Perform multi-step analysis of a document using nested sampling

    This demonstrates how an MCP server can use multiple sampling calls,
    including nested sampling, to achieve more complex workflows
    """
    sys.stderr.write("\n=== MULTI-STEP ANALYSIS ===\n")
    sys.stderr.write(f"Document length: {len(document)} chars\n")

    results = {}

    # Step 1: Extract key topics
    sys.stderr.write("Step 1: Extracting key topics...\n")
    topic_messages = [
        SamplingMessage(
            role="system",
            content=[
                TextContent(
                    text="Extract the 3 main topics from the document as a comma-separated list."
                )
            ],
        ),
        SamplingMessage(role="user", content=[TextContent(text=document)]),
    ]

    try:
        topic_result = mcp.sample(topic_messages)
        topics = [t.strip() for t in topic_result.content[0].text.split(",")]
        results["topics"] = topics
        sys.stderr.write(f"Topics: {topics}\n")

        # Step 2: For each topic, generate a summary using nested sampling
        results["topic_summaries"] = {}

        for topic in topics:
            sys.stderr.write(f"Step 2: Generating summary for topic '{topic}'...\n")

            summary_messages = [
                SamplingMessage(
                    role="system",
                    content=[
                        TextContent(
                            text=f"Write a short summary (max 50 words) about the topic '{topic}' based on the document."
                        )
                    ],
                ),
                SamplingMessage(role="user", content=[TextContent(text=document)]),
            ]

            summary_result = mcp.sample(summary_messages)
            results["topic_summaries"][topic] = summary_result.content[0].text.strip()

        # Step 3: Overall sentiment analysis
        sys.stderr.write("Step 3: Analyzing sentiment...\n")
        sentiment_messages = [
            SamplingMessage(
                role="system",
                content=[
                    TextContent(
                        text="What is the overall sentiment of this document? Respond with one word: Positive, Neutral, or Negative."
                    )
                ],
            ),
            SamplingMessage(role="user", content=[TextContent(text=document)]),
        ]

        sentiment_result = mcp.sample(sentiment_messages)
        results["sentiment"] = sentiment_result.content[0].text.strip()
        sys.stderr.write(f"Sentiment: {results['sentiment']}\n")

        # Record the analysis
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "document_length": len(document),
            "results": results,
        }
        sampling_history.append(record)

        return results

    except Exception as e:
        sys.stderr.write(f"⚠️ Analysis failed: {str(e)}\n")
        return {"error": "Analysis failed", "message": str(e)}


@mcp.tool()
def get_sampling_history() -> List[Dict[str, Any]]:
    """Get the history of sampling operations"""
    return sampling_history


@mcp.resource("sampling://capabilities")
def get_sampling_capabilities() -> str:
    """Get detailed information about the sampling capabilities"""
    return json.dumps(
        {
            "server_capabilities": mcp.server_capabilities["features"]["sampling"],
            "description": "This server demonstrates bidirectional sampling, where an MCP server can request the client to perform LLM operations",
        }
    )


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP SAMPLING MECHANISM DEMO ===\n")
sys.stderr.write("This example demonstrates MCP's bidirectional sampling capability:\n")
sys.stderr.write(
    "1. The server can request an LLM inference from the client via 'sampling'\n"
)
sys.stderr.write(
    "2. This allows tools to leverage LLM capabilities for their operation\n"
)
sys.stderr.write("3. Try the 'classify_text' tool to see basic sampling in action\n")
sys.stderr.write("4. Try the 'multi_step_analysis' tool to see nested sampling\n\n")
sys.stderr.write(
    "NOTE: This demo requires a client that supports the 'sampling' feature\n"
)
sys.stderr.write("(such as Claude Desktop or another sampling-capable client)\n")
sys.stderr.write("=== END SAMPLING MECHANISM INFO ===\n\n")

# This server demonstrates the MCP sampling mechanism
# Run with: uv run mcp dev 46-sampling-mechanism.py
