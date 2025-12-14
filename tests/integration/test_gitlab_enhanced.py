"""
Integration tests for Enhanced GitLab component.

Tests enhanced GitLab functionality including:
- MR automation with templates
- AI-powered code review
- CI/CD pipeline control
- Issue automation
- Webhook management
"""

import asyncio
import json
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from src.discovery.gitlab_enhanced import (
    GitLabEnhanced,
    MRAction,
    MRReviewResult,
    MRTemplate,
    PipelineConfig,
    PipelineTrigger,
    create_gitlab_enhanced,
)


class TestGitLabEnhanced:
    """Test suite for GitLabEnhanced."""

    @pytest.fixture
    async def client(self):
        """Create GitLab enhanced client for testing."""
        # Mock the client to avoid needing real GitLab credentials
        with patch("src.discovery.gitlab_enhanced.GitLabClient.__init__") as mock_init:
            mock_init.return_value = None
            client = GitLabEnhanced()

            # Mock essential methods
            client._request = AsyncMock()
            client.test_connection = AsyncMock(return_value=True)

            yield client

    @pytest.mark.asyncio
    async def test_mr_templates(self, client):
        """Test MR template functionality."""
        # Verify templates are loaded
        assert "feature" in client.mr_templates
        assert "bugfix" in client.mr_templates
        assert "hotfix" in client.mr_templates

        # Check template structure
        feature_template = client.mr_templates["feature"]
        assert isinstance(feature_template, MRTemplate)
        assert feature_template.name == "Feature"
        assert "feat: {feature_name}" in feature_template.title_template

    @pytest.mark.asyncio
    async def test_create_automated_mr(self, client):
        """Test automated MR creation."""
        # Mock API response
        mock_response = {
            "id": 123,
            "iid": 45,
            "title": "feat: Test Feature",
            "description": "Test description",
            "source_branch": "feature/test",
            "target_branch": "main",
            "web_url": "https://gitlab.com/test/project/-/merge_requests/45",
        }
        client._request.return_value = mock_response

        # Create MR
        mr = await client.create_automated_mr(
            project_id="test/project",
            source_branch="feature/test",
            target_branch="main",
            template_type="feature",
            context={
                "feature_name": "Test Feature",
                "description": "Test description",
                "changes": "- Add test feature",
                "testing": "- Unit tests added",
            },
        )

        assert mr.iid == 45
        assert mr.title == "feat: Test Feature"
        assert mr.source_branch == "feature/test"
        assert mr.target_branch == "main"

        # Verify API was called correctly
        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[0][0] == "POST"
        assert "merge_requests" in call_args[0][1]

        # Check request data
        data = call_args[1]["data"]
        assert data["title"] == "feat: Test Feature"
        assert "Test description" in data["description"]
        assert "feature" in data["labels"]

    @pytest.mark.asyncio
    async def test_ai_review_with_mock(self, client):
        """Test AI-powered MR review with mocked LLM."""
        # Mock MR and changes
        client.get_merge_request = AsyncMock(
            return_value=AsyncMock(
                iid=45,
                title="Test MR",
                description="Test description",
                source_branch="feature/test",
                target_branch="main",
            )
        )

        client.get_mr_changes = AsyncMock(
            return_value={
                "changes": [
                    {
                        "new_path": "test.py",
                        "diff": "+def test():\n+    pass\n",
                    }
                ]
            }
        )

        # Mock LLM response
        with patch("src.discovery.gitlab_enhanced.LiteLLMRouter") as mock_router:
            mock_router.return_value.complete = AsyncMock(
                return_value=json.dumps(
                    {
                        "approved": True,
                        "comments": ["Good implementation", "Tests are missing"],
                        "suggestions": ["Add unit tests"],
                        "confidence": 0.8,
                    }
                )
            )

            client.add_mr_comment = AsyncMock()

            # Perform review
            result = await client.review_mr_with_ai(
                project_id="test/project",
                mr_iid=45,
                include_diff=True,
            )

            assert result.mr_iid == 45
            assert result.approved is True
            assert len(result.review_comments) == 2
            assert "Tests are missing" in result.review_comments
            assert result.confidence_score == 0.8

    @pytest.mark.asyncio
    async def test_trigger_pipeline(self, client):
        """Test CI/CD pipeline triggering."""
        # Mock API response
        mock_response = {
            "id": 789,
            "ref": "main",
            "sha": "abc123",
            "status": "pending",
            "web_url": "https://gitlab.com/test/project/-/pipelines/789",
        }
        client._request.return_value = mock_response

        # Trigger pipeline
        config = PipelineConfig(
            trigger=PipelineTrigger.MANUAL,
            target_branch="main",
            variables={"TEST_VAR": "test_value"},
        )

        pipeline = await client.trigger_pipeline(
            project_id="test/project",
            config=config,
        )

        assert pipeline.id == 789
        assert pipeline.ref == "main"
        assert pipeline.status == "pending"

        # Verify API call
        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[0][0] == "POST"
        assert "pipeline" in call_args[0][1]

        # Check request data
        data = call_args[1]["data"]
        assert data["ref"] == "main"
        assert len(data["variables"]) == 1
        assert data["variables"][0]["key"] == "TEST_VAR"

    @pytest.mark.asyncio
    async def test_wait_for_pipeline(self, client):
        """Test waiting for pipeline completion."""
        # Mock pipeline responses
        client.get_pipeline = AsyncMock(
            side_effect=[
                AsyncMock(id=789, status="running"),
                AsyncMock(id=789, status="running"),
                AsyncMock(id=789, status="success"),
            ]
        )

        # Wait for completion
        pipeline = await client.wait_for_pipeline(
            project_id="test/project",
            pipeline_id=789,
            timeout=10,
        )

        assert pipeline.status == "success"
        assert client.get_pipeline.call_count == 3

    @pytest.mark.asyncio
    async def test_create_issue_from_error(self, client):
        """Test creating issue from error."""
        # Mock API response
        mock_response = {
            "id": 456,
            "iid": 23,
            "title": "Error: ValueError",
            "description": "Error details...",
        }
        client._request.return_value = mock_response

        # Mock current user
        client.get_current_user = AsyncMock(return_value={"id": 999})

        # Create issue from error
        error = ValueError("Test error message")
        context = {"file": "test.py", "line": 42}

        issue = await client.create_issue_from_error(
            project_id="test/project",
            error=error,
            context=context,
            assign_to_creator=True,
        )

        assert issue.iid == 23
        assert "Error: ValueError" in issue.title

        # Verify API call
        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[0][0] == "POST"
        assert "issues" in call_args[0][1]

        # Check error details in description
        data = call_args[1]["data"]
        assert "ValueError" in data["description"]
        assert "Test error message" in data["description"]
        assert "test.py" in data["description"]
        assert "42" in data["description"]

    @pytest.mark.asyncio
    async def test_webhook_management(self, client):
        """Test webhook creation and testing."""
        # Mock API responses
        create_response = {"id": 111, "url": "https://example.com/webhook"}
        test_response = {"success": True}
        client._request.side_effect = [create_response, test_response]

        # Create webhook
        webhook = await client.create_webhook(
            project_id="test/project",
            url="https://example.com/webhook",
            events=["push", "merge_requests", "pipeline"],
            secret_token="test_secret",
        )

        assert webhook["id"] == 111
        assert webhook["url"] == "https://example.com/webhook"

        # Test webhook
        result = await client.test_webhook(
            project_id="test/project",
            hook_id=111,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_merge_mr(self, client):
        """Test merging a merge request."""
        # Mock API response
        mock_response = {
            "id": 123,
            "iid": 45,
            "state": "merged",
            "merged_at": "2024-01-01T00:00:00Z",
        }
        client._request.return_value = mock_response

        # Merge MR
        result = await client.merge_mr(
            project_id="test/project",
            mr_iid=45,
            squash=True,
            should_remove_source_branch=True,
            merge_commit_message="Automated merge",
        )

        assert result["state"] == "merged"
        assert result["iid"] == 45

        # Verify API call
        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[0][0] == "PUT"
        assert "merge" in call_args[0][1]

        # Check merge options
        data = call_args[1]["data"]
        assert data["squash"] is True
        assert data["should_remove_source_branch"] is True
        assert data["merge_commit_message"] == "Automated merge"

    @pytest.mark.asyncio
    async def test_link_issue_to_mr(self, client):
        """Test linking an issue to a merge request."""
        # Mock API response
        mock_response = {
            "id": 789,
            "source_issue": {"id": 123},
            "target_issue": {"id": 456},
        }
        client._request.return_value = mock_response

        # Link issue to MR
        result = await client.link_issue_to_mr(
            project_id="test/project",
            issue_iid=23,
            mr_iid=45,
        )

        assert result["id"] == 789

        # Verify API call
        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[0][0] == "POST"
        assert "links" in call_args[0][1]


if __name__ == "__main__":
    # Run tests directly
    import sys

    print("Running GitLab Enhanced integration tests...")

    async def run_tests():
        test = TestGitLabEnhanced()

        try:
            async with patch(
                "src.discovery.gitlab_enhanced.GitLabClient.__init__"
            ) as mock_init:
                mock_init.return_value = None
                client = GitLabEnhanced()
                client._request = AsyncMock()
                client.test_connection = AsyncMock(return_value=True)

                await test.test_mr_templates(client)
                print("✓ MR templates test passed")

                await test.test_create_automated_mr(client)
                print("✓ Automated MR creation test passed")

                await test.test_trigger_pipeline(client)
                print("✓ Pipeline triggering test passed")

                await test.test_create_issue_from_error(client)
                print("✓ Issue from error test passed")

                await test.test_webhook_management(client)
                print("✓ Webhook management test passed")

                await test.test_merge_mr(client)
                print("✓ MR merge test passed")

                await test.test_link_issue_to_mr(client)
                print("✓ Issue-MR linking test passed")

            print("\nAll tests passed! ✓")

        except Exception as e:
            print(f"\nTest failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_tests())
