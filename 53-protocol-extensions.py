import getpass
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from mcp.server.fastmcp import FastMCP

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server with extended capabilities
mcp = FastMCP("ProtocolExtensionsDemo")

# Define our custom capabilities
mcp.server_capabilities["features"]["vector_storage"] = {
    "supported": True,
    "dimensions": [128, 384, 768, 1536],
    "distance_metrics": ["cosine", "euclidean", "dot"],
    "max_vectors": 10000,
}

mcp.server_capabilities["features"]["semantic_search"] = {
    "supported": True,
    "model_name": "text-embedding-ada-002",
    "dimensions": 1536,
    "max_batch_size": 100,
}

mcp.server_capabilities["features"]["custom_tool_annotations"] = {
    "supported": True,
    "supported_annotations": [
        "cost",
        "latency",
        "rate_limit",
        "needs_confirmation",
        "streaming",
        "security_level",
    ],
}

# Define semantic vectors for demonstration
# In a real implementation, these would be generated from a proper embedding model
DOCUMENT_VECTORS = {}
QUERY_HISTORY = []

# Sample documents for vector search
DOCUMENTS = [
    {
        "id": "doc-001",
        "title": "Introduction to MCP",
        "content": "The Model Context Protocol (MCP) is a standardized protocol for AI systems to interact with external tools and data sources.",
        "tags": ["protocol", "ai", "introduction"],
    },
    {
        "id": "doc-002",
        "title": "MCP Resource System",
        "content": "MCP resources provide a way to expose structured data to AI models. Resources can be embedded directly in responses or referenced by URI.",
        "tags": ["protocol", "resources", "advanced"],
    },
    {
        "id": "doc-003",
        "title": "MCP Tool System",
        "content": "MCP tools allow AI models to perform actions through function calls. Tools can return embedded resources in their responses.",
        "tags": ["protocol", "tools", "advanced"],
    },
    {
        "id": "doc-004",
        "title": "MCP Extensions",
        "content": "The Model Context Protocol can be extended with custom capabilities for specific use cases like vector storage and semantic search.",
        "tags": ["protocol", "extensions", "advanced"],
    },
    {
        "id": "doc-005",
        "title": "Vector Embeddings",
        "content": "Vector embeddings are numerical representations of text that capture semantic meaning, allowing for similarity-based retrieval.",
        "tags": ["embeddings", "vectors", "semantic"],
    },
]


# Initialize document vectors with simple fake embeddings
def initialize_vectors():
    """Create simple fake embeddings for demonstration purposes"""
    np.random.seed(42)  # For reproducibility

    # Create a simplistic fake embedding based on word overlap
    # (In a real application, you would use a proper embedding model)
    all_words = set()
    for doc in DOCUMENTS:
        all_words.update(doc["content"].lower().split())

    word_to_index = {word: i for i, word in enumerate(all_words)}
    dim = 128  # Using a smaller dimension for this demo

    for doc in DOCUMENTS:
        # Create a sparse vector based on word presence
        vec = np.zeros(dim)
        for word in doc["content"].lower().split():
            if word in word_to_index:
                idx = word_to_index[word] % dim  # Map to our smaller dimension
                vec[idx] += 1

        # Normalize the vector
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        DOCUMENT_VECTORS[doc["id"]] = vec.tolist()


# Call initialization
initialize_vectors()


# Helper functions for vector operations
def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0


def euclidean_distance(vec1, vec2):
    """Compute Euclidean distance between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.linalg.norm(vec1 - vec2)


def create_query_vector(query: str) -> List[float]:
    """Create a simple query vector from text"""
    # This is a placeholder for a real embedding model
    # In production, you would use a proper model like OpenAI's text-embedding-ada-002

    np.random.seed(hash(query) % 2**32)  # Deterministic based on query

    # Simple approach: create a sparse vector based on query word presence
    all_words = set()
    for doc in DOCUMENTS:
        all_words.update(doc["content"].lower().split())

    word_to_index = {word: i for i, word in enumerate(all_words)}
    dim = 128  # Using a smaller dimension for this demo

    # Create a sparse vector based on word presence
    vec = np.zeros(dim)
    for word in query.lower().split():
        if word in word_to_index:
            idx = word_to_index[word] % dim  # Map to our smaller dimension
            vec[idx] += 1

    # Normalize the vector
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()


# Extended tools with custom annotations
@mcp.tool(
    annotations={
        "cost": 0.0,  # Free
        "latency": "low",
        "rate_limit": 1000,
        "needs_confirmation": False,
        "security_level": "public",
    }
)
def vector_search(
    query: str, top_k: int = 3, threshold: float = 0.0, metric: str = "cosine"
) -> Dict[str, Any]:
    """
    Search for documents similar to the query using vector similarity

    Args:
        query: The search query
        top_k: Maximum number of results to return
        threshold: Minimum similarity score threshold (0.0-1.0)
        metric: Similarity metric to use ('cosine', 'euclidean', 'dot')

    This tool demonstrates vector-based semantic search.
    """
    # Check parameters
    if top_k <= 0:
        return {"error": "top_k must be positive"}

    if threshold < 0.0 or threshold > 1.0:
        return {"error": "threshold must be between 0.0 and 1.0"}

    if metric not in ["cosine", "euclidean", "dot"]:
        return {"error": f"Unsupported metric: {metric}"}

    # Create query vector
    query_vector = create_query_vector(query)

    # Record the query for history
    QUERY_HISTORY.append(
        {
            "id": str(uuid.uuid4()),
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "vector": query_vector[
                :10
            ],  # Store just the first 10 dimensions for display
            "parameters": {
                "top_k": top_k,
                "threshold": threshold,
                "metric": metric,
            },
        }
    )

    # Calculate similarity for each document
    results = []

    for doc_id, doc_vector in DOCUMENT_VECTORS.items():
        # Find the corresponding document
        doc = next((d for d in DOCUMENTS if d["id"] == doc_id), None)
        if not doc:
            continue

        # Calculate similarity score based on chosen metric
        if metric == "cosine":
            score = cosine_similarity(query_vector, doc_vector)
        elif metric == "euclidean":
            # Convert distance to similarity score (1 / (1 + distance))
            distance = euclidean_distance(query_vector, doc_vector)
            score = 1.0 / (1.0 + distance)
        else:  # dot product
            score = np.dot(query_vector, doc_vector)

        # Apply threshold
        if score >= threshold:
            results.append(
                {
                    "document_id": doc_id,
                    "title": doc["title"],
                    "score": score,
                    "document": doc,
                }
            )

    # Sort by score and take top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:top_k]

    return {
        "query": query,
        "results": results,
        "result_count": len(results),
        "metric": metric,
    }


@mcp.tool(
    annotations={
        "cost": 0.1,  # $0.10 per call
        "latency": "high",
        "rate_limit": 10,
        "needs_confirmation": True,
        "security_level": "authenticated",
    }
)
def store_vector(
    document_id: str,
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    vector: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Store a document with its vector embedding

    Args:
        document_id: Unique document identifier
        title: Document title
        content: Document content
        tags: Optional list of tags
        vector: Optional pre-computed vector (if not provided, one will be generated)

    This tool demonstrates vector storage operations.
    """
    # Validate input
    if not document_id or not title or not content:
        return {"error": "document_id, title, and content are required"}

    # Create the document
    doc = {
        "id": document_id,
        "title": title,
        "content": content,
        "tags": tags or [],
    }

    # Check for existing document
    existing_index = next(
        (i for i, d in enumerate(DOCUMENTS) if d["id"] == document_id), None
    )
    if existing_index is not None:
        # Update existing document
        DOCUMENTS[existing_index] = doc
        action = "updated"
    else:
        # Add new document
        DOCUMENTS.append(doc)
        action = "created"

    # Generate or use provided vector
    if vector is not None:
        # Validate vector dimensions
        if len(vector) != 128:
            return {"error": f"Vector must have 128 dimensions, got {len(vector)}"}

        # Store the provided vector
        DOCUMENT_VECTORS[document_id] = vector
    else:
        # Generate a new vector
        DOCUMENT_VECTORS[document_id] = create_query_vector(content)

    return {
        "status": "success",
        "message": f"Document {action} with vector embedding",
        "document_id": document_id,
        "vector_dimensions": len(DOCUMENT_VECTORS[document_id]),
    }


@mcp.tool(
    annotations={
        "cost": 0.05,  # $0.05 per call
        "latency": "medium",
        "rate_limit": 100,
        "needs_confirmation": False,
        "security_level": "authenticated",
        "streaming": True,
    }
)
def batch_embed_text(texts: List[str]) -> Dict[str, Any]:
    """
    Generate vector embeddings for multiple texts

    Args:
        texts: List of text strings to embed

    This tool demonstrates batch vector embedding generation.
    """
    # Check input
    if not texts:
        return {"error": "No texts provided"}

    # Check batch size limit
    batch_limit = mcp.server_capabilities["features"]["semantic_search"][
        "max_batch_size"
    ]
    if len(texts) > batch_limit:
        return {"error": f"Batch size exceeds limit of {batch_limit}"}

    # Simulate embedding generation with a delay proportional to batch size
    time.sleep(0.01 * len(texts))  # 10ms per text

    # Generate embeddings
    embeddings = []
    for text in texts:
        vector = create_query_vector(text)
        embeddings.append(vector)

    return {
        "count": len(texts),
        "dimensions": len(embeddings[0]),
        "embeddings": embeddings,
    }


@mcp.tool(
    annotations={
        "cost": 0.0,
        "latency": "low",
        "rate_limit": 1000,
        "needs_confirmation": False,
        "security_level": "public",
    }
)
def get_similar_documents(
    document_id: str, top_k: int = 3, include_self: bool = False
) -> Dict[str, Any]:
    """
    Find documents similar to a given document

    Args:
        document_id: ID of the reference document
        top_k: Maximum number of results to return
        include_self: Whether to include the reference document in results

    This tool demonstrates document similarity search.
    """
    # Check if document exists
    if document_id not in DOCUMENT_VECTORS:
        return {"error": f"Document not found: {document_id}"}

    # Get the reference vector
    reference_vector = DOCUMENT_VECTORS[document_id]

    # Get the reference document
    reference_doc = next((d for d in DOCUMENTS if d["id"] == document_id), None)

    # Calculate similarity for each document
    results = []

    for doc_id, doc_vector in DOCUMENT_VECTORS.items():
        # Skip self if not including
        if doc_id == document_id and not include_self:
            continue

        # Find the corresponding document
        doc = next((d for d in DOCUMENTS if d["id"] == doc_id), None)
        if not doc:
            continue

        # Calculate cosine similarity
        score = cosine_similarity(reference_vector, doc_vector)

        results.append(
            {
                "document_id": doc_id,
                "title": doc["title"],
                "score": score,
                "document": doc,
            }
        )

    # Sort by score and take top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:top_k]

    return {
        "reference_document": {
            "id": document_id,
            "title": reference_doc["title"] if reference_doc else None,
        },
        "similar_documents": results,
        "result_count": len(results),
    }


# Tools for exploring extended capabilities
@mcp.tool()
def get_server_capabilities() -> Dict[str, Any]:
    """
    Get detailed information about server capabilities

    This tool exposes the custom capabilities defined by this server.
    """
    return mcp.server_capabilities


@mcp.tool()
def get_tool_annotations() -> Dict[str, Any]:
    """
    Get metadata about all tools and their custom annotations

    This tool exposes the custom annotations used by the server's tools.
    """
    tools_with_annotations = []

    # Collect all tools that have custom annotations
    for name, tool in mcp.tools.items():
        if hasattr(tool, "annotations") and tool.annotations:
            tools_with_annotations.append(
                {
                    "name": name,
                    "description": tool.description,
                    "annotations": tool.annotations,
                }
            )

    return {
        "tool_count": len(tools_with_annotations),
        "tools": tools_with_annotations,
        "supported_annotations": mcp.server_capabilities["features"][
            "custom_tool_annotations"
        ]["supported_annotations"],
    }


@mcp.tool()
def get_query_history() -> Dict[str, Any]:
    """
    Get the history of semantic search queries

    This tool demonstrates tracking and analytics for vector operations.
    """
    return {
        "query_count": len(QUERY_HISTORY),
        "queries": QUERY_HISTORY,
    }


# Resources to expose extended capabilities
@mcp.resource("extensions://vector-storage")
def get_vector_storage_info() -> str:
    """Get information about the vector storage capability"""
    info = {
        "capability": "vector_storage",
        "description": "Store and retrieve document vectors for semantic search",
        "details": mcp.server_capabilities["features"]["vector_storage"],
        "document_count": len(DOCUMENT_VECTORS),
        "vector_dimensions": 128,
    }
    return json.dumps(info, indent=2)


@mcp.resource("extensions://semantic-search")
def get_semantic_search_info() -> str:
    """Get information about the semantic search capability"""
    info = {
        "capability": "semantic_search",
        "description": "Search for semantically similar documents",
        "details": mcp.server_capabilities["features"]["semantic_search"],
        "available_metrics": ["cosine", "euclidean", "dot"],
    }
    return json.dumps(info, indent=2)


@mcp.resource("extensions://tool-annotations")
def get_tool_annotations_info() -> str:
    """Get information about the custom tool annotations capability"""
    info = {
        "capability": "custom_tool_annotations",
        "description": "Extended metadata for tools",
        "details": mcp.server_capabilities["features"]["custom_tool_annotations"],
        "annotation_descriptions": {
            "cost": "Cost in USD per call",
            "latency": "Expected latency (low, medium, high)",
            "rate_limit": "Maximum calls per minute",
            "needs_confirmation": "Whether the tool requires explicit user confirmation",
            "security_level": "Required security level (public, authenticated, admin)",
            "streaming": "Whether the tool supports streaming responses",
        },
    }
    return json.dumps(info, indent=2)


@mcp.resource("documents/{document_id}")
def get_document(document_id: str) -> str:
    """Get a document by ID"""
    doc = next((d for d in DOCUMENTS if d["id"] == document_id), None)
    if not doc:
        return json.dumps({"error": f"Document not found: {document_id}"})

    # Include vector information if available
    vector = DOCUMENT_VECTORS.get(document_id)
    result = {**doc}

    if vector:
        result["vector_preview"] = vector[:10]  # Just the first 10 dimensions
        result["vector_dimensions"] = len(vector)

    return json.dumps(result, indent=2)


@mcp.resource("documents")
def get_all_documents() -> str:
    """Get all available documents"""
    result = {
        "count": len(DOCUMENTS),
        "documents": DOCUMENTS,
    }
    return json.dumps(result, indent=2)


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP PROTOCOL EXTENSIONS DEMO ===\n")
sys.stderr.write("This example demonstrates extending MCP with custom capabilities:\n")
sys.stderr.write("1. Vector storage for semantic document representation\n")
sys.stderr.write("2. Semantic search based on vector similarity\n")
sys.stderr.write("3. Custom tool annotations for extended metadata\n\n")
sys.stderr.write("Try these tools to see protocol extensions in action:\n")
sys.stderr.write("- vector_search: Search for documents similar to a query\n")
sys.stderr.write("- store_vector: Store a document with its vector embedding\n")
sys.stderr.write("- get_similar_documents: Find similar documents\n")
sys.stderr.write("- get_tool_annotations: See custom annotations on tools\n")
sys.stderr.write("- get_server_capabilities: See extended server capabilities\n")
sys.stderr.write("=== END PROTOCOL EXTENSIONS INFO ===\n\n")

# This server demonstrates extending the MCP protocol with custom capabilities
# Run with: uv run mcp dev 53-protocol-extensions.py
