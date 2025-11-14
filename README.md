# Tagging MCP

MCP server for tagging CSV rows using polar_llama with parallel LLM inference.

## Overview

This MCP server enables fast, parallel tagging of CSV data using multiple LLM providers. It leverages [polar_llama](https://github.com/daviddrummond95/polar_llama) to process rows concurrently, making it ideal for batch classification and tagging tasks.

## Features

- **Parallel Processing**: Tag hundreds or thousands of CSV rows concurrently
- **Multiple LLM Providers**: Support for Claude (Anthropic), OpenAI, Gemini, and Groq
- **Structured Output**: Uses Pydantic models for consistent, type-safe results
- **Flexible Taxonomy**: Define custom tag lists for your use case
- **Optional Reasoning**: Include confidence levels and explanations for tags

## Installation

### Prerequisites

- Python 3.12+
- UV package manager
- API key for at least one LLM provider

### Environment Setup

1. Clone this repository
2. Create a `.env` file with your API keys:
   ```bash
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here
   ```

## Claude Desktop Configuration

### Option 1: Local Development (Recommended)

Run directly without containers:

```json
{
  "mcpServers": {
    "tagging-mcp": {
      "command": "uv",
      "args": ["run", "fastmcp", "run", "/path/to/tagging_mcp/tagging.py"]
    }
  }
}
```

### Option 2: Container Deployment

1. Build the container:
   ```bash
   container build -t tagging_mcp .
   ```

2. Configure Claude Desktop:
   ```json
   {
     "mcpServers": {
       "tagging-mcp": {
         "command": "container",
         "args": ["run", "--interactive", "tagging_mcp"]
       }
     }
   }
   ```

## Available Tools

### `tag_csv`
Tag all rows in a CSV file based on a provided taxonomy.

**Parameters:**
- `csv_path` (str): Path to the CSV file to tag
- `taxonomy` (List[str]): List of possible tags/categories to assign
- `text_column` (str, optional): Column containing text to analyze (default: "text")
- `provider` (str, optional): LLM provider - "claude", "openai", "gemini", or "groq" (default: "claude")
- `model` (str, optional): Model identifier (default: "claude-3-5-sonnet-20241022")
- `api_key` (str, optional): API key if not set via environment variable
- `output_path` (str, optional): Path to save tagged CSV
- `include_reasoning` (bool, optional): Include confidence and reasoning (default: false)

**Returns:** Dictionary with status, preview/data, and optional output path

### `preview_csv`
Preview the first few rows of a CSV file to understand its structure.

**Parameters:**
- `csv_path` (str): Path to the CSV file
- `rows` (int, optional): Number of rows to preview (default: 5)

**Returns:** Dictionary with columns, row count, and preview data

### `get_tagging_info`
Get information about the tagging MCP server and supported providers.

**Returns:** Server metadata, supported providers, and features

## Example Usage

1. **Preview your CSV:**
   ```
   Use preview_csv with csv_path="/path/to/data.csv"
   ```

2. **Tag the data:**
   ```
   Use tag_csv with:
   - csv_path="/path/to/data.csv"
   - taxonomy=["technology", "business", "science", "politics"]
   - text_column="description"
   - output_path="/path/to/tagged_output.csv"
   ```

## Supported LLM Providers

- **Claude (Anthropic)**: claude-3-5-sonnet-20241022, claude-3-opus-20240229
- **OpenAI**: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- **Gemini**: gemini-1.5-pro, gemini-1.5-flash
- **Groq**: llama-3.1-70b-versatile, mixtral-8x7b-32768

## License

MIT
