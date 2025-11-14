#!/usr/bin/env python3
from fastmcp import FastMCP
import polars as pl
from polar_llama import tag_taxonomy, Provider
from typing import List, Optional, Dict, Any
import os

# Create an MCP server
mcp = FastMCP("Tagging MCP")


# Provider mapping
PROVIDER_MAP = {
    "claude": Provider.ANTHROPIC,
    "anthropic": Provider.ANTHROPIC,
    "openai": Provider.OPENAI,
    "gemini": Provider.GEMINI,
    "groq": Provider.GROQ,
    "bedrock": Provider.BEDROCK
}


def _create_taxonomy_from_tags(tags: List[str], field_name: str = "category") -> Dict[str, Any]:
    """Convert a simple list of tags into a taxonomy structure."""
    return {
        field_name: {
            "description": f"The most appropriate {field_name} for this text",
            "values": {tag: f"Content that belongs in the '{tag}' {field_name}" for tag in tags}
        }
    }


@mcp.tool()
def tag_csv(
    csv_path: str,
    taxonomy: List[str],
    text_column: str = "text",
    provider: str = "groq",
    model: str = "llama-3.3-70b-versatile",
    api_key: Optional[str] = None,
    output_path: Optional[str] = None,
    include_reasoning: bool = False,
    field_name: str = "category"
) -> dict:
    """
    Tag all rows in a CSV file based on a provided taxonomy using parallel LLM inference.

    Args:
        csv_path: Path to the CSV file to tag
        taxonomy: List of possible tags/categories to assign (e.g., ["technology", "business", "science"])
        text_column: Name of the column containing text to analyze (default: "text")
        provider: LLM provider - "claude", "openai", "gemini", "groq", or "bedrock" (default: "groq")
        model: Model identifier (default: "llama-3.3-70b-versatile")
        api_key: API key for the provider (if not set via environment variable)
        output_path: Optional path to save the tagged CSV (if not provided, returns preview)
        include_reasoning: Whether to include detailed reasoning and reflection in output (default: False)
        field_name: Name for the classification field (default: "category")

    Returns:
        Dictionary with status, preview of tagged data, and optionally the output path
    """
    try:
        # Read the CSV file
        df = pl.read_csv(csv_path)

        # Validate that the text column exists
        if text_column not in df.columns:
            return {
                "status": "error",
                "message": f"Column '{text_column}' not found in CSV. Available columns: {df.columns}"
            }

        # Set up API key if provided
        if api_key:
            if provider.lower() in ["claude", "anthropic"]:
                os.environ["ANTHROPIC_API_KEY"] = api_key
            else:
                os.environ[f"{provider.upper()}_API_KEY"] = api_key

        # Convert tag list to taxonomy format
        taxonomy_dict = _create_taxonomy_from_tags(taxonomy, field_name)

        # Get the provider enum
        provider_enum = PROVIDER_MAP.get(provider.lower())
        if not provider_enum:
            return {
                "status": "error",
                "message": f"Unsupported provider: {provider}. Use 'claude', 'openai', 'gemini', 'groq', or 'bedrock'"
            }

        # Apply taxonomy tagging using polar_llama
        df = df.with_columns(
            tags=tag_taxonomy(
                pl.col(text_column),
                taxonomy_dict,
                provider=provider_enum,
                model=model
            )
        )

        # Extract the selected tag value and confidence
        df = df.with_columns([
            pl.col("tags").struct.field(field_name).struct.field("value").alias(field_name),
            pl.col("tags").struct.field(field_name).struct.field("confidence").alias("confidence")
        ])

        # Optionally include reasoning and reflection
        if include_reasoning:
            df = df.with_columns([
                pl.col("tags").struct.field(field_name).struct.field("thinking").alias("thinking"),
                pl.col("tags").struct.field(field_name).struct.field("reflection").alias("reflection")
            ])

        # Check for errors
        error_rows = df.filter(
            pl.col("tags").struct.field("_error").is_not_null()
        )

        if len(error_rows) > 0:
            error_details = error_rows.select([
                text_column,
                pl.col("tags").struct.field("_error").alias("error"),
                pl.col("tags").struct.field("_details").alias("error_details")
            ]).to_dicts()
        else:
            error_details = None

        # Drop the raw tags column for cleaner output
        df = df.drop("tags")

        # Save to file if output path is provided
        if output_path:
            df.write_csv(output_path)
            result = {
                "status": "success",
                "message": f"Successfully tagged {len(df)} rows",
                "output_path": output_path,
                "preview": df.head(5).to_dicts(),
                "total_rows": len(df)
            }
            if error_details:
                result["errors"] = error_details
        else:
            result = {
                "status": "success",
                "message": f"Successfully tagged {len(df)} rows",
                "data": df.to_dicts(),
                "total_rows": len(df)
            }
            if error_details:
                result["errors"] = error_details

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def preview_csv(csv_path: str, rows: int = 5) -> dict:
    """
    Preview the first few rows of a CSV file to understand its structure.

    Args:
        csv_path: Path to the CSV file
        rows: Number of rows to preview (default: 5)

    Returns:
        Dictionary with column names and preview data
    """
    try:
        df = pl.read_csv(csv_path)
        return {
            "status": "success",
            "columns": df.columns,
            "rows": len(df),
            "preview": df.head(rows).to_dicts()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def tag_csv_advanced(
    csv_path: str,
    taxonomy: Dict[str, Dict[str, Any]],
    text_column: str = "text",
    provider: str = "groq",
    model: str = "llama-3.3-70b-versatile",
    api_key: Optional[str] = None,
    output_path: Optional[str] = None,
    include_reasoning: bool = False
) -> dict:
    """
    Tag CSV rows using a custom taxonomy with multiple fields and detailed value definitions.

    This is the advanced version that accepts a full taxonomy dictionary for multi-dimensional classification.

    Args:
        csv_path: Path to the CSV file to tag
        taxonomy: Full taxonomy dictionary with structure:
            {
                "field_name": {
                    "description": "What this field represents",
                    "values": {
                        "value1": "Definition of value1",
                        "value2": "Definition of value2"
                    }
                }
            }
        text_column: Name of the column containing text to analyze (default: "text")
        provider: LLM provider - "claude", "openai", "gemini", "groq", or "bedrock" (default: "groq")
        model: Model identifier (default: "llama-3.3-70b-versatile")
        api_key: API key for the provider (if not set via environment variable)
        output_path: Optional path to save the tagged CSV
        include_reasoning: Whether to include detailed reasoning and reflection (default: False)

    Returns:
        Dictionary with status, preview of tagged data, and optionally the output path

    Example taxonomy:
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
    """
    try:
        # Read the CSV file
        df = pl.read_csv(csv_path)

        # Validate that the text column exists
        if text_column not in df.columns:
            return {
                "status": "error",
                "message": f"Column '{text_column}' not found in CSV. Available columns: {df.columns}"
            }

        # Set up API key if provided
        if api_key:
            if provider.lower() in ["claude", "anthropic"]:
                os.environ["ANTHROPIC_API_KEY"] = api_key
            else:
                os.environ[f"{provider.upper()}_API_KEY"] = api_key

        # Get the provider enum
        provider_enum = PROVIDER_MAP.get(provider.lower())
        if not provider_enum:
            return {
                "status": "error",
                "message": f"Unsupported provider: {provider}. Use 'claude', 'openai', 'gemini', 'groq', or 'bedrock'"
            }

        # Apply taxonomy tagging
        df = df.with_columns(
            tags=tag_taxonomy(
                pl.col(text_column),
                taxonomy,
                provider=provider_enum,
                model=model
            )
        )

        # Extract values and confidence for each field
        field_columns = []
        for field_name in taxonomy.keys():
            field_columns.extend([
                pl.col("tags").struct.field(field_name).struct.field("value").alias(field_name),
                pl.col("tags").struct.field(field_name).struct.field("confidence").alias(f"{field_name}_confidence")
            ])

            if include_reasoning:
                field_columns.extend([
                    pl.col("tags").struct.field(field_name).struct.field("thinking").alias(f"{field_name}_thinking"),
                    pl.col("tags").struct.field(field_name).struct.field("reflection").alias(f"{field_name}_reflection")
                ])

        df = df.with_columns(field_columns)

        # Check for errors
        error_rows = df.filter(
            pl.col("tags").struct.field("_error").is_not_null()
        )

        if len(error_rows) > 0:
            error_details = error_rows.select([
                text_column,
                pl.col("tags").struct.field("_error").alias("error"),
                pl.col("tags").struct.field("_details").alias("error_details")
            ]).to_dicts()
        else:
            error_details = None

        # Drop the raw tags column
        df = df.drop("tags")

        # Save or return results
        if output_path:
            df.write_csv(output_path)
            result = {
                "status": "success",
                "message": f"Successfully tagged {len(df)} rows with {len(taxonomy)} fields",
                "output_path": output_path,
                "preview": df.head(5).to_dicts(),
                "total_rows": len(df),
                "fields": list(taxonomy.keys())
            }
            if error_details:
                result["errors"] = error_details
        else:
            result = {
                "status": "success",
                "message": f"Successfully tagged {len(df)} rows with {len(taxonomy)} fields",
                "data": df.to_dicts(),
                "total_rows": len(df),
                "fields": list(taxonomy.keys())
            }
            if error_details:
                result["errors"] = error_details

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def get_tagging_info() -> dict:
    """Get information about the tagging MCP server and supported providers"""
    return {
        "name": "Tagging MCP",
        "description": "MCP server for tagging CSV rows using polar_llama with parallel LLM inference",
        "version": "0.2.0",
        "supported_providers": [
            {
                "name": "groq",
                "models": [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "llama-3-groq-70b-tool-use",
                    "llama-3-groq-8b-tool-use",
                    "mixtral-8x7b-32768"
                ],
                "env_var": "GROQ_API_KEY",
                "recommended": True,
                "notes": "Fast inference with specialized tool-use models"
            },
            {
                "name": "claude",
                "models": [
                    "claude-sonnet-4-5",
                    "claude-haiku-4-5",
                    "claude-opus-4",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ],
                "env_var": "ANTHROPIC_API_KEY",
                "notes": "Latest models support fine-grained tool streaming"
            },
            {
                "name": "openai",
                "models": [
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4o-2024-08-06",
                    "gpt-4-turbo",
                    "gpt-4",
                    "gpt-3.5-turbo"
                ],
                "env_var": "OPENAI_API_KEY",
                "notes": "gpt-4o-2024-08-06 achieves 100% structured output reliability"
            },
            {
                "name": "gemini",
                "models": [
                    "gemini-2.5-pro",
                    "gemini-2.5-flash",
                    "gemini-2.0-flash",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash"
                ],
                "env_var": "GEMINI_API_KEY",
                "notes": "Gemini 2.x models have simplified function calling"
            },
            {
                "name": "bedrock",
                "models": [
                    "us.anthropic.claude-sonnet-4-5-v1:0",
                    "us.anthropic.claude-haiku-4-5-v1:0",
                    "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "anthropic.claude-3-opus-20240229-v1:0",
                    "anthropic.claude-3-sonnet-20240229-v1:0",
                    "anthropic.claude-3-haiku-20240307-v1:0"
                ],
                "env_var": "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY",
                "notes": "Use Converse API for tool calling"
            }
        ],
        "features": [
            "Parallel LLM inference for fast batch processing",
            "Multiple LLM provider support (Groq, Claude, OpenAI, Gemini, Bedrock)",
            "Taxonomy-based classification with reasoning and confidence scores",
            "Simple tag list or advanced multi-field taxonomy support",
            "Automatic error detection and reporting",
            "Optional detailed reasoning and reflection output"
        ],
        "tools": {
            "tag_csv": "Simple tagging with a list of categories",
            "tag_csv_advanced": "Advanced multi-dimensional classification with custom taxonomy",
            "preview_csv": "Preview CSV structure before tagging",
            "get_tagging_info": "Get server information"
        }
    }


# When running with fastmcp CLI, it will automatically call run()
# No need to manually call mcp.run() when using 'fastmcp run'
