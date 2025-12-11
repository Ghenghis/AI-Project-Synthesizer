"""
AI Project Synthesizer - MCP Server

Main entry point for the Model Context Protocol server.
Exposes synthesis tools to any MCP-compatible client.

Supported Clients:
- Windsurf IDE
- Claude Desktop
- VS Code (Continue, Cline extensions)
- Cursor IDE
- LM Studio
- JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)
- Neovim / Vim
- Emacs
- Zed Editor
- Sourcegraph Cody
- Open Interpreter
- Any custom MCP client

Usage:
    python -m src.mcp_server.server

Configuration Examples:

Windsurf (~/.windsurf/mcp_config.json):
    {
        "mcpServers": {
            "ai-project-synthesizer": {
                "command": "python",
                "args": ["-m", "src.mcp_server.server"]
            }
        }
    }

Claude Desktop:
    {
        "mcpServers": {
            "ai-project-synthesizer": {
                "command": "python",
                "args": ["-m", "src.mcp_server.server"],
                "cwd": "/path/to/AI_Synthesizer"
            }
        }
    }

VS Code Continue:
    {
        "mcpServers": [{
            "name": "ai-project-synthesizer",
            "command": "python",
            "args": ["-m", "src.mcp_server.server"]
        }]
    }

See docs/MCP_CLIENT_SUPPORT.md for full configuration guide.
"""

import asyncio
import json
import time
from typing import Any

# Import from external mcp package
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.core.config import get_settings
from src.core.security import SecretManager, get_secure_logger
from src.core.observability import correlation_manager, track_performance, metrics
from src.core.lifecycle import lifecycle
from src.mcp_server.tools import (
    handle_search_repositories,
    handle_analyze_repository,
    handle_check_compatibility,
    handle_resolve_dependencies,
    handle_synthesize_project,
    handle_generate_documentation,
    handle_get_synthesis_status,
    handle_assistant_chat,
    handle_assistant_voice,
    handle_assistant_toggle_voice,
    handle_get_voices,
    handle_speak_fast,
    handle_assemble_project,
)

# Configure secure logging
secure_logger = get_secure_logger(__name__)
logger = secure_logger.logger

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
        ),
        # ==================== ASSISTANT TOOLS ====================
        Tool(
            name="assistant_chat",
            description="Chat with the AI assistant. It understands natural language, asks clarifying questions, and helps complete tasks like searching, analyzing, and building projects.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Your message to the assistant"
                    },
                    "voice_enabled": {
                        "type": "boolean",
                        "default": False,
                        "description": "Generate voice audio for the response"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="assistant_speak",
            description="Convert text to speech using ElevenLabs voices",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech"
                    },
                    "voice": {
                        "type": "string",
                        "default": "rachel",
                        "description": "Voice name: rachel, josh, adam, bella, domi, antoni, sam"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="assistant_toggle_voice",
            description="Toggle voice output on/off for the assistant",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable or disable voice"
                    }
                },
                "required": ["enabled"]
            }
        ),
        Tool(
            name="get_voices",
            description="Get list of available voices for text-to-speech",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="speak_fast",
            description="FAST streaming voice - plays audio as it generates with no gaps. Best for smooth, natural speech. Uses turbo model for lowest latency.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to speak"
                    },
                    "voice": {
                        "type": "string",
                        "default": "rachel",
                        "description": "Voice: rachel, josh, adam, bella, domi, antoni, sam"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="assemble_project",
            description="THE ULTIMATE TOOL: Automatically assemble a complete project from an idea. Searches GitHub/HuggingFace/Kaggle, downloads code/models/datasets, creates folder structure on G:/, generates README, creates GitHub repo, prepares for Windsurf IDE.",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {
                        "type": "string",
                        "description": "Project idea/description (e.g., 'RAG chatbot with local LLM')"
                    },
                    "name": {
                        "type": "string",
                        "description": "Project name (optional, auto-generated if not provided)"
                    },
                    "output_dir": {
                        "type": "string",
                        "default": "G:/",
                        "description": "Output directory for the project"
                    },
                    "create_github": {
                        "type": "boolean",
                        "default": True,
                        "description": "Create a GitHub repository for the project"
                    }
                },
                "required": ["idea"]
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
    # Generate correlation ID for request tracing
    correlation_id = correlation_manager.generate_id()
    correlation_manager.set_correlation_id(correlation_id)

    # Mask secrets in arguments before logging
    sanitized_args = SecretManager.mask_secrets(str(arguments))

    secure_logger.info(
        f"Tool called: {name}",
        correlation_id=correlation_id,
        tool=name,
        args_count=len(arguments)
    )

    metrics.increment("tool_calls_total", tags={"tool": name})

    try:
        # Route to appropriate handler with performance tracking
        with track_performance(f"tool_{name}"):
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
            # Assistant tools
            elif name == "assistant_chat":
                result = await handle_assistant_chat(arguments)
            elif name == "assistant_speak":
                result = await handle_assistant_voice(arguments)
            elif name == "assistant_toggle_voice":
                result = await handle_assistant_toggle_voice(arguments)
            elif name == "get_voices":
                result = await handle_get_voices(arguments)
            elif name == "speak_fast":
                result = await handle_speak_fast(arguments)
            elif name == "assemble_project":
                result = await handle_assemble_project(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
                metrics.increment("tool_errors_total", tags={"tool": name, "error_type": "unknown_tool"})

        # Convert result to JSON string
        result_text = json.dumps(result, indent=2, default=str)

        secure_logger.info(
            f"Tool {name} completed successfully",
            correlation_id=correlation_id,
            tool=name,
            result_size=len(result_text)
        )

        metrics.increment("tool_success_total", tags={"tool": name})

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        # Mask secrets in error messages
        sanitized_error = SecretManager.mask_secrets(str(e))

        secure_logger.error(
            f"Error in tool {name}: {sanitized_error}",
            correlation_id=correlation_id,
            tool=name,
            error_type=type(e).__name__
        )

        metrics.increment("tool_errors_total", tags={"tool": name, "error_type": type(e).__name__})

        error_response = {
            "error": True,
            "message": sanitized_error,
            "tool": name,
            "correlation_id": correlation_id
        }

        return [TextContent(type="text", text=json.dumps(error_response))]

    finally:
        # Clear correlation ID
        correlation_manager.clear_correlation_id()


async def main():
    """
    Main entry point for the MCP server.
    
    Starts the server using stdio transport for Windsurf integration.
    """
    secure_logger.info("=" * 60)
    secure_logger.info("Starting AI Project Synthesizer MCP Server")
    secure_logger.info("=" * 60)
    secure_logger.info(f"Environment: {settings.app.app_env}")
    secure_logger.info(f"Debug mode: {settings.app.debug}")
    secure_logger.info(f"Enabled platforms: {settings.platforms.get_enabled_platforms()}")
    secure_logger.info(f"LLM Host: {settings.llm.ollama_host}")
    secure_logger.info("=" * 60)

    # Register shutdown handler
    async def shutdown_mcp_server():
        """Shutdown MCP server gracefully."""
        secure_logger.info("Shutting down MCP server")

    lifecycle.add_shutdown_task("mcp_server", shutdown_mcp_server, priority=100)

    # Initialize metrics
    metrics.set_gauge("server_startup_time", time.time())
    metrics.increment("server_startups_total")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        secure_logger.error(f"Server error: {SecretManager.mask_secrets(str(e))}")
        metrics.increment("server_errors_total")
        raise
    finally:
        metrics.set_gauge("server_shutdown_time", time.time())


if __name__ == "__main__":
    asyncio.run(main())
