# Tagging MCP

MCP server for tagging CSV rows using polar_llama with parallel LLM inference.

## Overview

This MCP server enables fast, parallel tagging of CSV data using multiple LLM providers. It leverages [polar_llama](https://github.com/daviddrummond95/polar_llama) to process rows concurrently, making it ideal for batch classification and tagging tasks.

## Features

- **Parallel Processing**: Tag hundreds or thousands of CSV rows concurrently
- **Multiple LLM Providers**: Support for 30+ models across Groq, Claude, OpenAI, Gemini, and AWS Bedrock
- **Structured Output**: Uses taxonomy-based classification with guaranteed schema compliance
- **Flexible Taxonomy**: Define custom tag lists or complex multi-field taxonomies
- **Optional Reasoning**: Include confidence levels, detailed thinking, and reflection for each tag
- **Latest Models**: Support for Claude 4.5, GPT-4o, Gemini 2.5, and specialized Llama tool-use models
- **Error Detection**: Automatic error tracking and reporting for failed classifications

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
Simple tagging with a list of categories. Perfect for basic classification tasks.

**Parameters:**
- `csv_path` (str): Path to the CSV file to tag
- `taxonomy` (List[str]): List of possible tags/categories (e.g., ["technology", "business", "science"])
- `text_column` (str, optional): Column containing text to analyze (default: "text")
- `provider` (str, optional): LLM provider - "claude", "openai", "gemini", "groq", or "bedrock" (default: "groq")
- `model` (str, optional): Model identifier (default: "llama-3.3-70b-versatile")
- `api_key` (str, optional): API key if not set via environment variable
- `output_path` (str, optional): Path to save tagged CSV
- `include_reasoning` (bool, optional): Include detailed reasoning and reflection (default: false)
- `field_name` (str, optional): Name for the classification field (default: "category")

**Returns:** Dictionary with status, tagged data preview, confidence scores, and optional errors

### `tag_csv_advanced`
Advanced multi-dimensional classification with custom taxonomy definitions. Use this for complex tagging with multiple fields.

**Parameters:**
- `csv_path` (str): Path to the CSV file to tag
- `taxonomy` (Dict): Full taxonomy dictionary with field definitions and value descriptions
- `text_column` (str, optional): Column containing text to analyze (default: "text")
- `provider` (str, optional): LLM provider (default: "groq")
- `model` (str, optional): Model identifier (default: "llama-3.3-70b-versatile")
- `api_key` (str, optional): API key if not set via environment variable
- `output_path` (str, optional): Path to save tagged CSV
- `include_reasoning` (bool, optional): Include detailed reasoning (default: false)

**Example Taxonomy:**
```json
{
  "sentiment": {
    "description": "The emotional tone of the text",
    "values": {
      "positive": "Text expresses positive emotions or favorable opinions",
      "negative": "Text expresses negative emotions or unfavorable opinions",
      "neutral": "Text is factual and objective"
    }
  },
  "urgency": {
    "description": "How urgent the content is",
    "values": {
      "high": "Requires immediate attention",
      "medium": "Should be addressed soon",
      "low": "Can be addressed at any time"
    }
  }
}
```

**Returns:** Dictionary with status, all field values, confidence scores per field, and optional reasoning

### `preview_csv`
Preview the first few rows of a CSV file to understand its structure.

**Parameters:**
- `csv_path` (str): Path to the CSV file
- `rows` (int, optional): Number of rows to preview (default: 5)

**Returns:** Dictionary with columns, row count, and preview data

### `get_tagging_info`
Get information about the tagging MCP server and supported providers.

**Returns:** Server metadata, supported providers, features, and available tools

## Example Usage

### Basic Tagging

1. **Preview your CSV:**
   ```
   Use preview_csv with csv_path="/path/to/data.csv"
   ```

2. **Simple category tagging:**
   ```
   Use tag_csv with:
   - csv_path="/path/to/data.csv"
   - taxonomy=["technology", "business", "science", "politics"]
   - text_column="description"
   - output_path="/path/to/tagged_output.csv"
   ```

3. **Include reasoning for transparency:**
   ```
   Use tag_csv with:
   - csv_path="/path/to/data.csv"
   - taxonomy=["urgent", "normal", "low_priority"]
   - field_name="priority"
   - include_reasoning=true
   ```

### Advanced Multi-Field Tagging

For complex classification with multiple dimensions:

```
Use tag_csv_advanced with:
- csv_path="/path/to/support_tickets.csv"
- taxonomy={
    "department": {
      "description": "Which department should handle this",
      "values": {
        "sales": "Product inquiries and purchases",
        "support": "Technical issues and bugs",
        "billing": "Payment and account questions"
      }
    },
    "priority": {
      "description": "How urgent this is",
      "values": {
        "urgent": "Service down or critical issue",
        "high": "Significant problem",
        "normal": "Standard request"
      }
    }
  }
- text_column="ticket_description"
- output_path="/path/to/classified_tickets.csv"
```

## Output Structure

### Basic Tagging Output
- Original CSV columns
- `{field_name}`: The selected tag
- `confidence`: Confidence score (0.0 to 1.0)
- `thinking`: Reasoning for each possible value (if `include_reasoning=true`)
- `reflection`: Overall analysis (if `include_reasoning=true`)

### Advanced Tagging Output
- Original CSV columns
- For each taxonomy field:
  - `{field_name}`: Selected value
  - `{field_name}_confidence`: Confidence score
  - `{field_name}_thinking`: Reasoning dict (if enabled)
  - `{field_name}_reflection`: Analysis (if enabled)

## Supported LLM Providers

All models listed below support tool calling/function calling and structured outputs required for taxonomy-based tagging.

### Groq (Recommended)
Fast inference with specialized tool-use models:
- `llama-3.3-70b-versatile` - Best balance of speed and quality
- `llama-3.1-8b-instant` - Fast with native function calling and JSON mode
- `llama-3-groq-70b-tool-use` - Specialized for tool use (preview)
- `llama-3-groq-8b-tool-use` - Fast specialized tool use (preview)
- `mixtral-8x7b-32768` - Large context window

### Claude (Anthropic)
Latest models with fine-grained tool streaming:
- `claude-sonnet-4-5` - Latest Sonnet with enhanced streaming
- `claude-haiku-4-5` - Latest Haiku, fast and cost-effective
- `claude-opus-4` - Most capable Claude model
- `claude-3-5-sonnet-20241022` - Strong performance
- `claude-3-opus-20240229` - Previous generation flagship
- `claude-3-sonnet-20240229` - Previous generation balanced
- `claude-3-haiku-20240307` - Previous generation fast

### OpenAI
Models with structured outputs support:
- `gpt-4o` - Latest multimodal model
- `gpt-4o-mini` - Fast and cost-effective
- `gpt-4o-2024-08-06` - 100% structured output reliability
- `gpt-4-turbo` - Previous flagship
- `gpt-4` - Original GPT-4
- `gpt-3.5-turbo` - Fast and economical

### Google Gemini
Gemini 2.x models with simplified function calling:
- `gemini-2.5-pro` - Latest Pro with enhanced capabilities
- `gemini-2.5-flash` - Latest Flash, fast and efficient
- `gemini-2.0-flash` - Previous generation Flash
- `gemini-1.5-pro` - Multimodal with long context
- `gemini-1.5-flash` - Fast 1.5 generation

### AWS Bedrock
Claude models via Bedrock (use Converse API):
- `us.anthropic.claude-sonnet-4-5-v1:0` - Latest Sonnet
- `us.anthropic.claude-haiku-4-5-v1:0` - Latest Haiku
- `anthropic.claude-3-5-sonnet-20241022-v2:0` - Claude 3.5 Sonnet
- `anthropic.claude-3-opus-20240229-v1:0` - Claude 3 Opus
- `anthropic.claude-3-sonnet-20240229-v1:0` - Claude 3 Sonnet
- `anthropic.claude-3-haiku-20240307-v1:0` - Claude 3 Haiku

## Key Features

✨ **Detailed Reasoning**: For each tag, see why the model chose it
🔍 **Reflection**: Model reflects on its analysis
📊 **Confidence Scores**: Know how confident each classification is (0.0-1.0)
⚡ **Parallel Processing**: All rows processed concurrently
🎯 **Error Detection**: Automatic error tracking and reporting
🔧 **Flexible**: Simple list or complex multi-field taxonomies

## License

MIT
