"""
Enhanced GitLab Client for VIBE MCP

Extended GitLab integration with advanced features:
- Merge request automation
- CI/CD pipeline integration
- Issue tracking automation
- Webhook management
- Project analytics

Builds on the existing GitLabClient with additional automation capabilities.
"""

import asyncio
import json
import logging
import os
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.core.safe_formatter import MR_FORMATTER
from src.llm.litellm_router import LiteLLMRouter
from src.platform.browser_automation import (
    BrowserAutomation,
    BrowserType,
    create_browser_automation,
)

from .gitlab_client import (
    GitLabClient,
    GitLabIssue,
    GitLabMergeRequest,
    GitLabPipeline,
)

secure_logger = logging.getLogger(__name__)


class MRAction(Enum):
    """Merge request actions."""
    CREATE = "create"
    UPDATE = "update"
    MERGE = "merge"
    CLOSE = "close"
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"


class PipelineTrigger(Enum):
    """Pipeline trigger types."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEB = "web"
    API = "api"


@dataclass
class MRTemplate:
    """Merge request template."""
    name: str
    title_template: str
    description_template: str
    labels: list[str] = field(default_factory=list)
    assignee_ids: list[int] = field(default_factory=list)
    reviewer_ids: list[int] = field(default_factory=list)


@dataclass
class MRReviewResult:
    """Result of MR review."""
    mr_iid: int
    approved: bool
    review_comments: list[str]
    suggested_changes: list[str]
    approval_required: bool = False
    confidence_score: float = 0.0


@dataclass
class PipelineConfig:
    """CI/CD pipeline configuration."""
    trigger: PipelineTrigger
    variables: dict[str, str] = field(default_factory=dict)
    target_branch: str | None = None
    dry_run: bool = False


class GitLabEnhanced(GitLabClient):
    """
    Enhanced GitLab client with automation features.

    Extends GitLabClient with:
    - Automated MR creation and management
    - CI/CD pipeline control
    - Intelligent code review
    - Webhook integration
    """

    def __init__(self, **kwargs):
        """Initialize enhanced GitLab client."""
        super().__init__(**kwargs)

        # Initialize LLM router for intelligent operations
        self.llm_router = LiteLLMRouter()

        # Browser automation for UI operations
        self.browser: BrowserAutomation | None = None

        # MR templates
        self.mr_templates: dict[str, MRTemplate] = {}
        self._load_mr_templates()

        # Webhook endpoints
        self.webhook_url = os.getenv("GITLAB_WEBHOOK_URL")

        secure_logger.info("Enhanced GitLab client initialized")

    def _load_mr_templates(self):
        """Load MR templates from configuration."""
        self.mr_templates = {
            "feature": MRTemplate(
                name="Feature",
                title_template="feat: {feature_name}",
                description_template="""
## Description
{description}

## Changes
- {changes}

## Testing
- {testing}

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
                """,
                labels=["feature", "ready-for-review"],
            ),
            "bugfix": MRTemplate(
                name="Bug Fix",
                title_template="fix: {issue_number} {issue_title}",
                description_template="""
## Fixes
Fixes #{issue_number}

## Description
{description}

## Root Cause
{root_cause}

## Solution
{solution}

## Testing
- {testing}

## Verification
- [ ] Bug is fixed
- [ ] No regressions introduced
- [ ] Tests pass
                """,
                labels=["bugfix", "ready-for-review"],
            ),
            "hotfix": MRTemplate(
                name="Hotfix",
                title_template="hotfix: {description}",
                description_template="""
## Hotfix for {branch}

## Issue
{issue}

## Fix
{fix}

## Impact
{impact}

## Testing
{testing}

## Deployment
- [ ] Tested in staging
- [ ] Ready for production
                """,
                labels=["hotfix", "urgent"],
            ),
        }

    # ========================================================================
    # MERGE REQUEST AUTOMATION
    # ========================================================================

    async def create_automated_mr(
        self,
        project_id: int | str,
        source_branch: str,
        target_branch: str,
        template_type: str,
        context: dict[str, Any],
        auto_assign: bool = True,
    ) -> GitLabMergeRequest:
        """
        Create an automated merge request.

        Args:
            project_id: Project ID or path
            source_branch: Source branch
            target_branch: Target branch
            template_type: Template type to use
            context: Context for template variables
            auto_assign: Auto-assign to current user

        Returns:
            Created merge request
        """
        template = self.mr_templates.get(template_type)
        if not template:
            raise ValueError(f"Unknown template type: {template_type}")

        # Generate title and description safely
        title = MR_FORMATTER.format_markdown(template.title_template, context)
        description = MR_FORMATTER.format_markdown(template.description_template, context)

        # Create MR
        mr_data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
        }

        if template.labels:
            mr_data["labels"] = ",".join(template.labels)

        if template.assignee_ids and auto_assign:
            mr_data["assignee_ids"] = template.assignee_ids

        if template.reviewer_ids:
            mr_data["reviewer_ids"] = template.reviewer_ids

        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/merge_requests"
        response = await self._request("POST", endpoint, data=mr_data)

        mr = self._parse_merge_request(response)
        secure_logger.info(f"Created MR {mr.iid}: {mr.title}")

        return mr

    async def review_mr_with_ai(
        self,
        project_id: int | str,
        mr_iid: int,
        include_diff: bool = True,
    ) -> MRReviewResult:
        """
        Review a merge request using AI.

        Args:
            project_id: Project ID or path
            mr_iid: MR IID
            include_diff: Whether to include code diff

        Returns:
            Review result
        """
        # Get MR details
        mr = await self.get_merge_request(project_id, mr_iid)

        # Get changes
        changes = None
        if include_diff:
            changes = await self.get_mr_changes(project_id, mr_iid)

        # Prepare review prompt
        prompt = self._build_review_prompt(mr, changes)

        # Get AI review
        response = await self.llm_router.complete(
            prompt=prompt,
            model="gpt-4",
            max_tokens=1000,
        )

        # Parse response
        review_result = self._parse_ai_review(response, mr_iid)

        # Post review as comment if needed
        if review_result.review_comments:
            await self.add_mr_comment(
                project_id,
                mr_iid,
                "\n".join(review_result.review_comments),
            )

        return review_result

    async def get_merge_request(
        self,
        project_id: int | str,
        mr_iid: int,
    ) -> GitLabMergeRequest:
        """Get a specific merge request."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/merge_requests/{mr_iid}"
        response = await self._request("GET", endpoint)
        return self._parse_merge_request(response)

    async def get_mr_changes(
        self,
        project_id: int | str,
        mr_iid: int,
    ) -> dict[str, Any]:
        """Get merge request changes."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/merge_requests/{mr_iid}/changes"
        return await self._request("GET", endpoint)

    async def add_mr_comment(
        self,
        project_id: int | str,
        mr_iid: int,
        comment: str,
    ) -> dict[str, Any]:
        """Add comment to merge request."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/merge_requests/{mr_iid}/notes"
        return await self._request("POST", endpoint, data={"body": comment})

    async def merge_mr(
        self,
        project_id: int | str,
        mr_iid: int,
        squash: bool = True,
        should_remove_source_branch: bool = True,
        merge_commit_message: str | None = None,
    ) -> dict[str, Any]:
        """Merge a merge request."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/merge_requests/{mr_iid}/merge"

        data = {
            "squash": squash,
            "should_remove_source_branch": should_remove_source_branch,
        }

        if merge_commit_message:
            data["merge_commit_message"] = merge_commit_message

        return await self._request("PUT", endpoint, data=data)

    def _build_review_prompt(
        self,
        mr: GitLabMergeRequest,
        changes: dict[str, Any] | None,
    ) -> str:
        """Build AI review prompt."""
        prompt = f"""
Review this merge request:

Title: {mr.title}
Description: {mr.description}
Source Branch: {mr.source_branch}
Target Branch: {mr.target_branch}

"""

        if changes:
            prompt += "\nChanges:\n"
            for change in changes.get("changes", [])[:5]:  # Limit to 5 files
                prompt += f"\nFile: {change.get('new_path', change.get('old_path', ''))}\n"
                prompt += f"```diff\n{change.get('diff', '')[:500]}\n```\n"

        prompt += """
Please review and provide:
1. Overall assessment (approve/request changes)
2. Specific issues found
3. Suggested improvements
4. Security concerns
5. Code quality feedback

Format your response as JSON:
{
    "approved": true/false,
    "comments": ["comment1", "comment2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": 0.8
}
"""

        return prompt

    def _parse_ai_review(self, response: str, mr_iid: int) -> MRReviewResult:
        """Parse AI review response."""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                return MRReviewResult(
                    mr_iid=mr_iid,
                    approved=data.get("approved", False),
                    review_comments=data.get("comments", []),
                    suggested_changes=data.get("suggestions", []),
                    confidence_score=data.get("confidence", 0.0),
                )
        except Exception:
            pass

        # Fallback
        return MRReviewResult(
            mr_iid=mr_iid,
            approved=False,
            review_comments=["AI review parsing failed"],
            suggested_changes=[],
            confidence_score=0.0,
        )

    # ========================================================================
    # CI/CD PIPELINE AUTOMATION
    # ========================================================================

    async def trigger_pipeline(
        self,
        project_id: int | str,
        config: PipelineConfig,
    ) -> GitLabPipeline:
        """
        Trigger a CI/CD pipeline.

        Args:
            project_id: Project ID or path
            config: Pipeline configuration

        Returns:
            Triggered pipeline
        """
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/pipeline"

        data = {
            "ref": config.target_branch or "main",
        }

        if config.variables:
            data["variables"] = [
                {"key": k, "value": v}
                for k, v in config.variables.items()
            ]

        response = await self._request("POST", endpoint, data=data)
        pipeline = self._parse_pipeline(response)

        secure_logger.info(f"Triggered pipeline {pipeline.id} for {pipeline.ref}")
        return pipeline

    async def wait_for_pipeline(
        self,
        project_id: int | str,
        pipeline_id: int,
        timeout: int = 1800,  # 30 minutes
    ) -> GitLabPipeline:
        """
        Wait for pipeline to complete.

        Args:
            project_id: Project ID or path
            pipeline_id: Pipeline ID
            timeout: Timeout in seconds

        Returns:
            Final pipeline status
        """
        start_time = datetime.now()

        while True:
            pipeline = await self.get_pipeline(project_id, pipeline_id)

            if pipeline.status in ["success", "failed", "canceled", "skipped"]:
                return pipeline

            # Check timeout
            if (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Pipeline {pipeline_id} did not complete within {timeout}s")

            # Wait before polling
            await asyncio.sleep(10)

    async def get_pipeline(
        self,
        project_id: int | str,
        pipeline_id: int,
    ) -> GitLabPipeline:
        """Get specific pipeline."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/pipelines/{pipeline_id}"
        response = await self._request("GET", endpoint)
        return self._parse_pipeline(response)

    async def get_pipeline_jobs(
        self,
        project_id: int | str,
        pipeline_id: int,
    ) -> list[dict[str, Any]]:
        """Get jobs for a pipeline."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/pipelines/{pipeline_id}/jobs"
        return await self._paginate(endpoint)

    async def retry_pipeline_job(
        self,
        project_id: int | str,
        job_id: int,
    ) -> dict[str, Any]:
        """Retry a failed pipeline job."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/jobs/{job_id}/retry"
        return await self._request("POST", endpoint)

    # ========================================================================
    # ISSUE AUTOMATION
    # ========================================================================

    async def create_issue_from_error(
        self,
        project_id: int | str,
        error: Exception,
        context: dict[str, Any],
        assign_to_creator: bool = True,
    ) -> GitLabIssue:
        """
        Create an issue from an error.

        Args:
            project_id: Project ID or path
            error: Exception that occurred
            context: Additional context
            assign_to_creator: Assign to current user

        Returns:
            Created issue
        """
        # Get current user if needed
        assignee_id = None
        if assign_to_creator:
            user = await self.get_current_user()
            assignee_id = user["id"]

        # Build issue content
        title = f"Error: {type(error).__name__}"

        description = f"""
## Error Details
- **Type**: {type(error).__name__}
- **Message**: {str(error)}
- **Time**: {datetime.now().isoformat()}

## Context
{json.dumps(context, indent=2)}

## Stack Trace
```python
{traceback.format_exc()}
```

## Action Items
- [ ] Investigate root cause
- [ ] Implement fix
- [ ] Add tests to prevent regression
        """

        # Create issue
        return await self.create_issue(
            project_id=project_id,
            title=title,
            description=description,
            labels=["bug", "auto-generated"],
            assignee_ids=[assignee_id] if assignee_id else None,
        )

    async def link_issue_to_mr(
        self,
        project_id: int | str,
        issue_iid: int,
        mr_iid: int,
    ) -> dict[str, Any]:
        """Link an issue to a merge request."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/issues/{issue_iid}/links"

        data = {
            "target_project_id": project_id,
            "target_issue_iid": mr_iid,
            "link_type": "relates_to",
        }

        return await self._request("POST", endpoint, data=data)

    # ========================================================================
    # WEBHOOK MANAGEMENT
    # ========================================================================

    async def create_webhook(
        self,
        project_id: int | str,
        url: str,
        events: list[str],
        secret_token: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a webhook.

        Args:
            project_id: Project ID or path
            url: Webhook URL
            events: List of events
            secret_token: Secret token for validation

        Returns:
            Created webhook
        """
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/hooks"

        data = {
            "url": url,
            "push_events": "push" in events,
            "merge_requests_events": "merge_requests" in events,
            "issues_events": "issues" in events,
            "pipeline_events": "pipeline" in events,
        }

        if secret_token:
            data["token"] = secret_token

        return await self._request("POST", endpoint, data=data)

    async def test_webhook(
        self,
        project_id: int | str,
        hook_id: int,
    ) -> dict[str, Any]:
        """Test a webhook."""
        endpoint = f"/projects/{str(project_id).replace('/', '%2F')}/hooks/{hook_id}/test"
        return await self._request("POST", endpoint)

    # ========================================================================
    # BROWSER INTEGRATION
    # ========================================================================

    async def open_in_browser(
        self,
        url: str,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headed: bool = False,
    ) -> BrowserAutomation:
        """
        Open GitLab page in browser for manual operations.

        Args:
            url: GitLab URL to open
            browser_type: Browser to use
            headed: Show browser window

        Returns:
            Browser automation instance
        """
        self.browser = await create_browser_automation(
            browser_type=browser_type,
            headless=not headed,
        )

        await self.browser.navigate(url)
        return self.browser

    async def close_browser(self):
        """Close browser if open."""
        if self.browser:
            await self.browser.close()
            self.browser = None


# Factory function
async def create_gitlab_enhanced(**kwargs) -> GitLabEnhanced:
    """
    Create and initialize enhanced GitLab client.

    Args:
        **kwargs: Arguments for GitLabEnhanced

    Returns:
        Initialized enhanced GitLab client
    """
    client = GitLabEnhanced(**kwargs)

    # Test connection
    if await client.test_connection():
        return client
    else:
        secure_logger.warning("GitLab connection failed")
        return client


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    import asyncio
    import traceback

    async def main():
        parser = argparse.ArgumentParser(description="Enhanced GitLab Client Test")
        parser.add_argument("--project", required=True, help="Project ID or path")
        parser.add_argument("--action", choices=["mr", "pipeline", "issue"], required=True)
        parser.add_argument("--source-branch", help="Source branch for MR")
        parser.add_argument("--target-branch", default="main", help="Target branch for MR")
        parser.add_argument("--title", help="MR/Issue title")
        parser.add_argument("--description", help="MR/Issue description")

        args = parser.parse_args()

        # Create client
        client = await create_gitlab_enhanced()

        async with client:
            if args.action == "mr":
                # Create automated MR
                if not args.source_branch:
                    print("Error: --source-branch required for MR creation")
                    return

                context = {
                    "feature_name": args.title or "Test Feature",
                    "description": args.description or "Test description",
                    "changes": "- Test change",
                    "testing": "- Manual testing",
                }

                mr = await client.create_automated_mr(
                    project_id=args.project,
                    source_branch=args.source_branch,
                    target_branch=args.target_branch,
                    template_type="feature",
                    context=context,
                )

                print(f"\nCreated MR #{mr.iid}: {mr.title}")
                print(f"URL: {mr.web_url}")

                # AI review
                review = await client.review_mr_with_ai(args.project, mr.iid)
                print(f"\nAI Review: {'Approved' if review.approved else 'Changes Requested'}")
                print(f"Confidence: {review.confidence_score:.2f}")
                for comment in review.review_comments:
                    print(f"  - {comment}")

            elif args.action == "pipeline":
                # Trigger pipeline
                config = PipelineConfig(
                    trigger=PipelineTrigger.MANUAL,
                    target_branch=args.target_branch,
                )

                pipeline = await client.trigger_pipeline(args.project, config)
                print(f"\nTriggered pipeline #{pipeline.id}")
                print(f"Status: {pipeline.status}")
                print(f"URL: {pipeline.web_url}")

                # Wait for completion
                print("\nWaiting for pipeline...")
                final_pipeline = await client.wait_for_pipeline(args.project, pipeline.id)
                print(f"Final status: {final_pipeline.status}")

    asyncio.run(main())
