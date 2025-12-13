"""
VIBE MCP - Memory MCP Tools

MCP server tools for memory management using the enhanced Mem0 integration.
Implements Phase 4.3 of the VIBE MCP roadmap.

Features:
- Add, search, and retrieve memories
- Memory consolidation and insights
- Export functionality
- Multi-agent memory support
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from src.memory.mem0_integration import MemoryCategory, MemoryConfig, MemorySystem

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("vibe-memory")

# Global memory system instance
_memory_system: MemorySystem | None = None


class AddMemoryRequest(BaseModel):
    """Request to add a memory."""
    content: str = Field(description="The memory content to store")
    category: str = Field(
        default="context",
        description="Memory category: preference, decision, pattern, error_solution, context, learning, component, workflow"
    )
    tags: list[str] = Field(default=[], description="Tags for categorization")
    agent_id: str | None = Field(default=None, description="ID of the agent adding the memory")
    session_id: str | None = Field(default=None, description="Current session ID")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0-1)")


class SearchMemoryRequest(BaseModel):
    """Request to search memories."""
    query: str = Field(description="Search query")
    category: str | None = Field(default=None, description="Filter by category")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    agent_id: str | None = Field(default=None, description="Filter by agent ID")


class ConsolidateRequest(BaseModel):
    """Request to consolidate memories."""
    category: str | None = Field(default=None, description="Category to consolidate")
    agent_id: str | None = Field(default=None, description="Agent to consolidate for")


class ExportRequest(BaseModel):
    """Request to export memories."""
    format: str = Field(default="json", description="Export format: json, csv, markdown")
    category: str | None = Field(default=None, description="Filter by category")
    agent_id: str | None = Field(default=None, description="Filter by agent ID")


def get_memory_system() -> MemorySystem:
    """Get or create the global memory system."""
    global _memory_system
    if _memory_system is None:
        # Initialize with enhanced configuration
        config = MemoryConfig(
            enable_consolidation=True,
            consolidation_interval=24,
            consolidation_threshold=50,
            enable_analytics=True,
        )
        _memory_system = MemorySystem(config)
        logger.info("Memory system initialized for MCP")
    return _memory_system


def parse_category(category_str: str | None) -> MemoryCategory | None:
    """Parse category string to enum."""
    if not category_str:
        return None

    try:
        return MemoryCategory(category_str.lower())
    except ValueError:
        logger.warning(f"Invalid category: {category_str}")
        return MemoryCategory.CONTEXT


@mcp.tool()
async def add_memory(request: AddMemoryRequest) -> dict[str, Any]:
    """
    Add a new memory to the system.

    Args:
        request: Memory addition request with content, category, tags, etc.

    Returns:
        Dictionary with memory ID and status
    """
    try:
        memory_system = get_memory_system()
        category = parse_category(request.category)

        memory_id = await memory_system.add(
            content=request.content,
            category=category or MemoryCategory.CONTEXT,
            tags=request.tags,
            agent_id=request.agent_id,
            session_id=request.session_id,
            importance=request.importance,
        )

        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory added successfully",
            "category": (category or MemoryCategory.CONTEXT).value,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to add memory",
        }


@mcp.tool()
async def search_memory(request: SearchMemoryRequest) -> dict[str, Any]:
    """
    Search for memories matching the query.

    Args:
        request: Search request with query, filters, and limits

    Returns:
        Dictionary with search results
    """
    try:
        memory_system = get_memory_system()
        category = parse_category(request.category)

        results = await memory_system.search(
            query=request.query,
            category=category,
            limit=request.limit,
            agent_id=request.agent_id,
        )

        # Format results for MCP response
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id"),
                "content": result.get("memory", result.get("content", "")),
                "category": result.get("metadata", {}).get("category", "unknown"),
                "tags": result.get("metadata", {}).get("tags", []),
                "created_at": result.get("metadata", {}).get("created_at", result.get("created_at", "")),
                "importance": result.get("metadata", {}).get("importance", 0.5),
                "agent_id": result.get("metadata", {}).get("agent_id"),
                "relevance_score": result.get("score", 1.0),
            })

        return {
            "success": True,
            "results": formatted_results,
            "total": len(formatted_results),
            "query": request.query,
            "category": request.category,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "total": 0,
        }


@mcp.tool()
async def get_memory(memory_id: str) -> dict[str, Any]:
    """
    Retrieve a specific memory by ID.

    Args:
        memory_id: ID of the memory to retrieve

    Returns:
        Dictionary with memory details
    """
    try:
        memory_system = get_memory_system()
        result = await memory_system.get(memory_id)

        if result:
            return {
                "success": True,
                "memory": {
                    "id": result.get("id"),
                    "content": result.get("memory", result.get("content", "")),
                    "category": result.get("metadata", {}).get("category", "unknown"),
                    "tags": result.get("metadata", {}).get("tags", []),
                    "created_at": result.get("metadata", {}).get("created_at", result.get("created_at", "")),
                    "updated_at": result.get("metadata", {}).get("updated_at", ""),
                    "importance": result.get("metadata", {}).get("importance", 0.5),
                    "agent_id": result.get("metadata", {}).get("agent_id"),
                    "session_id": result.get("metadata", {}).get("session_id"),
                    "access_count": result.get("metadata", {}).get("access_count", 0),
                }
            }
        else:
            return {
                "success": False,
                "error": "Memory not found",
                "memory_id": memory_id,
            }

    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "memory_id": memory_id,
        }


@mcp.tool()
async def update_memory(memory_id: str, content: str) -> dict[str, Any]:
    """
    Update an existing memory's content.

    Args:
        memory_id: ID of the memory to update
        content: New content for the memory

    Returns:
        Dictionary with update status
    """
    try:
        memory_system = get_memory_system()
        success = await memory_system.update(memory_id, content)

        if success:
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory updated successfully",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "success": False,
                "error": "Memory not found or update failed",
                "memory_id": memory_id,
            }

    except Exception as e:
        logger.error(f"Failed to update memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "memory_id": memory_id,
        }


@mcp.tool()
async def delete_memory(memory_id: str) -> dict[str, Any]:
    """
    Delete a memory by ID.

    Args:
        memory_id: ID of the memory to delete

    Returns:
        Dictionary with deletion status
    """
    try:
        memory_system = get_memory_system()
        success = await memory_system.delete(memory_id)

        if success:
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory deleted successfully",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "success": False,
                "error": "Memory not found or deletion failed",
                "memory_id": memory_id,
            }

    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        return {
            "success": False,
            "error": str(e),
            "memory_id": memory_id,
        }


@mcp.tool()
async def get_context_for_task(task_description: str, categories: list[str] | None = None) -> dict[str, Any]:
    """
    Get relevant memories for a specific task.

    Args:
        task_description: Description of the task
        categories: List of categories to include (default: all)

    Returns:
        Dictionary with categorized relevant memories
    """
    try:
        memory_system = get_memory_system()

        # Parse categories
        include_categories = None
        if categories:
            include_categories = []
            for cat_str in categories:
                cat = parse_category(cat_str)
                if cat:
                    include_categories.append(cat)

        context = await memory_system.get_context_for_task(
            task_description=task_description,
            include_categories=include_categories,
            limit=5,
        )

        # Format memories for response
        formatted_memories = {}
        for cat, memories in context["memories"].items():
            formatted_memories[cat] = [
                {
                    "id": m.get("id"),
                    "content": m.get("memory", m.get("content", ""))[:200] + "...",
                    "tags": m.get("metadata", {}).get("tags", []),
                    "created_at": m.get("metadata", {}).get("created_at", ""),
                }
                for m in memories
            ]

        return {
            "success": True,
            "task": task_description,
            "summary": context["summary"],
            "memories": formatted_memories,
            "total_relevant": sum(len(m) for m in formatted_memories.values()),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get context: {e}")
        return {
            "success": False,
            "error": str(e),
            "task": task_description,
            "memories": {},
        }


@mcp.tool()
async def consolidate_memories(request: ConsolidateRequest) -> dict[str, Any]:
    """
    Consolidate old memories to save space.

    Args:
        request: Consolidation request with filters

    Returns:
        Dictionary with consolidation report
    """
    try:
        memory_system = get_memory_system()
        category = parse_category(request.category)

        report = await memory_system.consolidate_memories(
            category=category,
            agent_id=request.agent_id,
        )

        return {
            "success": report.get("success", False),
            "consolidated": report.get("consolidated", {}),
            "total_consolidated": report.get("total_consolidated", 0),
            "timestamp": report.get("timestamp", datetime.now().isoformat()),
            "error": report.get("error"),
        }

    except Exception as e:
        logger.error(f"Failed to consolidate memories: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_consolidated": 0,
        }


@mcp.tool()
async def get_memory_insights(agent_id: str | None = None, category: str | None = None) -> dict[str, Any]:
    """
    Get insights and analytics about stored memories.

    Args:
        agent_id: Filter by agent ID
        category: Filter by category

    Returns:
        Dictionary with memory insights
    """
    try:
        memory_system = get_memory_system()
        cat = parse_category(category)

        insights = await memory_system.get_memory_insights(
            agent_id=agent_id,
            category=cat,
        )

        return {
            "success": True,
            "insights": insights,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        return {
            "success": False,
            "error": str(e),
            "insights": {},
        }


@mcp.tool()
async def export_memories(request: ExportRequest) -> dict[str, Any]:
    """
    Export memories to a file.

    Args:
        request: Export request with format and filters

    Returns:
        Dictionary with export file path
    """
    try:
        memory_system = get_memory_system()
        category = parse_category(request.category)

        if request.format not in ["json", "csv", "markdown"]:
            return {
                "success": False,
                "error": "Invalid format. Must be: json, csv, or markdown",
            }

        file_path = await memory_system.export_memories(
            format=request.format,
            category=category,
            agent_id=request.agent_id,
        )

        return {
            "success": True,
            "file_path": file_path,
            "format": request.format,
            "message": f"Memories exported to {file_path}",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to export memories: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": "",
        }


@mcp.tool()
async def get_memory_statistics() -> dict[str, Any]:
    """
    Get comprehensive statistics about the memory system.

    Returns:
        Dictionary with memory statistics
    """
    try:
        memory_system = get_memory_system()
        stats = await memory_system.get_stats()

        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return {
            "success": False,
            "error": str(e),
            "statistics": {},
        }


# Convenience methods for common memory types
@mcp.tool()
async def remember_preference(preference: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Remember a user preference."""
    request = AddMemoryRequest(
        content=preference,
        category="preference",
        tags=tags or ["preference"],
        importance=0.7,
    )
    return await add_memory(request)


@mcp.tool()
async def remember_error_solution(error: str, solution: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Remember an error and its solution."""
    content = f"Error: {error}\nSolution: {solution}"
    request = AddMemoryRequest(
        content=content,
        category="error_solution",
        tags=tags or ["error", "solution"],
        importance=0.8,
    )
    return await add_memory(request)


@mcp.tool()
async def remember_code_pattern(pattern: str, language: str | None = None, tags: list[str] | None = None) -> dict[str, Any]:
    """Remember a reusable code pattern."""
    request = AddMemoryRequest(
        content=pattern,
        category="pattern",
        tags=tags or ["pattern", language or "general"],
        importance=0.6,
    )
    return await add_memory(request)


# Resource definitions for memory system info
@mcp.resource("memory://categories")
def get_memory_categories() -> str:
    """Get available memory categories."""
    categories = {
        cat.value: {
            "description": cat.name.replace("_", " ").title(),
            "memory_type": cat.memory_type,
        }
        for cat in MemoryCategory
    }
    return json.dumps(categories, indent=2)


@mcp.resource("memory://stats")
async def get_memory_stats_resource() -> str:
    """Get current memory statistics as JSON."""
    try:
        memory_system = get_memory_system()
        stats = await memory_system.get_stats()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Main server function
def run_server(host: str = "localhost", port: int = 8001):
    """Run the Memory MCP server."""
    logger.info(f"Starting Memory MCP server on {host}:{port}")
    mcp.run(host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VIBE Memory MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    run_server(host=args.host, port=args.port)
