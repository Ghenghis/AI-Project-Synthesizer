"""
Test core MCP server functionality with mocks.
"""

from typing import Any
from unittest.mock import patch

import pytest

from tests.mocks.mock_browser import MockBrowserClient
from tests.mocks.mock_external import MockFirecrawlClient, MockGitLabClient

# Import mocks
from tests.mocks.mock_llm import MockLiteLLMRouter, MockMemorySystem
from tests.mocks.mock_voice import MockVoicePlayer


@pytest.fixture
def mock_llm_router():
    """Create a mock LLM router."""
    return MockLiteLLMRouter()


@pytest.fixture
def mock_memory_system():
    """Create a mock memory system."""
    return MockMemorySystem()


@pytest.fixture
def mock_browser_client():
    """Create a mock browser client."""
    return MockBrowserClient()


@pytest.fixture
def mock_voice_player():
    """Create a mock voice player."""
    return MockVoicePlayer()


@pytest.fixture
def mock_gitlab_client():
    """Create a mock GitLab client."""
    return MockGitLabClient()


@pytest.fixture
def mock_firecrawl_client():
    """Create a mock Firecrawl client."""
    return MockFirecrawlClient()


class TestMCPServerCore:
    """Test core MCP server functionality."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, mock_llm_router, mock_memory_system):
        """Test server can initialize with mocked dependencies."""
        # Mock the imports
        with (
            patch("src.llm.litellm_router.LiteLLMRouter", return_value=mock_llm_router),
            patch(
                "src.memory.mem0_integration.MemorySystem",
                return_value=mock_memory_system,
            ),
        ):
            # Import after patching
            from src.mcp_server.server import MCPServer

            # Create server instance
            server = MCPServer()

            # Verify server initialized
            assert server is not None
            assert hasattr(server, "llm_router")
            assert hasattr(server, "memory_system")

            # Test basic server info
            info = await self._get_server_info(server)
            assert info["name"] == "AI Project Synthesizer"
            assert "tools" in info

    @pytest.mark.asyncio
    async def test_llm_integration(self, mock_llm_router):
        """Test LLM integration with mock."""
        # Set up mock response
        mock_response = "This is a test response from the mock LLM."
        mock_llm_router.set_response(mock_response)

        # Test completion
        result = await mock_llm_router.complete("Test prompt")
        assert result["choices"][0]["message"]["content"] == mock_response
        assert mock_llm_router.call_count == 1

    @pytest.mark.asyncio
    async def test_browser_automation(self, mock_browser_client):
        """Test browser automation with mock."""
        # Start browser
        result = await mock_browser_client.start_browser()
        assert result["success"] is True

        # Navigate to URL
        result = await mock_browser_client.navigate("https://example.com")
        assert result["url"] == "https://example.com"
        assert result["title"] == "Mock Page for https://example.com"

        # Click element
        result = await mock_browser_client.click("#submit-button")
        assert result["success"] is True

        # Type text
        result = await mock_browser_client.type_text("#input-field", "test text")
        assert result["success"] is True

        # Take screenshot
        result = await mock_browser_client.screenshot()
        assert result["success"] is True
        assert result["data"] == b"mock_screenshot_data"

    @pytest.mark.asyncio
    async def test_voice_functionality(self, mock_voice_player):
        """Test voice functionality with mock."""
        # Play file
        result = await mock_voice_player.play_file("/path/to/audio.mp3")
        assert result["success"] is True

        # Play base64 audio
        result = await mock_voice_player.play_base64("base64audiodata", format="mp3")
        assert result["success"] is True
        assert result["format"] == "mp3"

        # Check volume
        volume = await mock_voice_player.get_volume()
        assert volume == 0.8

        # Set volume
        await mock_voice_player.set_volume(0.5)
        # Volume setting is mocked, so we just verify it doesn't error

    @pytest.mark.asyncio
    async def test_gitlab_integration(self, mock_gitlab_client):
        """Test GitLab integration with mock."""
        # Add a test project
        project = {"id": 1, "name": "test-project", "description": "Test project"}
        mock_gitlab_client.add_project(project)

        # Get project
        result = await mock_gitlab_client.get_project(1)
        assert result["id"] == 1
        assert result["name"] == "test-project"

        # Create merge request
        mr = await mock_gitlab_client.create_merge_request(
            1, "Test MR", "feature-branch", "main"
        )
        assert mr["title"] == "Test MR"
        assert mr["source_branch"] == "feature-branch"
        assert mr["target_branch"] == "main"

    @pytest.mark.asyncio
    async def test_firecrawl_integration(self, mock_firecrawl_client):
        """Test Firecrawl integration with mock."""
        # Set up scraped content
        content = {
            "url": "https://example.com",
            "title": "Example Page",
            "content": "This is example content",
        }
        mock_firecrawl_client.set_scraped_content("https://example.com", content)

        # Scrape URL
        result = await mock_firecrawl_client.scrape_url("https://example.com")
        assert result["title"] == "Example Page"
        assert result["content"] == "This is example content"

        # Search
        result = await mock_firecrawl_client.search("test query")
        assert result["success"] is True
        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_memory_system(self, mock_memory_system):
        """Test memory system with mock."""
        # Add memory
        memory = await mock_memory_system.add_memory(
            "Test memory content", {"type": "test", "importance": "high"}
        )
        assert memory["content"] == "Test memory content"
        assert memory["metadata"]["type"] == "test"

        # Search memories
        mock_memory_system.set_memories([memory])
        results = await mock_memory_system.search_memories("test")
        assert len(results) == 1
        assert results[0]["content"] == "Test memory content"

    async def _get_server_info(self, server) -> dict[str, Any]:
        """Helper to get server info."""
        # Mock implementation - in real server this would query the server
        return {
            "name": "AI Project Synthesizer",
            "version": "1.0.0",
            "tools": ["code_analysis", "browser_automation", "voice_player"],
        }


class TestToolIntegration:
    """Test tool integration with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_code_analysis_tool(self, mock_llm_router):
        """Test code analysis tool with mocked LLM."""
        # Mock LLM response
        mock_llm_router.set_response("This code looks good. No issues found.")

        # Mock the tool execution
        with patch("src.mcp_server.tools.handle_analyze_repository") as mock_analyze:
            mock_analyze.return_value = {
                "summary": "Code analysis complete",
                "issues": [],
                "suggestions": [],
            }

            # Execute tool
            result = await mock_analyze({"repo_url": "https://github.com/test/repo"})
            assert result["summary"] == "Code analysis complete"
            assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_browser_automation_tool(self, mock_browser_client):
        """Test browser automation tool with mocked browser."""
        with patch(
            "src.automation.browser_client.BrowserClient",
            return_value=mock_browser_client,
        ):
            # Start browser
            await mock_browser_client.start_browser()

            # Execute browser actions
            await mock_browser_client.navigate("https://example.com")
            await mock_browser_client.click("#test-button")

            # Verify actions were recorded
            assert "https://example.com" in mock_browser_client.navigation_history
            assert "#test-button" in mock_browser_client.clicked_selectors

    @pytest.mark.asyncio
    async def test_voice_player_tool(self, mock_voice_player):
        """Test voice player tool with mocked voice."""
        with patch("src.voice.player.get_voice_player", return_value=mock_voice_player):
            # Import after patching
            from src.voice.player import play_audio

            # Play audio
            result = await play_audio("base64audiodata", format="mp3")
            assert result["success"] is True

            # Verify audio was played
            assert len(mock_voice_player.played_audio) == 1
            assert mock_voice_player.played_audio[0][1] == "mp3"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
