"""
AI Project Synthesizer - MCP Server

Main entry point for the Model Context Protocol server.
Exposes synthesis tools to Windsurf IDE via the MCP protocol.

Usage:
    python -m src.mcp.server
    
Or via Windsurf mcp_config.json:
    {
        "mcpServers": {
            "ai-project-synthesizer": {
                "command": "python",
                "args": ["-m", "src.mcp.server"]
            }
        }
    }
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.core.config import get_settings
from src.mcp.tools import (
    handle_search_repositories,
    handle_analyze_repository,
    handle_check_compatibility,
    handle_resolve_dependencies,
    handle_synthesize_project,
    handle_generate_documentation,
    handle_get_synthesis_status,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("ai-project-synthesizer")

# Get settings
settings = get_settings()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available MCP tools.
    
    Returns tools for:
    - Repository discovery and search
    - Code analysis
    - Dependency resolution
    - Project synthesis
    - Documentation generation
    """
    return [
        Tool(
            name="search_repositories",
            description="Search for repositories across GitHub, HuggingFace, Kaggle, and other platforms. Returns ranked results with metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query describing what you're looking for"
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["github", "huggingface"],
                        "description": "Platforms to search (github, huggingface, kaggle, arxiv)"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Maximum number of results to return"
                    },
                    "language_filter": {
                        "type": "string",
                        "description": "Filter by programming language"
                    },
                    "min_stars": {
                        "type": "integer",
                        "default": 10,
                        "description": "Minimum star count for repositories"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_repository",
            description="Perform deep analysis of a repository including code structure, dependencies, quality metrics, and extractable components",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "Repository URL to analyze (GitHub, HuggingFace, etc.)"
                    },
                    "include_transitive_deps": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include transitive dependency analysis"
                    },
                    "extract_components": {
                        "type": "boolean",
                        "default": True,
                        "description": "Identify extractable code components"
                    }
                },
                "required": ["repo_url"]
            }
        ),
        Tool(
            name="check_compatibility",
            description="Check if multiple repositories can work together by analyzing dependencies, Python versions, and potential conflicts",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of repository URLs to check for compatibility"
                    },
                    "target_python_version": {
                        "type": "string",
                        "default": "3.11",
                        "description": "Target Python version for compatibility check"
                    }
                },
                "required": ["repo_urls"]
            }
        ),
        Tool(
            name="resolve_dependencies",
            description="Resolve and merge dependencies from multiple repositories into a unified, conflict-free set using SAT solver",
            inputSchema={
                "type": "object",
                "properties": {
                    "repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Repository URLs to merge dependencies from"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional version constraints (e.g., 'numpy>=1.20')"
                    },
                    "python_version": {
                        "type": "string",
                        "default": "3.11",
                        "description": "Target Python version"
                    }
                },
                "required": ["repositories"]
            }
        ),
        Tool(
            name="synthesize_project",
            description="Create a unified project by intelligently combining code, dependencies, and structure from multiple repositories",
            inputSchema={
                "type": "object",
                "properties": {
                    "repositories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "repo_url": {"type": "string", "description": "Repository URL"},
                                "components": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Component names to extract"
                                },
                                "destination": {"type": "string", "description": "Target directory"}
                            },
                            "required": ["repo_url"]
                        },
                        "description": "Repositories and components to extract"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Name for the synthesized project"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output directory path"
                    },
                    "template": {
                        "type": "string",
                        "default": "python-default",
                        "description": "Project template (python-default, python-ml, python-web, minimal)"
                    }
                },
                "required": ["repositories", "project_name", "output_path"]
            }
        ),
        Tool(
            name="generate_documentation",
            description="Generate comprehensive documentation including README, architecture docs, API reference, and diagrams",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project to document"
                    },
                    "doc_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["readme", "architecture", "api"],
                        "description": "Types of documentation to generate"
                    },
                    "llm_enhanced": {
                        "type": "boolean",
                        "default": True,
                        "description": "Use LLM for enhanced documentation quality"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="get_synthesis_status",
            description="Get the status and progress of an ongoing synthesis operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "string",
                        "description": "Synthesis operation ID returned from synthesize_project"
                    }
                },
                "required": ["synthesis_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls from Windsurf.
    
    Dispatches to the appropriate handler based on tool name.
    All handlers are implemented in src/mcp/tools.py
    """
    logger.info(f"Tool called: {name} with args: {arguments}")
    
    try:
        # Route to appropriate handler
        if name == "search_repositories":
            result = await handle_search_repositories(arguments)
        elif name == "analyze_repository":
            result = await handle_analyze_repository(arguments)
        elif name == "check_compatibility":
            result = await handle_check_compatibility(arguments)
        elif name == "resolve_dependencies":
            result = await handle_resolve_dependencies(arguments)
        elif name == "synthesize_project":
            result = await handle_synthesize_project(arguments)
        elif name == "generate_documentation":
            result = await handle_generate_documentation(arguments)
        elif name == "get_synthesis_status":
            result = await handle_get_synthesis_status(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Convert result to JSON string
        import json
        result_text = json.dumps(result, indent=2, default=str)
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.exception(f"Error in tool {name}")
        error_response = {
            "error": True,
            "message": str(e),
            "tool": name
        }
        import json
        return [TextContent(type="text", text=json.dumps(error_response))]


async def main():
    """
    Main entry point for the MCP server.
    
    Starts the server using stdio transport for Windsurf integration.
    """
    logger.info("=" * 60)
    logger.info("Starting AI Project Synthesizer MCP Server")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.app.app_env}")
    logger.info(f"Debug mode: {settings.app.debug}")
    logger.info(f"Enabled platforms: {settings.platforms.get_enabled_platforms()}")
    logger.info(f"LLM Host: {settings.llm.ollama_host}")
    logger.info("=" * 60)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
