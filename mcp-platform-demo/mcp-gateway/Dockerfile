FROM python:3.10-slim

WORKDIR /app

# Install essential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy requirements
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY gateway.py .
COPY config.yaml .

# Copy MCP servers
COPY mcp_servers/ ./mcp_servers/

# Expose ports
EXPOSE 8888
EXPOSE 9999

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_SERVER_PORT=8888
ENV WEBSOCKET_PORT=9999

# Run the server
CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8888"] 