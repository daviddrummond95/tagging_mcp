#!/usr/bin/env python3
from fastmcp import FastMCP
import polars as pl
from polar_llama import add_claude, add_openai, add_gemini, add_groq
from pydantic import BaseModel, Field
from typing import List, Optional
import os

# Create an MCP server
mcp = FastMCP("Tagging MCP")


class TaggingResult(BaseModel):
    """Result of tagging operation"""
    tags: List[str] = Field(description="The assigned tags from the taxonomy")
    confidence: Optional[str] = Field(default=None, description="Confidence level of the tagging")
    reasoning: Optional[str] = Field(default=None, description="Brief explanation for the tags")


@mcp.tool()
def tag_csv(
    csv_path: str,
    taxonomy: List[str],
    text_column: str = "text",
    provider: str = "claude",
    model: str = "claude-3-5-sonnet-20241022",
    api_key: Optional[str] = None,
    output_path: Optional[str] = None,
    include_reasoning: bool = False
) -> dict:
    """
    Tag all rows in a CSV file based on a provided taxonomy using parallel LLM inference.

    Args:
        csv_path: Path to the CSV file to tag
        taxonomy: List of possible tags/categories to assign
        text_column: Name of the column containing text to analyze (default: "text")
        provider: LLM provider - "claude", "openai", "gemini", or "groq" (default: "claude")
        model: Model identifier (default: "claude-3-5-sonnet-20241022")
        api_key: API key for the provider (if not set via environment variable)
        output_path: Optional path to save the tagged CSV (if not provided, returns preview)
        include_reasoning: Whether to include reasoning in the output (default: False)

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

        # Create the tagging prompt
        taxonomy_str = "\n".join([f"- {tag}" for tag in taxonomy])

        if include_reasoning:
            system_prompt = f"""You are a text classification expert. Your task is to analyze text and assign relevant tags from a predefined taxonomy.

Available tags:
{taxonomy_str}

Rules:
- You can assign one or multiple tags from the taxonomy
- Only use tags from the provided list
- Be precise and choose the most relevant tags
- Provide your confidence level (high/medium/low)
- Briefly explain your reasoning"""

            user_prompt_template = "Analyze and tag the following text:\n\n{text}"
        else:
            system_prompt = f"""You are a text classification expert. Your task is to analyze text and assign relevant tags from a predefined taxonomy.

Available tags:
{taxonomy_str}

Rules:
- You can assign one or multiple tags from the taxonomy
- Only use tags from the provided list
- Be precise and choose the most relevant tags"""

            user_prompt_template = "Analyze and tag the following text:\n\n{text}"

        # Create user prompts for each row
        df = df.with_columns(
            pl.col(text_column).map_elements(
                lambda x: user_prompt_template.format(text=x),
                return_dtype=pl.Utf8
            ).alias("prompt")
        )

        # Set up API key if provided
        if api_key:
            os.environ[f"{provider.upper()}_API_KEY"] = api_key

        # Add LLM inference based on provider
        if provider.lower() == "claude":
            df = add_claude(
                df=df,
                user_prompt_col="prompt",
                system_prompt=system_prompt,
                model=model,
                response_model=TaggingResult,
                response_col="tagging_result"
            )
        elif provider.lower() == "openai":
            df = add_openai(
                df=df,
                user_prompt_col="prompt",
                system_prompt=system_prompt,
                model=model,
                response_model=TaggingResult,
                response_col="tagging_result"
            )
        elif provider.lower() == "gemini":
            df = add_gemini(
                df=df,
                user_prompt_col="prompt",
                system_prompt=system_prompt,
                model=model,
                response_model=TaggingResult,
                response_col="tagging_result"
            )
        elif provider.lower() == "groq":
            df = add_groq(
                df=df,
                user_prompt_col="prompt",
                system_prompt=system_prompt,
                model=model,
                response_model=TaggingResult,
                response_col="tagging_result"
            )
        else:
            return {
                "status": "error",
                "message": f"Unsupported provider: {provider}. Use 'claude', 'openai', 'gemini', or 'groq'"
            }

        # Extract tags from the structured response
        df = df.with_columns([
            pl.col("tagging_result").struct.field("tags").alias("tags"),
        ])

        if include_reasoning:
            df = df.with_columns([
                pl.col("tagging_result").struct.field("confidence").alias("confidence"),
                pl.col("tagging_result").struct.field("reasoning").alias("reasoning")
            ])

        # Drop the prompt and raw result columns for cleaner output
        df = df.drop(["prompt", "tagging_result"])

        # Save to file if output path is provided
        if output_path:
            df.write_csv(output_path)
            result = {
                "status": "success",
                "message": f"Successfully tagged {len(df)} rows",
                "output_path": output_path,
                "preview": df.head(5).to_dicts()
            }
        else:
            result = {
                "status": "success",
                "message": f"Successfully tagged {len(df)} rows",
                "data": df.to_dicts()
            }

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
def get_tagging_info() -> dict:
    """Get information about the tagging MCP server and supported providers"""
    return {
        "name": "Tagging MCP",
        "description": "MCP server for tagging CSV rows using polar_llama with parallel LLM inference",
        "version": "0.1.0",
        "supported_providers": [
            {
                "name": "claude",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                "env_var": "ANTHROPIC_API_KEY"
            },
            {
                "name": "openai",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "env_var": "OPENAI_API_KEY"
            },
            {
                "name": "gemini",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
                "env_var": "GEMINI_API_KEY"
            },
            {
                "name": "groq",
                "models": ["llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
                "env_var": "GROQ_API_KEY"
            }
        ],
        "features": [
            "Parallel LLM inference for fast batch processing",
            "Multiple LLM provider support",
            "Structured output with Pydantic models",
            "Configurable taxonomy-based tagging",
            "Optional confidence and reasoning output"
        ]
    }


# When running with fastmcp CLI, it will automatically call run()
# No need to manually call mcp.run() when using 'fastmcp run'
