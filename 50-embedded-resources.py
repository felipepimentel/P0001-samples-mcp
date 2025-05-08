import getpass
import json
import os
import sys
import uuid
from base64 import b64encode
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("EmbeddedResourcesDemo")

# Sample data for our resources
documents = {
    "doc-001": {
        "id": "doc-001",
        "title": "Introduction to MCP",
        "content": "The Model Context Protocol (MCP) is a standardized protocol for AI systems to interact with external tools and data sources.",
        "tags": ["protocol", "ai", "introduction"],
        "created_at": "2025-01-15T10:00:00Z",
        "attachments": ["att-001", "att-002"],
    },
    "doc-002": {
        "id": "doc-002",
        "title": "MCP Resource System",
        "content": "MCP resources provide a way to expose structured data to AI models. Resources can be embedded directly in responses or referenced by URI.",
        "tags": ["protocol", "resources", "advanced"],
        "created_at": "2025-01-20T14:30:00Z",
        "attachments": ["att-002", "att-003"],
    },
    "doc-003": {
        "id": "doc-003",
        "title": "MCP Tool System",
        "content": "MCP tools allow AI models to perform actions through function calls. Tools can return embedded resources in their responses.",
        "tags": ["protocol", "tools", "advanced"],
        "created_at": "2025-01-25T09:15:00Z",
        "attachments": ["att-001", "att-003"],
    },
}

attachments = {
    "att-001": {
        "id": "att-001",
        "filename": "mcp_architecture.png",
        "content_type": "image/png",
        "description": "MCP architecture diagram",
        "content": b64encode(b"FAKE_IMAGE_DATA_FOR_ARCHITECTURE_DIAGRAM").decode(
            "utf-8"
        ),
        "created_at": "2025-01-10T08:45:00Z",
    },
    "att-002": {
        "id": "att-002",
        "filename": "protocol_specification.pdf",
        "content_type": "application/pdf",
        "description": "MCP protocol specification document",
        "content": b64encode(b"FAKE_PDF_DATA_FOR_PROTOCOL_SPECIFICATION").decode(
            "utf-8"
        ),
        "created_at": "2025-01-12T11:20:00Z",
    },
    "att-003": {
        "id": "att-003",
        "filename": "implementation_notes.md",
        "content_type": "text/markdown",
        "description": "Implementation notes in Markdown format",
        "content": "# MCP Implementation Notes\n\n## Key Components\n\n- Transport Layer\n- Message Format\n- Resource System\n- Tool System\n\n## Best Practices\n\n- Always validate inputs\n- Handle errors gracefully\n- Maintain backward compatibility",
        "created_at": "2025-01-18T16:10:00Z",
    },
}

# Track newly created resources
custom_resources = {}


# Define resource handlers
@mcp.resource("documents/{doc_id}")
def get_document(doc_id: str) -> str:
    """Get a document by ID"""
    if doc_id in documents:
        return json.dumps(documents[doc_id])
    elif doc_id in custom_resources:
        return json.dumps(custom_resources[doc_id])
    else:
        return json.dumps({"error": f"Document not found: {doc_id}"})


@mcp.resource("attachments/{attachment_id}")
def get_attachment(attachment_id: str) -> str:
    """Get an attachment by ID"""
    if attachment_id in attachments:
        return json.dumps(attachments[attachment_id])
    else:
        return json.dumps({"error": f"Attachment not found: {attachment_id}"})


# Helper function for embedding resources
def create_embedded_resource(
    uri: str, content_type: str, content: Any
) -> Dict[str, Any]:
    """Create an embedded resource structure"""
    return {
        "_type": "embedded_resource",
        "uri": uri,
        "content_type": content_type,
        "content": content,
    }


# Tools that demonstrate embedded resources
@mcp.tool()
def get_document_with_attachments(doc_id: str) -> Dict[str, Any]:
    """
    Get a document with all its attachments embedded directly in the response

    Args:
        doc_id: The ID of the document to retrieve

    This demonstrates how resources can be embedded directly in responses,
    reducing the need for multiple requests.
    """
    # Check if document exists
    if doc_id not in documents and doc_id not in custom_resources:
        return {"error": f"Document not found: {doc_id}"}

    # Get the document
    doc = documents.get(doc_id) or custom_resources.get(doc_id)

    # Create a response with embedded resources
    response = {"document": doc, "embedded_attachments": []}

    # Embed each attachment
    for attachment_id in doc.get("attachments", []):
        if attachment_id in attachments:
            attachment = attachments[attachment_id]

            # Create an embedded version of the attachment
            embedded_attachment = create_embedded_resource(
                uri=f"attachments/{attachment_id}",
                content_type=attachment["content_type"],
                content=attachment,
            )

            response["embedded_attachments"].append(embedded_attachment)

    return response


@mcp.tool()
def search_documents(query: str, embed_results: bool = True) -> Dict[str, Any]:
    """
    Search documents for a query term and optionally embed matching documents

    Args:
        query: The search term to look for
        embed_results: Whether to embed document content in the response (default: True)

    This demonstrates how search results can include embedded resources.
    """
    matches = []

    # Perform a simple search (case-insensitive substring match)
    query = query.lower()
    for doc_id, doc in {**documents, **custom_resources}.items():
        if (
            query in doc["title"].lower()
            or query in doc["content"].lower()
            or any(query in tag.lower() for tag in doc["tags"])
        ):
            matches.append(doc_id)

    # Prepare response
    response = {
        "query": query,
        "match_count": len(matches),
        "matching_ids": matches,
    }

    # If embedding is requested, include the full content
    if embed_results and matches:
        embedded_docs = []

        for doc_id in matches:
            doc = documents.get(doc_id) or custom_resources.get(doc_id)

            # Create embedded resource
            embedded_doc = create_embedded_resource(
                uri=f"documents/{doc_id}", content_type="application/json", content=doc
            )

            embedded_docs.append(embedded_doc)

        response["embedded_results"] = embedded_docs

    return response


@mcp.tool()
def create_document(title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
    """
    Create a new document and return it with an embedded URI

    Args:
        title: The document title
        content: The document content
        tags: Optional list of tags

    Returns the created document with its permanent URI embedded.
    """
    # Generate a new document ID
    doc_id = f"custom-{str(uuid.uuid4())[:8]}"

    # Create the document
    doc = {
        "id": doc_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "attachments": [],
    }

    # Store the document
    custom_resources[doc_id] = doc

    # Return the document with its embedded URI
    return {
        "document": doc,
        "uri": create_embedded_resource(
            uri=f"documents/{doc_id}", content_type="application/json", content=doc
        ),
    }


@mcp.tool()
def create_attachment_for_document(
    doc_id: str,
    filename: str,
    content: str,
    content_type: str = "text/plain",
    description: str = "",
) -> Dict[str, Any]:
    """
    Create a new attachment and associate it with a document

    Args:
        doc_id: The document ID to attach to
        filename: The attachment filename
        content: The attachment content as text
        content_type: The content MIME type
        description: Optional description

    Returns the document with the new attachment embedded.
    """
    # Check if document exists
    if doc_id not in documents and doc_id not in custom_resources:
        return {"error": f"Document not found: {doc_id}"}

    # Get the document
    doc = documents.get(doc_id) or custom_resources.get(doc_id)

    # Generate a new attachment ID
    attachment_id = f"custom-att-{str(uuid.uuid4())[:8]}"

    # Create the attachment
    attachment = {
        "id": attachment_id,
        "filename": filename,
        "content_type": content_type,
        "description": description,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }

    # Store the attachment
    attachments[attachment_id] = attachment

    # Update the document to reference the new attachment
    if doc_id in documents:
        documents[doc_id]["attachments"].append(attachment_id)
    else:
        custom_resources[doc_id]["attachments"].append(attachment_id)

    # Return the result with embedded resources
    return {
        "document": create_embedded_resource(
            uri=f"documents/{doc_id}", content_type="application/json", content=doc
        ),
        "attachment": create_embedded_resource(
            uri=f"attachments/{attachment_id}",
            content_type=content_type,
            content=attachment,
        ),
    }


@mcp.tool()
def get_related_documents(doc_id: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Find documents related to the given document based on shared tags

    Args:
        doc_id: The document ID to find related content for
        max_results: Maximum number of results to return

    This demonstrates how complex resource relationships can be presented
    with embedded resources.
    """
    # Check if document exists
    if doc_id not in documents and doc_id not in custom_resources:
        return {"error": f"Document not found: {doc_id}"}

    # Get the document
    doc = documents.get(doc_id) or custom_resources.get(doc_id)
    doc_tags = set(doc["tags"])

    # Find related documents based on tag overlap
    related = []

    for related_id, related_doc in {**documents, **custom_resources}.items():
        if related_id == doc_id:
            continue  # Skip the original document

        # Calculate tag overlap
        related_tags = set(related_doc["tags"])
        overlap = len(doc_tags.intersection(related_tags))

        if overlap > 0:
            related.append(
                {
                    "doc_id": related_id,
                    "overlap": overlap,
                    "document": create_embedded_resource(
                        uri=f"documents/{related_id}",
                        content_type="application/json",
                        content=related_doc,
                    ),
                }
            )

    # Sort by overlap (highest first) and limit results
    related.sort(key=lambda x: x["overlap"], reverse=True)
    related = related[:max_results]

    return {
        "document_id": doc_id,
        "related_count": len(related),
        "related_documents": related,
    }


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP EMBEDDED RESOURCES DEMO ===\n")
sys.stderr.write("This example demonstrates the use of embedded resources in MCP:\n")
sys.stderr.write("1. Resources can be embedded directly in responses\n")
sys.stderr.write("2. This reduces the need for multiple round-trips\n")
sys.stderr.write("3. Resources maintain their URI identity when embedded\n")
sys.stderr.write(
    "4. Clients can choose to use the embedded data or fetch fresh data\n\n"
)
sys.stderr.write("Try these tools to see embedded resources in action:\n")
sys.stderr.write(
    "- get_document_with_attachments: Embeds attachments in document response\n"
)
sys.stderr.write("- search_documents: Embeds matching documents in search results\n")
sys.stderr.write("- create_document: Creates a document and returns it embedded\n")
sys.stderr.write(
    "- get_related_documents: Finds and embeds documents with shared tags\n"
)
sys.stderr.write("=== END EMBEDDED RESOURCES INFO ===\n\n")

# This server demonstrates MCP embedded resources
# Run with: uv run mcp dev 50-embedded-resources.py
