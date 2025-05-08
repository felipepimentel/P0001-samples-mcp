import getpass
import io
import json
import os
import sys
from base64 import b64encode
from datetime import datetime
from typing import Any, Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from mcp.server.fastmcp import FastMCP
from PIL import Image

# Disable GUI for matplotlib
matplotlib.use("Agg")

# Workaround for os.getlogin issues in some environments
os.getlogin = getpass.getuser

# Create an MCP server
mcp = FastMCP("ContentTypeNegotiationDemo")

# Sample binary data for testing
SAMPLE_SVG = """
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" stroke="black" stroke-width="4" fill="blue" />
</svg>
"""

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>MCP Content-Type Demo</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
    h1 { color: #333; }
    .box { background: #f0f0f0; padding: 10px; border-radius: 5px; }
  </style>
</head>
<body>
  <h1>MCP Content Type Negotiation</h1>
  <div class="box">
    <p>This HTML content is returned via MCP with the appropriate content type.</p>
  </div>
</body>
</html>
"""

SAMPLE_CSV = """
id,name,value,timestamp
1,temperature,22.5,2025-01-15T10:30:00Z
2,humidity,45.2,2025-01-15T10:30:00Z
3,pressure,1013.2,2025-01-15T10:30:00Z
4,wind_speed,12.3,2025-01-15T10:30:00Z
5,rainfall,0.0,2025-01-15T10:30:00Z
"""

# Content type registry - maps extensions to MIME types
CONTENT_TYPES = {
    "json": "application/json",
    "html": "text/html",
    "txt": "text/plain",
    "md": "text/markdown",
    "csv": "text/csv",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
    "bin": "application/octet-stream",
}


# Resource handlers for different content types
@mcp.resource("content/text.txt")
def get_text_content() -> str:
    """Get plain text content"""
    content = "This is a plain text file returned with text/plain content type.\n\nMCP can handle various content types and represent them appropriately."
    return content


@mcp.resource("content/document.md")
def get_markdown_content() -> str:
    """Get markdown content"""
    content = """# Markdown Document

## Introduction to MCP Content Types

The Model Context Protocol supports various content types:

* Plain text
* JSON
* HTML
* Markdown
* CSV data
* Images
* Binary data

## Code Examples

```python
@mcp.resource("content/document.md")
def get_markdown_content() -> str:
    \"\"\"Get markdown content\"\"\"
    return markdown_content
```

## Benefits

- Standards-based MIME types
- Proper content type identification
- Wide range of supported formats
"""
    return content


@mcp.resource("content/data.json")
def get_json_content() -> str:
    """Get JSON data"""
    data = {
        "protocol": "MCP",
        "version": "2024-11-05",
        "content_types": list(CONTENT_TYPES.values()),
        "features": [
            "Content type negotiation",
            "Binary data support",
            "Embedded resources",
            "URI templates",
        ],
        "timestamp": datetime.now().isoformat(),
    }
    return json.dumps(data, indent=2)


@mcp.resource("content/page.html")
def get_html_content() -> str:
    """Get HTML content"""
    return SAMPLE_HTML


@mcp.resource("content/data.csv")
def get_csv_content() -> str:
    """Get CSV data"""
    return SAMPLE_CSV


@mcp.resource("content/image.svg")
def get_svg_content() -> str:
    """Get SVG image"""
    return SAMPLE_SVG


@mcp.resource("content/plot.png")
def get_plot_image() -> str:
    """Generate and return a PNG plot image"""
    # Create a simple matplotlib plot
    plt.figure(figsize=(8, 6))

    # Generate sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)

    # Create the plot
    plt.plot(x, y1, label="sin(x)")
    plt.plot(x, y2, label="cos(x)")
    plt.title("Sine and Cosine Functions")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.legend()

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()

    # Convert to base64
    buf.seek(0)
    img_data = buf.getvalue()
    base64_data = b64encode(img_data).decode("utf-8")

    # Return the base64-encoded PNG data
    return base64_data


# Custom resource handler that includes content-type in function signature
@mcp.resource("custom/{filename}")
def get_custom_resource(filename: str) -> (str, str):
    """
    Get custom content with dynamic content-type

    This function returns a tuple of (content, content_type)
    """
    # Extract file extension
    parts = filename.split(".")
    if len(parts) > 1:
        ext = parts[-1].lower()
        content_type = CONTENT_TYPES.get(ext, "text/plain")
    else:
        content_type = "text/plain"

    # Generate content based on extension
    if ext == "json":
        content = json.dumps(
            {
                "filename": filename,
                "type": "json",
                "custom": True,
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )
    elif ext == "txt":
        content = (
            f"Custom text file: {filename}\nGenerated at: {datetime.now().isoformat()}"
        )
    elif ext == "html":
        content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Custom HTML: {filename}</title>
        </head>
        <body>
            <h1>Custom Generated HTML</h1>
            <p>Filename: {filename}</p>
            <p>Generated at: {datetime.now().isoformat()}</p>
        </body>
        </html>
        """
    else:
        content = f"Unknown format for {filename}"

    return content, content_type


# Tools for working with different content types
@mcp.tool()
def list_available_content() -> Dict[str, Any]:
    """List all available content resources and their types"""
    content_list = [
        {
            "uri": "content/text.txt",
            "type": "text/plain",
            "description": "Plain text sample",
        },
        {
            "uri": "content/document.md",
            "type": "text/markdown",
            "description": "Markdown document",
        },
        {
            "uri": "content/data.json",
            "type": "application/json",
            "description": "JSON data",
        },
        {
            "uri": "content/page.html",
            "type": "text/html",
            "description": "HTML content",
        },
        {"uri": "content/data.csv", "type": "text/csv", "description": "CSV data"},
        {
            "uri": "content/image.svg",
            "type": "image/svg+xml",
            "description": "SVG image",
        },
        {
            "uri": "content/plot.png",
            "type": "image/png",
            "description": "Generated PNG plot",
        },
    ]

    return {
        "count": len(content_list),
        "content": content_list,
        "custom_endpoint": "custom/{filename}",
        "supported_extensions": list(CONTENT_TYPES.keys()),
    }


@mcp.tool()
def generate_dynamic_content(content_type: str, content: str) -> Dict[str, Any]:
    """
    Generate dynamic content with the specified content type

    Args:
        content_type: MIME type for the content
        content: The content to return with the specified type

    Returns the content with the appropriate content type.
    """
    # Validate content type
    if "/" not in content_type:
        return {
            "error": f"Invalid content type: {content_type}. Must be in format 'type/subtype'"
        }

    # For binary data that's passed as text, we'd need to decode it
    # For this example, we're keeping everything as text for simplicity

    return {
        "content_type": content_type,
        "content": content,
        "length": len(content),
        "timestamp": datetime.now().isoformat(),
    }


@mcp.tool()
def generate_image(
    width: int = 300,
    height: int = 200,
    shape: str = "rectangle",
    color: str = "blue",
    format: str = "png",
) -> Dict[str, Any]:
    """
    Generate a simple image with the specified parameters

    Args:
        width: Image width in pixels
        height: Image height in pixels
        shape: Shape to draw ('rectangle', 'circle', or 'triangle')
        color: Color to use (name or hex code)
        format: Image format ('png' or 'jpeg')

    Returns base64-encoded image data.
    """
    # Validate parameters
    if width <= 0 or height <= 0:
        return {"error": "Width and height must be positive"}

    if width > 1000 or height > 1000:
        return {"error": "Maximum allowed dimensions are 1000x1000"}

    if format not in ["png", "jpeg"]:
        return {"error": "Format must be 'png' or 'jpeg'"}

    if shape not in ["rectangle", "circle", "triangle"]:
        return {
            "error": f"Shape '{shape}' not supported. Use 'rectangle', 'circle', or 'triangle'"
        }

    # Create a blank image
    image = Image.new("RGB", (width, height), (255, 255, 255))

    # Create drawing context
    from PIL import ImageDraw

    draw = ImageDraw.Draw(image)

    # Determine the color
    try:
        # Handle hex codes
        if color.startswith("#"):
            color_tuple = tuple(
                int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
            )
        else:
            # Use named color
            color_tuple = color
    except:
        color_tuple = "blue"  # Default if parsing fails

    # Draw the requested shape
    if shape == "rectangle":
        draw.rectangle([(10, 10), (width - 10, height - 10)], fill=color_tuple)
    elif shape == "circle":
        draw.ellipse([(10, 10), (width - 10, height - 10)], fill=color_tuple)
    elif shape == "triangle":
        # Create a triangle that fits within the image
        points = [
            (width // 2, 10),  # Top
            (10, height - 10),  # Bottom left
            (width - 10, height - 10),  # Bottom right
        ]
        draw.polygon(points, fill=color_tuple)

    # Save the image to a bytes buffer
    buf = io.BytesIO()
    image.save(buf, format=format)
    buf.seek(0)

    # Get the binary data and encode as base64
    img_data = buf.getvalue()
    base64_data = b64encode(img_data).decode("utf-8")

    # Determine content type
    content_type = f"image/{format}"

    return {
        "content_type": content_type,
        "width": width,
        "height": height,
        "shape": shape,
        "color": color,
        "format": format,
        "content": base64_data,
    }


@mcp.tool()
def convert_content_type(content: str, from_type: str, to_type: str) -> Dict[str, Any]:
    """
    Convert content from one type to another

    Args:
        content: The content to convert
        from_type: Source content type
        to_type: Target content type

    This demonstrates content type conversion operations.
    """
    # Handle some simple conversions

    # JSON to CSV
    if from_type == "application/json" and to_type == "text/csv":
        try:
            # Parse JSON
            data = json.loads(content)

            # Handle various JSON structures
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                # Array of objects - use keys from first object as headers
                headers = data[0].keys()

                # Create CSV
                csv_lines = [",".join(headers)]
                for item in data:
                    row = [str(item.get(header, "")) for header in headers]
                    csv_lines.append(",".join(row))

                result = "\n".join(csv_lines)
                return {
                    "original_type": from_type,
                    "converted_type": to_type,
                    "content": result,
                }
            else:
                return {"error": "JSON structure not supported for CSV conversion"}
        except Exception as e:
            return {"error": f"JSON to CSV conversion failed: {str(e)}"}

    # CSV to JSON
    elif from_type == "text/csv" and to_type == "application/json":
        try:
            # Parse CSV
            lines = content.strip().split("\n")
            headers = lines[0].split(",")

            # Create JSON
            data = []
            for line in lines[1:]:
                values = line.split(",")
                if len(values) == len(headers):
                    row = {headers[i]: values[i] for i in range(len(headers))}
                    data.append(row)

            result = json.dumps(data, indent=2)
            return {
                "original_type": from_type,
                "converted_type": to_type,
                "content": result,
            }
        except Exception as e:
            return {"error": f"CSV to JSON conversion failed: {str(e)}"}

    # Plain text to HTML
    elif from_type == "text/plain" and to_type == "text/html":
        escaped = (
            content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Converted Text</title>
        </head>
        <body>
            <pre>{escaped}</pre>
        </body>
        </html>
        """

        return {
            "original_type": from_type,
            "converted_type": to_type,
            "content": html,
        }

    # Markdown to HTML
    elif from_type == "text/markdown" and to_type == "text/html":
        try:
            # Simple markdown conversion
            # For real applications, use a proper markdown library
            lines = content.split("\n")
            html_lines = []

            for line in lines:
                # Headers
                if line.startswith("# "):
                    html_lines.append(f"<h1>{line[2:]}</h1>")
                elif line.startswith("## "):
                    html_lines.append(f"<h2>{line[3:]}</h2>")
                elif line.startswith("### "):
                    html_lines.append(f"<h3>{line[4:]}</h3>")
                # Lists
                elif line.startswith("* "):
                    html_lines.append(f"<li>{line[2:]}</li>")
                elif line.startswith("- "):
                    html_lines.append(f"<li>{line[2:]}</li>")
                # Code blocks
                elif line.startswith("```"):
                    if html_lines and html_lines[-1] == "<pre><code>":
                        html_lines.append("</code></pre>")
                    else:
                        html_lines.append("<pre><code>")
                # Paragraphs
                elif line.strip() == "":
                    html_lines.append("<p></p>")
                else:
                    html_lines.append(line)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Converted Markdown</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                {" ".join(html_lines)}
            </body>
            </html>
            """

            return {
                "original_type": from_type,
                "converted_type": to_type,
                "content": html,
            }
        except Exception as e:
            return {"error": f"Markdown to HTML conversion failed: {str(e)}"}

    else:
        return {"error": f"Conversion from {from_type} to {to_type} is not supported"}


# Explain what this demo does when run with MCP CLI
sys.stderr.write("\n=== MCP CONTENT TYPE NEGOTIATION DEMO ===\n")
sys.stderr.write("This example demonstrates content type handling in MCP:\n")
sys.stderr.write("1. Resources can be served with appropriate MIME types\n")
sys.stderr.write("2. Binary data can be represented and transferred (as base64)\n")
sys.stderr.write("3. Dynamic content can be generated with specified types\n")
sys.stderr.write("4. Content can be converted between different formats\n\n")
sys.stderr.write("Try these resources and tools to see content types in action:\n")
sys.stderr.write("- Use list_available_content to see all available content types\n")
sys.stderr.write("- Access resources like content/text.txt or content/plot.png\n")
sys.stderr.write("- Use generate_image to create custom images\n")
sys.stderr.write("- Use convert_content_type to transform between formats\n")
sys.stderr.write("=== END CONTENT TYPE NEGOTIATION INFO ===\n\n")

# This server demonstrates MCP content type negotiation
# Run with: uv run mcp dev 51-content-type-negotiation.py
