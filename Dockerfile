# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Set working directory
WORKDIR /app

# Copy dependency files and install dependencies as root for better caching
COPY pyproject.toml ./
RUN uv sync --no-install-project

# Copy application code
COPY tagging.py ./

# Set environment variables
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV CONTAINER=true
ENV MCP_TRANSPORT=stdio

# Change ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Run the MCP server
CMD ["uv", "run", "fastmcp", "run", "tagging.py", "--transport", "stdio"]
