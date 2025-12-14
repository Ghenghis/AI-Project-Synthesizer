"""
Integration test for MCP API contracts.
Tests: API contracts, provider fallback, and error handling.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests import Response
from requests.structures import CaseInsensitiveDict

from src.discovery.github_client import GitHubClient
from src.discovery.gitlab_client import GitLabClient
from src.llm.litellm_router import LiteLLMRouter
from src.mcp_server import server as mcp_server


class TestMCPApiContract:
    """Test MCP server API contracts and compliance."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_server_api_spec_compliance(self):
        """Test MCP server follows MCP protocol specification."""

        # Get server instance
        server_instance = mcp_server.server
        assert server_instance is not None

        # Test that server has basic MCP structure
        # The actual MCP protocol testing would require the full FastMCP framework
        # For now, we verify the server module loads correctly
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_contract(self):
        """Test tool execution follows proper contract."""

        # Test that tools can be called directly and return proper structure
        from src.mcp_server import tools

        with patch('src.mcp_server.tools.create_unified_search') as mock_create:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_create.return_value = mock_instance

            # Call search tool
            result = await tools.search_repositories(
                query="test",
                platforms=["github"],
                max_results=5
            )

            # Verify result structure
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.integration
    def test_github_api_contract_compliance(self):
        """Test GitHub client follows GitHub API contract."""

        client = GitHubClient(token="test_token")

        # Mock GitHub API responses
        with patch('requests.get') as mock_get:
            # Repository response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": 123456789,
                "name": "test-repo",
                "full_name": "owner/test-repo",
                "description": "Test repository",
                "stargazers_count": 42,
                "language": "Python",
                "forks": 5,
                "open_issues": 3,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T00:00:00Z",
                "default_branch": "main",
                "owner": {
                    "login": "owner",
                    "type": "User"
                }
            }
            mock_get.return_value = mock_response

            # Test repository retrieval
            repo = client.get_repository("owner/test-repo")

            # Verify contract compliance
            assert repo.name == "test-repo"
            assert repo.full_name == "owner/test-repo"
            assert repo.stargazers == 42
            assert repo.language == "Python"

            # Verify correct API endpoint was called
            mock_get.assert_called_with(
                "https://api.github.com/repos/owner/test-repo",
                headers={"Authorization": "token test_token"}
            )

    @pytest.mark.integration
    def test_gitlab_api_contract_compliance(self):
        """Test GitLab client follows GitLab API contract."""

        client = GitLabClient(token="test_token")

        with patch('requests.get') as mock_get:
            # Project response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": 98765,
                "name": "test-project",
                "path_with_namespace": "group/test-project",
                "description": "Test project",
                "star_count": 10,
                "forks_count": 2,
                "open_issues_count": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "last_activity_at": "2024-01-15T00:00:00Z",
                "default_branch": "main",
                "visibility": "public",
                "owner": {
                    "name": "owner",
                    "username": "owner"
                }
            }
            mock_get.return_value = mock_response

            # Test project retrieval
            project = client.get_project(98765)

            # Verify contract compliance
            assert project.name == "test-project"
            assert project.path == "group/test-project"
            assert project.stars == 10

            # Verify correct API endpoint
            mock_get.assert_called_with(
                "https://gitlab.com/api/v4/projects/98765",
                headers={"Private-Token": "test_token"}
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_provider_fallback_contract(self):
        """Test LLM router follows provider fallback contract."""

        router = LiteLLMRouter()

        # Mock provider responses
        with patch.object(router, '_call_provider') as mock_call:
            # Primary provider fails
            mock_call.side_effect = [
                Exception("Primary provider down"),
                {
                    "content": "Response from fallback provider",
                    "provider": "fallback",
                    "tokens_used": 100,
                    "cost": 0.001
                }
            ]

            result = await router.complete(
                prompt="Test prompt",
                providers=["primary", "fallback"]
            )

            # Verify fallback was used
            assert result["provider"] == "fallback"
            assert result["content"] == "Response from fallback provider"

            # Verify both providers were tried
            assert mock_call.call_count == 2

    @pytest.mark.integration
    def test_api_error_response_contract(self):
        """Test all APIs return proper error responses."""

        # Test GitHub API errors
        client = GitHubClient(token="invalid")

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {
                "message": "Not Found",
                "documentation_url": "https://docs.github.com/rest"
            }
            mock_get.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                client.get_repository("nonexistent/repo")

            assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)

        # Test MCP server errors
        async def test_mcp_errors():
            server = MCPServer()
            await server.initialize()

            # Invalid JSON-RPC request
            invalid_request = {
                "jsonrpc": "1.0",  # Invalid version
                "id": 1,
                "method": "tools/list"
            }

            response = await server.handle_request(invalid_request)

            assert "error" in response
            assert response["error"]["code"] == -32600  # Invalid Request

            await server.shutdown()

        import asyncio
        asyncio.run(test_mcp_errors())

    @pytest.mark.integration
    def test_api_rate_limiting_contract(self):
        """Test APIs handle rate limiting per contract."""

        client = GitHubClient(token="test_token")

        with patch('requests.get') as mock_get:
            # Rate limit response
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.headers = {
                "X-RateLimit-Limit": "60",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(__import__('time').time()) + 3600)
            }
            mock_response.json.return_value = {
                "message": "API rate limit exceeded",
                "documentation_url": "https://docs.github.com/rest"
            }
            mock_get.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                client.get_repository("owner/repo")

            assert "rate limit" in str(exc_info.value).lower()

            # Verify rate limit info is extracted
            rate_info = client.get_rate_limit_info()
            assert rate_info is not None
            assert rate_info["remaining"] == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_versioning_contract(self):
        """Test APIs support versioning as per contract."""

        server = MCPServer()
        await server.initialize()

        # Test with different protocol versions
        versions = ["2024-11-05", "2024-10-07"]

        for version in versions:
            request = {
                "jsonrpc": "2.0",
                "id": hash(version),
                "method": "initialize",
                "params": {
                    "protocolVersion": version,
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }

            response = await server.handle_request(request)

            # Should respond with supported version
            assert "result" in response
            assert "protocolVersion" in response["result"]

        await server.shutdown()

    @pytest.mark.integration
    def test_api_authentication_contract(self):
        """Test APIs follow authentication contract."""

        # Test GitHub authentication
        with pytest.raises(ValueError):
            GitHubClient(token=None)  # Token required

        with pytest.raises(ValueError):
            GitHubClient(token="")  # Empty token invalid

        # Test with valid token
        client = GitHubClient(token="ghp_test_token")
        assert client.token == "ghp_test_token"

        # Test GitLab authentication
        gitlab_client = GitLabClient(token="glpat_test_token")
        assert gitlab_client.token == "glpat_test_token"

        # Verify authentication headers are set correctly
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "token ghp_test_token"
        assert "Private-Token" in gitlab_client.session.headers
        assert gitlab_client.session.headers["Private-Token"] == "glpat_test_token"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
