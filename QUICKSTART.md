# Quick Start Guide

## Prerequisites
- Apple container tool
- UV (for local development)

## Build & Run with Apple Containers

```bash
# Start container service (first time only)
container system start

# Build the container
container build --tag tagging_mcp .

# Run with HTTP transport (default)
container run --interactive tagging_mcp

# Check logs
container logs tagging_mcp
```

## Local Development

```bash
# Install dependencies
uv sync

# Run with stdio transport (default for local)
uv run python hello.py

# Run with HTTP transport locally
MCP_TRANSPORT=streamable-http uv run python hello.py

# Run with custom settings
MCP_TRANSPORT=streamable-http FASTMCP_PORT=8080 uv run python hello.py
```

## Environment Variables

- `MCP_TRANSPORT`: Transport method (stdio, streamable-http, sse)
- `FASTMCP_HOST`: HTTP server host (default: 0.0.0.0)
- `FASTMCP_PORT`: HTTP server port (default: 8000)
- `CONTAINER`: Set to "true" when running in container

## Testing Your MCP Server

### With stdio transport:
```bash
# Run interactively
npx @modelcontextprotocol/inspector uv run fastmcp run hello.py --transport stdio
```

## Next Steps

1. Edit `hello.py` to add your custom MCP tools
2. Update `pyproject.toml` with any additional dependencies
3. Rebuild and test your container
4. Deploy to your infrastructure
