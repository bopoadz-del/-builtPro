#!/usr/bin/env python3
"""
Kimi AI (Moonshot) MCP Server for BuilTPro Brain AI

Exposes three tools via the Model Context Protocol:
  - kimi_vision_analyze: Analyze construction images
  - kimi_code_generate: Generate code for construction data analysis
  - kimi_document_analyze: Analyze construction documents (long-context)

Usage:
    python mcp-servers/kimi/server.py

Requires:
    MOONSHOT_API_KEY environment variable
    pip install mcp httpx
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

# Ensure the package is importable when run directly
sys.path.insert(0, os.path.dirname(__file__))

from kimi_client import KimiAPIError, KimiClient, KimiConfigurationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

VISION_SYSTEM = (
    "You are a construction site image analyst. Analyze the provided image and "
    "give detailed observations about: construction progress, safety compliance, "
    "material identification, structural elements, equipment usage, and any "
    "potential issues. Be precise and technical in your analysis."
)

CODE_SYSTEM = (
    "You are a code generator for the BuilTPro Brain AI platform. Generate clean, "
    "well-documented code for construction data analysis tasks. The platform uses "
    "Python 3.11+, FastAPI, SQLAlchemy, pandas, numpy, and scikit-learn. Common "
    "tasks include: EVM (Earned Value Management) calculations, QTO (Quantity "
    "Take-Off) processing, schedule analysis (SPI/CPI), cost forecasting with "
    "Monte Carlo simulation, and IFC/BIM data processing."
)

DOCUMENT_SYSTEM = (
    "You are a construction document analyst. Analyze the provided document text "
    "and extract key information including: action items, deadlines, responsible "
    "parties, cost figures, schedule milestones, risk items, change orders, and "
    "compliance requirements. Be thorough and structured in your analysis."
)


# ---------------------------------------------------------------------------
# MCP Server setup
# ---------------------------------------------------------------------------


def create_server():
    """Create and configure the MCP server with Kimi tools."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError:
        print(
            "Error: mcp package not installed. Install with: pip install mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    server = Server("builtpro-kimi-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="kimi_vision_analyze",
                description=(
                    "Analyze construction images using Kimi AI vision capabilities. "
                    "Use for: site photos, architectural drawings, floor plans, "
                    "progress verification photos, safety compliance images."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "What to analyze in the image",
                        },
                        "image_url": {
                            "type": "string",
                            "description": "URL of the image to analyze",
                        },
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image data (alternative to URL)",
                        },
                        "model": {
                            "type": "string",
                            "description": "Kimi model to use (default: kimi-k2.5)",
                            "default": "kimi-k2.5",
                        },
                    },
                    "required": ["prompt"],
                },
            ),
            Tool(
                name="kimi_code_generate",
                description=(
                    "Generate code for construction data analysis using Kimi AI. "
                    "Use for: EVM calculations, schedule analysis scripts, cost "
                    "estimation tools, QTO calculators, data transformation scripts."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Description of the code to generate",
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language (default: python)",
                            "default": "python",
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional project context or requirements",
                        },
                        "model": {
                            "type": "string",
                            "description": "Kimi model to use (default: kimi-k2.5)",
                            "default": "kimi-k2.5",
                        },
                    },
                    "required": ["prompt"],
                },
            ),
            Tool(
                name="kimi_document_analyze",
                description=(
                    "Analyze construction documents using Kimi AI with long-context "
                    "support (up to 128k tokens). Use for: contracts, specifications, "
                    "RFIs, submittals, change orders, meeting minutes, safety documents."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "What to analyze or extract from the document",
                        },
                        "document_text": {
                            "type": "string",
                            "description": "Full text content of the document",
                        },
                        "model": {
                            "type": "string",
                            "description": "Kimi model (default: moonshot-v1-128k for long docs)",
                            "default": "moonshot-v1-128k",
                        },
                    },
                    "required": ["prompt"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            client = KimiClient()
        except KimiConfigurationError as exc:
            return [TextContent(type="text", text=f"Configuration error: {exc}")]

        try:
            if name == "kimi_vision_analyze":
                result = await _handle_vision(client, arguments)
            elif name == "kimi_code_generate":
                result = await _handle_code(client, arguments)
            elif name == "kimi_document_analyze":
                result = await _handle_document(client, arguments)
            else:
                result = f"Unknown tool: {name}"
        except KimiAPIError as exc:
            result = f"Kimi API error: {exc}"

        return [TextContent(type="text", text=result)]

    return server


async def _handle_vision(client: KimiClient, args: dict) -> str:
    prompt = args["prompt"]
    image_url = args.get("image_url")
    image_base64 = args.get("image_base64")
    model = args.get("model", "kimi-k2.5")

    if image_base64 and not image_url:
        image_url = f"data:image/png;base64,{image_base64}"

    user_content: list | str
    if image_url:
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    else:
        user_content = prompt

    messages = [
        {"role": "system", "content": VISION_SYSTEM},
        {"role": "user", "content": user_content},
    ]
    return await client.complete(messages, model=model)


async def _handle_code(client: KimiClient, args: dict) -> str:
    prompt = args["prompt"]
    language = args.get("language", "python")
    context = args.get("context", "")
    model = args.get("model", "kimi-k2.5")

    full_prompt = f"Generate {language} code for the following task:\n\n{prompt}"
    if context:
        full_prompt += f"\n\nAdditional context:\n{context}"

    messages = [
        {"role": "system", "content": CODE_SYSTEM},
        {"role": "user", "content": full_prompt},
    ]
    return await client.complete(messages, model=model)


async def _handle_document(client: KimiClient, args: dict) -> str:
    prompt = args["prompt"]
    document_text = args.get("document_text", "")
    model = args.get("model", "moonshot-v1-128k")

    user_content = prompt
    if document_text:
        user_content += f"\n\n--- DOCUMENT CONTENT ---\n{document_text}"

    messages = [
        {"role": "system", "content": DOCUMENT_SYSTEM},
        {"role": "user", "content": user_content},
    ]
    return await client.complete(messages, model=model)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main():
    from mcp.server.stdio import stdio_server

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
