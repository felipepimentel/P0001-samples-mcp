FROM python:3.10-slim

WORKDIR /app

# Install essential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY orchestrator.py .
COPY scenarios/ ./scenarios/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AUTO_START_SCENARIOS=true
ENV SCENARIO_INTERVAL=300
ENV DEMO_MODE=true

# Expose metrics port
EXPOSE 8091
# Expose API port
EXPOSE 8090

# Run the orchestrator
CMD ["python", "orchestrator.py", "--init-all", "--start-scenarios"] 