# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Node.js (using NodeSource for faster install)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv (for uvx command, used by some MCP servers like mcp-server-fetch)
RUN pip install uv

# Copy the requirements file into the container at /app
# We assume requirements.txt is at the root of Omni-Agent
COPY Omni-Agent/requirements.txt /app/

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Omni-Agent (Your Application)
COPY Omni-Agent/src /app/src
COPY Omni-Agent/config /app/config

# Expose port 8000 for Omni-Agent Server
EXPOSE 8000

# Define environment variable for Omni-Agent
ENV MODULE_NAME="src.server.app"
ENV VARIABLE_NAME="app"
ENV PORT="8000"

# Run Omni-Agent Server
CMD ["uvicorn", "src.server.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
