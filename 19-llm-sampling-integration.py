import json
import re
import time
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import AssistantMessage, SystemMessage, UserMessage

mcp = FastMCP("LLM Sampling Integration")

# Store some sample interactions
sample_history = []


@mcp.tool()
async def summarize_with_llm(text: str, style: Optional[str] = "concise") -> str:
    """
    Use the LLM to summarize text in a specific style

    Args:
        text: The text to summarize
        style: Style of summary (concise, detailed, bullet-points, etc.)
    """
    if not text or len(text) < 10:
        return "Error: Text is too short to summarize."

    valid_styles = ["concise", "detailed", "bullet-points", "academic", "simple"]
    if style not in valid_styles:
        return f"Error: Invalid style. Choose from: {', '.join(valid_styles)}"

    # Prepare the messages for the LLM
    messages = [
        SystemMessage(
            "You are a helpful AI assistant specialized in summarizing content."
        ),
        UserMessage(
            f"Please summarize the following text in a {style} style:\n\n{text}"
        ),
    ]

    # Request a completion from the LLM
    try:
        # Use MCP's sampling feature to get a completion from the LLM
        completion = await mcp.sample(messages=messages)

        # Log the interaction
        sample_history.append(
            {
                "timestamp": time.time(),
                "input_length": len(text),
                "style": style,
                "completion_length": len(completion.content),
            }
        )

        # Return the completion content
        return completion.content
    except Exception as e:
        return f"Error requesting LLM completion: {str(e)}"


@mcp.tool()
async def answer_question(question: str, context: Optional[str] = None) -> str:
    """
    Use the LLM to answer a question based on optional context

    Args:
        question: The question to answer
        context: Optional context to help answer the question
    """
    if not question or not question.strip():
        return "Error: Question cannot be empty."

    # Prepare messages for the LLM
    messages = [
        SystemMessage(
            "You are a helpful AI assistant that answers questions accurately based on the provided context."
        ),
    ]

    if context:
        messages.append(
            UserMessage(
                f"Context information:\n\n{context}\n\nBased on this context, please answer the following question: {question}"
            )
        )
    else:
        messages.append(UserMessage(f"Please answer this question: {question}"))

    # Request a completion from the LLM
    try:
        # Use MCP's sampling feature to get a completion from the LLM
        completion = await mcp.sample(messages=messages)

        # Log the interaction
        sample_history.append(
            {
                "timestamp": time.time(),
                "question": question,
                "has_context": context is not None,
                "completion_length": len(completion.content),
            }
        )

        # Return the completion content
        return completion.content
    except Exception as e:
        return f"Error requesting LLM completion: {str(e)}"


@mcp.tool()
async def generate_creative_content(
    prompt: str, format: str, tone: Optional[str] = "neutral"
) -> str:
    """
    Use the LLM to generate creative content in a specific format and tone

    Args:
        prompt: The creative prompt to inspire the content
        format: Format of the content (poem, story, joke, dialogue, etc.)
        tone: Tone of the content (formal, casual, humorous, serious, etc.)
    """
    if not prompt or not prompt.strip():
        return "Error: Prompt cannot be empty."

    valid_formats = ["poem", "story", "joke", "dialogue", "email", "blog-post"]
    if format not in valid_formats:
        return f"Error: Invalid format. Choose from: {', '.join(valid_formats)}"

    valid_tones = [
        "formal",
        "casual",
        "humorous",
        "serious",
        "inspirational",
        "neutral",
    ]
    if tone not in valid_tones:
        return f"Error: Invalid tone. Choose from: {', '.join(valid_tones)}"

    # Prepare messages for the LLM
    messages = [
        SystemMessage(
            f"You are a creative assistant specialized in generating {format}s in a {tone} tone."
        ),
        UserMessage(
            f"Please create a {format} based on the following prompt, maintaining a {tone} tone:\n\n{prompt}"
        ),
    ]

    # Request a completion from the LLM
    try:
        # Use MCP's sampling feature to get a completion from the LLM
        completion = await mcp.sample(messages=messages)

        # Log the interaction
        sample_history.append(
            {
                "timestamp": time.time(),
                "prompt": prompt,
                "format": format,
                "tone": tone,
                "completion_length": len(completion.content),
            }
        )

        # Return the completion content
        return completion.content
    except Exception as e:
        return f"Error requesting LLM completion: {str(e)}"


@mcp.tool()
async def extract_structured_data(text: str, schema: Dict[str, str]) -> str:
    """
    Use the LLM to extract structured data from text based on a schema

    Args:
        text: The text to extract data from
        schema: Dictionary describing the data to extract with field names and descriptions
    """
    if not text or len(text) < 10:
        return "Error: Text is too short to extract data from."

    if not schema or not isinstance(schema, dict) or len(schema) == 0:
        return "Error: Schema must be a non-empty dictionary with field names and descriptions."

    # Create a schema description for the prompt
    schema_description = "\n".join(
        [f"- {key}: {value}" for key, value in schema.items()]
    )

    # Prepare messages for the LLM
    messages = [
        SystemMessage(
            "You are a data extraction assistant that extracts structured information from text."
        ),
        UserMessage(
            f"Extract the following information from the text below. Return the data as a valid JSON object with these fields:\n\n{schema_description}\n\nText to analyze:\n\n{text}\n\nReturn ONLY a valid JSON object with the extracted data, nothing else."
        ),
    ]

    # Request a completion from the LLM
    try:
        # Use MCP's sampling feature to get a completion from the LLM
        completion = await mcp.sample(messages=messages)

        # Log the interaction
        sample_history.append(
            {
                "timestamp": time.time(),
                "text_length": len(text),
                "schema_fields": list(schema.keys()),
                "completion_length": len(completion.content),
            }
        )

        # Try to extract valid JSON from the response
        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", completion.content, re.DOTALL
        )
        if json_match:
            extracted_json = json_match.group(1)
        else:
            extracted_json = completion.content.strip()

        # Parse and validate the JSON
        try:
            parsed_json = json.loads(extracted_json)
            return json.dumps(parsed_json, indent=2)
        except json.JSONDecodeError:
            # If parsing fails, return the raw completion
            return f"Warning: Could not parse response as JSON. Raw response:\n\n{completion.content}"

    except Exception as e:
        return f"Error requesting LLM completion: {str(e)}"


@mcp.tool()
async def multi_turn_conversation(initial_prompt: str, follow_ups: List[str]) -> str:
    """
    Conduct a multi-turn conversation with the LLM

    Args:
        initial_prompt: The initial prompt to start the conversation
        follow_ups: List of follow-up prompts for additional turns
    """
    if not initial_prompt or not initial_prompt.strip():
        return "Error: Initial prompt cannot be empty."

    if not follow_ups or not isinstance(follow_ups, list):
        return "Error: Follow-ups must be a non-empty list of prompts."

    # Initialize the conversation
    conversation = [
        SystemMessage("You are a helpful AI assistant engaged in a conversation."),
        UserMessage(initial_prompt),
    ]

    # Build the conversation transcript
    transcript = ["# Conversation Transcript\n"]

    try:
        # First turn
        transcript.append(f"**User**: {initial_prompt}\n")

        # Get response for the initial prompt
        completion = await mcp.sample(messages=conversation)
        transcript.append(f"**Assistant**: {completion.content}\n")

        # Add the assistant's response to the conversation history
        conversation.append(AssistantMessage(completion.content))

        # Process follow-up turns
        for i, follow_up in enumerate(follow_ups, 1):
            if not follow_up or not follow_up.strip():
                transcript.append(f"\n**Follow-up {i}**: [Empty prompt skipped]\n")
                continue

            # Add the follow-up to the conversation
            conversation.append(UserMessage(follow_up))
            transcript.append(f"\n**User**: {follow_up}\n")

            # Get response for this turn
            completion = await mcp.sample(messages=conversation)
            transcript.append(f"**Assistant**: {completion.content}\n")

            # Add the assistant's response to the conversation history
            conversation.append(AssistantMessage(completion.content))

        # Log the interaction
        sample_history.append(
            {
                "timestamp": time.time(),
                "initial_prompt": initial_prompt,
                "turns": len(follow_ups) + 1,
                "total_messages": len(conversation),
            }
        )

        # Return the full transcript
        return "\n".join(transcript)

    except Exception as e:
        return f"Error in conversation: {str(e)}\n\nPartial transcript:\n" + "\n".join(
            transcript
        )


@mcp.resource("sampling://stats")
def get_sampling_stats() -> str:
    """Get statistics about LLM sampling usage"""
    if not sample_history:
        return json.dumps({"message": "No sampling history available yet."}, indent=2)

    # Calculate some basic stats
    total_samples = len(sample_history)
    avg_completion_length = (
        sum(entry.get("completion_length", 0) for entry in sample_history)
        / total_samples
        if total_samples > 0
        else 0
    )

    # Count sample types
    tool_counts = {}
    for entry in sample_history:
        if "style" in entry:  # summarize_with_llm
            tool_name = "summarize_with_llm"
        elif "question" in entry:  # answer_question
            tool_name = "answer_question"
        elif "format" in entry:  # generate_creative_content
            tool_name = "generate_creative_content"
        elif "schema_fields" in entry:  # extract_structured_data
            tool_name = "extract_structured_data"
        elif "turns" in entry:  # multi_turn_conversation
            tool_name = "multi_turn_conversation"
        else:
            tool_name = "unknown"

        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

    # Get the most recent samples
    recent_samples = sorted(
        sample_history, key=lambda x: x.get("timestamp", 0), reverse=True
    )[:5]

    return json.dumps(
        {
            "total_samples": total_samples,
            "avg_completion_length": avg_completion_length,
            "tool_usage": tool_counts,
            "recent_samples": recent_samples,
        },
        indent=2,
    )
