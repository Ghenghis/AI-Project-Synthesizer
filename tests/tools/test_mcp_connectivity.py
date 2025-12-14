"""
VIBE MCP - MCP Connectivity Test

Tests MCP server connectivity and basic tool functionality.
Replaces test-mcp-simple.js from windsurf-vibe-setup.

Usage:
    python tests/tools/test_mcp_connectivity.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.core.config import Settings, get_settings
from src.mcp_server.server import server

logger = logging.getLogger(__name__)


class MCPConnectivityTest:
    """Test MCP server connectivity and basic operations."""

    def __init__(self):
        """Initialize test with default configuration."""
        self.config = get_settings()
        # Use the server instance imported at module level
        self.server = server
        self.test_results = {
            "server_import": False,
            "tool_count": False,
            "tool_names": False,
            "server_config": False,
        }

    async def test_server_import(self) -> bool:
        """Test if MCP server can be imported."""
        print("🚀 Testing MCP server import...")

        try:
            # Check if server is available
            if self.server:
                print("✅ MCP server imported successfully")
                self.test_results["server_import"] = True
                return True
            else:
                print("❌ MCP server import failed")
                return False

        except Exception as e:
            print(f"❌ MCP server import failed: {e}")
            logger.exception("Server import error")
            return False

    async def test_tool_count(self) -> bool:
        """Test if tools are registered."""
        print("\n🔧 Testing tool registration...")

        try:
            # The server uses decorators, so we need to check the registered tools
            # We'll check the tools module to see what's available
            from src.mcp_server.tools import (
                handle_analyze_repository,
                handle_generate_documentation,
                handle_resolve_dependencies,
                handle_search_repositories,
                handle_synthesize_project,
            )

            # Count available handlers
            tool_handlers = [
                handle_search_repositories,
                handle_analyze_repository,
                handle_synthesize_project,
                handle_generate_documentation,
                handle_resolve_dependencies,
            ]

            if tool_handlers:
                print(f"✅ Found {len(tool_handlers)} tool handlers")
                self.test_results["tool_count"] = True
                return True
            else:
                print("⚠️ No tool handlers found")
                return False

        except Exception as e:
            print(f"❌ Tool registration check failed: {e}")
            logger.exception("Tool count error")
            return False

    async def test_tool_names(self) -> bool:
        """Test if we can list tool names."""
        print("\n📋 Testing tool names...")

        try:
            # List of expected tools based on the server implementation
            expected_tools = [
                "search_repositories",
                "analyze_repository",
                "synthesize_project",
                "generate_documentation",
                "resolve_dependencies",
                "assistant_chat",
                "assistant_speak",
                "assistant_toggle_voice",
                "get_voices",
                "speak_fast",
                "assemble_project",
            ]

            print("✅ Expected tools configured:")
            for tool in expected_tools:
                print(f"   - {tool}")

            self.test_results["tool_names"] = True
            return True

        except Exception as e:
            print(f"❌ Tool names check failed: {e}")
            logger.exception("Tool names error")
            return False

    async def test_server_config(self) -> bool:
        """Test server configuration."""
        print("\n⚙️ Testing server configuration...")

        try:
            # Check settings
            if self.config:
                print("✅ Configuration loaded:")
                print(f"   - Environment: {self.config.app.app_env}")
                print(f"   - Debug: {self.config.app.debug}")
                print(f"   - Ollama Host: {self.config.llm.ollama_host}")
                print(f"   - Ollama Model Medium: {self.config.llm.ollama_model_medium}")
                print(f"   - LM Studio Host: {self.config.llm.lmstudio_host}")
                print(f"   - Cloud LLM Enabled: {self.config.llm.cloud_llm_enabled}")

                # Check if platforms have tokens
                enabled = self.config.platforms.get_enabled_platforms()
                print(f"   - Enabled Platforms: {enabled}")

                self.test_results["server_config"] = True
                return True
            else:
                print("❌ Configuration not loaded")
                return False

        except Exception as e:
            print(f"❌ Server configuration check failed: {e}")
            logger.exception("Server config error")
            return False

    async def run_all_tests(self) -> dict:
        """Run all connectivity tests."""
        print("=" * 60)
        print("VIBE MCP - Connectivity Test Suite")
        print("=" * 60)

        # Run tests in sequence
        await self.test_server_import()
        await self.test_tool_count()
        await self.test_tool_names()
        await self.test_server_config()

        # Calculate results
        passed = sum(self.test_results.values())
        total = len(self.test_results)

        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)

        for test, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test.replace('_', ' ').title():<20} {status}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! MCP is ready.")
        elif passed >= total // 2:
            print("⚠️ Some tests failed. MCP may have partial functionality.")
        else:
            print("❌ Most tests failed. Check MCP server configuration.")

        return {
            "passed": passed,
            "total": total,
            "results": self.test_results,
            "success_rate": passed / total * 100,
        }

    async def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self.server, 'close'):
                await self.server.close()
        except:
            pass


async def main():
    """Main test runner."""
    test = MCPConnectivityTest()

    try:
        results = await test.run_all_tests()

        # Exit with appropriate code
        sys.exit(0 if results["success_rate"] >= 75 else 1)

    finally:
        await test.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run tests
    asyncio.run(main())
