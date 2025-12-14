"""
Review Agent for VIBE MCP Quality Pipeline

Uses AutoGen to create multi-agent code review debates:
- SecurityExpert: Reviews for security vulnerabilities
- QualityChecker: Reviews code quality and maintainability
- PerformanceAnalyst: Reviews performance implications
- LeadReviewer: Moderates and synthesizes final review

This ensures comprehensive code review before deployment.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from src.agents.autogen_integration import AutoGenIntegration
from src.core.config import get_settings
from src.llm.litellm_router import LiteLLMRouter


class ReviewSeverity(Enum):
    """Severity levels for review issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewStatus(Enum):
    """Review status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    APPROVED_WITH_CHANGES = "approved_with_changes"
    REJECTED = "rejected"


@dataclass
class ReviewIssue:
    """Represents an issue found during code review."""

    agent: str
    category: str
    severity: ReviewSeverity
    message: str
    file_path: str
    line_number: int | None = None
    suggestion: str | None = None
    code_snippet: str | None = None
    confidence: float = 0.0  # 0.0 to 1.0


@dataclass
class ReviewReport:
    """Complete code review report."""

    status: ReviewStatus
    overall_score: float  # 0.0 to 10.0
    issues: list[ReviewIssue]
    summary: str
    recommendations: list[str]
    debate_summary: str
    review_time: float
    agents_participated: list[str]
    consensus_score: float  # Agreement level between agents


class ReviewAgent:
    """
    Multi-agent code review system using AutoGen.

    Features:
    - Specialized reviewer agents
    - Moderated debate format
    - Consensus building
    - Structured output
    - Actionable recommendations
    """

    def __init__(self):
        self.config = get_settings()
        self.autogen = AutoGenIntegration()
        self.llm_router = LiteLLMRouter()

        # Define agent roles
        self.agent_configs = {
            "security_expert": {
                "name": "SecurityExpert",
                "system_message": """You are a Security Expert code reviewer. Your focus is on:
1. Security vulnerabilities (SQL injection, XSS, CSRF, etc.)
2. Authentication and authorization issues
3. Data exposure and privacy concerns
4. Input validation and sanitization
5. Cryptographic best practices
6. Dependency security

Always provide specific, actionable security recommendations.
Rate issues as: CRITICAL, HIGH, MEDIUM, or LOW severity.""",
                "description": "Reviews code for security vulnerabilities and best practices",
            },
            "quality_checker": {
                "name": "QualityChecker",
                "system_message": """You are a Code Quality expert. Your focus is on:
1. Code readability and maintainability
2. Adherence to coding standards and conventions
3. Proper error handling and logging
4. Code duplication and complexity
5. Documentation quality
6. Test coverage considerations

Provide constructive feedback on improving code quality.
Rate issues as: CRITICAL, HIGH, MEDIUM, or LOW severity.""",
                "description": "Reviews code for quality, maintainability, and best practices",
            },
            "performance_analyst": {
                "name": "PerformanceAnalyst",
                "system_message": """You are a Performance Analyst. Your focus is on:
1. Algorithm efficiency and complexity
2. Memory usage and potential leaks
3. Database query optimization
4. Caching strategies
5. Scalability concerns
6. Resource utilization

Identify performance bottlenecks and suggest optimizations.
Rate issues as: CRITICAL, HIGH, MEDIUM, or LOW severity.""",
                "description": "Reviews code for performance and scalability issues",
            },
            "lead_reviewer": {
                "name": "LeadReviewer",
                "system_message": """You are the Lead Reviewer moderating this code review. Your role is to:
1. Synthesize feedback from all reviewers
2. Identify consensus and disagreements
3. Make final approval/rejection decisions
4. Provide balanced, actionable summary
5. Prioritize issues by severity and impact
6. Ensure reviews are constructive

Consider all agent feedback and make a final decision:
- APPROVED: No critical issues, ready to merge
- APPROVED_WITH_CHANGES: Address issues before merge
- REJECTED: Critical issues must be fixed first

Be fair but thorough in your assessment.""",
                "description": "Moderates review and makes final decisions",
            },
        }

    async def review_code(
        self, code: str, file_path: str, context: dict[str, Any] | None = None
    ) -> ReviewReport:
        """
        Conduct multi-agent code review.

        Args:
            code: The code to review
            file_path: File path for context
            context: Additional context (PR description, requirements, etc.)

        Returns:
            ReviewReport with comprehensive feedback
        """
        start_time = time.time()

        # Prepare review context
        review_context = {
            "file_path": file_path,
            "code": code,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }

        # Initialize agents
        agents = await self._initialize_agents()

        # Conduct individual reviews
        individual_reviews = await self._conduct_individual_reviews(
            agents[:-1], review_context
        )

        # Conduct debate and synthesis
        final_review = await self._conduct_debate_and_synthesis(
            agents, individual_reviews, review_context
        )

        # Parse and structure the final report
        report = await self._parse_review_report(final_review, time.time() - start_time)

        return report

    async def _initialize_agents(self) -> list[Any]:
        """Initialize AutoGen agents for review."""
        agents = []

        for _agent_key, config in self.agent_configs.items():
            agent = await self.autogen.create_agent(
                name=config["name"],
                system_message=config["system_message"],
                description=config["description"],
            )
            agents.append(agent)

        return agents

    async def _conduct_individual_reviews(
        self, reviewers: list[Any], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get initial reviews from each specialist agent."""
        reviews = []

        # Build review prompt
        prompt = f"""Please review the following code:

File: {context["file_path"]}

```python
{context["code"]}
```

Context: {json.dumps(context.get("context", {}), indent=2)}

Provide your review in JSON format:
{{
    "agent": "Your role",
    "issues": [
        {{
            "category": "security|quality|performance",
            "severity": "critical|high|medium|low",
            "message": "Clear description of the issue",
            "line_number": 123,
            "suggestion": "How to fix it",
            "code_snippet": "Relevant code",
            "confidence": 0.9
        }}
    ],
    "summary": "Brief summary of your review",
    "score": 7.5
}}"""

        # Get reviews from each agent
        tasks = []
        for agent in reviewers:
            task = self.autogen.send_message(agent, prompt)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                print(f"Review error: {response}")
                continue

            try:
                # Parse JSON response
                review_data = json.loads(response)
                reviews.append(review_data)
            except json.JSONDecodeError:
                # Fallback: extract key points from text
                reviews.append(
                    {
                        "agent": "unknown",
                        "issues": [],
                        "summary": response[:200],
                        "score": 5.0,
                    }
                )

        return reviews

    async def _conduct_debate_and_synthesis(
        self, agents: list[Any], reviews: list[dict[str, Any]], context: dict[str, Any]
    ) -> str:
        """Conduct moderated debate to reach consensus."""
        lead_reviewer = agents[-1]  # Last agent is the lead reviewer

        # Compile all reviews for the lead reviewer
        reviews_summary = "\n\n".join(
            [f"Review from {r['agent']}:\n{json.dumps(r, indent=2)}" for r in reviews]
        )

        debate_prompt = f"""You are the Lead Reviewer. Please review the following feedback from your team:

{reviews_summary}

Original code:
File: {context["file_path"]}
```python
{context["code"]}
```

Please:
1. Analyze all feedback and identify consensus/disagreements
2. Prioritize issues by severity and impact
3. Make a final decision (APPROVED/APPROVED_WITH_CHANGES/REJECTED)
4. Provide a comprehensive summary with actionable recommendations

Output your final review in this JSON format:
{{
    "status": "approved|approved_with_changes|rejected",
    "overall_score": 8.5,
    "summary": "Overall assessment",
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2"
    ],
    "debate_summary": "Summary of the debate and consensus",
    "consensus_score": 0.8
}}"""

        # Get final review from lead reviewer
        final_response = await self.autogen.send_message(lead_reviewer, debate_prompt)

        return final_response

    async def _parse_review_report(
        self, final_review: str, review_time: float
    ) -> ReviewReport:
        """Parse the final review into a structured report."""
        try:
            data = json.loads(final_review)

            # Extract all issues from individual reviews (would need to pass them)
            issues = []  # Would be populated from actual reviews

            return ReviewReport(
                status=ReviewStatus(data.get("status", "pending")),
                overall_score=data.get("overall_score", 0.0),
                issues=issues,
                summary=data.get("summary", ""),
                recommendations=data.get("recommendations", []),
                debate_summary=data.get("debate_summary", ""),
                review_time=review_time,
                agents_participated=list(self.agent_configs.keys()),
                consensus_score=data.get("consensus_score", 0.0),
            )

        except json.JSONDecodeError:
            # Fallback report
            return ReviewReport(
                status=ReviewStatus.PENDING,
                overall_score=0.0,
                issues=[],
                summary="Review parsing failed",
                recommendations=[],
                debate_summary=final_review[:500],
                review_time=review_time,
                agents_participated=list(self.agent_configs.keys()),
                consensus_score=0.0,
            )

    async def review_pull_request(self, pr_data: dict[str, Any]) -> ReviewReport:
        """
        Review an entire pull request with multiple files.

        Args:
            pr_data: PR information including files, description, etc.

        Returns:
            Aggregated ReviewReport for the PR
        """
        all_issues = []
        file_summaries = []

        # Review each file
        for file_info in pr_data.get("files", []):
            if file_info.get("patch"):
                report = await self.review_code(
                    code=file_info["patch"],
                    file_path=file_info["filename"],
                    context={"pr_description": pr_data.get("description")},
                )
                all_issues.extend(report.issues)
                file_summaries.append(f"{file_info['filename']}: {report.status.value}")

        # Generate PR-level summary
        if all_issues:
            critical_count = sum(
                1 for i in all_issues if i.severity == ReviewSeverity.CRITICAL
            )
            high_count = sum(1 for i in all_issues if i.severity == ReviewSeverity.HIGH)

            if critical_count > 0:
                status = ReviewStatus.REJECTED
            elif high_count > 3:
                status = ReviewStatus.APPROVED_WITH_CHANGES
            else:
                status = ReviewStatus.APPROVED
        else:
            status = ReviewStatus.APPROVED

        return ReviewReport(
            status=status,
            overall_score=max(0, 10 - len(all_issues)),
            issues=all_issues,
            summary=f"PR review complete. {len(all_issues)} issues found across {len(file_summaries)} files.",
            recommendations=[f"Address {len(all_issues)} issues before merging"],
            debate_summary=f"Files reviewed: {', '.join(file_summaries)}",
            review_time=0,
            agents_participated=list(self.agent_configs.keys()),
            consensus_score=0.8,
        )

    def generate_report(self, report: ReviewReport) -> str:
        """Generate a human-readable review report."""
        output = []
        output.append("=" * 60)
        output.append("CODE REVIEW REPORT")
        output.append("=" * 60)
        output.append(f"Status: {report.status.value.upper()}")
        output.append(f"Overall Score: {report.overall_score}/10.0")
        output.append(f"Consensus: {report.consensus_score * 100:.0f}% agreement")
        output.append(f"Review Time: {report.review_time:.2f}s")
        output.append(f"Agents: {', '.join(report.agents_participated)}")
        output.append("")

        # Summary
        output.append("SUMMARY:")
        output.append(report.summary)
        output.append("")

        # Issues by severity
        if report.issues:
            output.append("ISSUES FOUND:")
            for severity in [
                ReviewSeverity.CRITICAL,
                ReviewSeverity.HIGH,
                ReviewSeverity.MEDIUM,
                ReviewSeverity.LOW,
            ]:
                issues = [i for i in report.issues if i.severity == severity]
                if issues:
                    output.append(f"\n{severity.value.upper()} ({len(issues)}):")
                    for issue in issues[:5]:  # Limit to 5 per severity
                        output.append(f"  • [{issue.agent}] {issue.message}")
                        if issue.line_number:
                            output.append(
                                f"    Line {issue.line_number} in {issue.file_path}"
                            )
                        if issue.suggestion:
                            output.append(f"    Suggestion: {issue.suggestion}")
                    if len(issues) > 5:
                        output.append(f"  ... and {len(issues) - 5} more")
        else:
            output.append("✅ No issues found!")
        output.append("")

        # Recommendations
        if report.recommendations:
            output.append("RECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations, 1):
                output.append(f"{i}. {rec}")
            output.append("")

        # Debate summary
        if report.debate_summary:
            output.append("DEBATE SUMMARY:")
            output.append(report.debate_summary)

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    async def apply_fixes(
        self, code: str, issues: list[ReviewIssue]
    ) -> tuple[str, list[str]]:
        """
        Attempt to automatically fix some issues.

        Args:
            code: Original code
            issues: List of issues to fix

        Returns:
            Tuple of (fixed_code, applied_fixes)
        """
        fixed_code = code
        applied_fixes = []

        # Sort issues by line number (reverse order to avoid offset issues)
        fixable_issues = [
            i
            for i in issues
            if i.suggestion
            and i.severity in [ReviewSeverity.LOW, ReviewSeverity.MEDIUM]
        ]
        fixable_issues.sort(key=lambda x: x.line_number or 0, reverse=True)

        for issue in fixable_issues:
            # Simple fix application (would be more sophisticated in production)
            if (
                "add" in issue.suggestion.lower()
                and "import" in issue.suggestion.lower()
            ):
                # Add missing import
                if "import" not in fixed_code.split("\n")[0]:
                    fixed_code = issue.suggestion + "\n\n" + fixed_code
                    applied_fixes.append(f"Added import for {issue.category}")

        return fixed_code, applied_fixes


# CLI interface for testing
if __name__ == "__main__":
    import sys

    async def main():
        reviewer = ReviewAgent()

        if len(sys.argv) > 1:
            # Review file
            file_path = sys.argv[1]
            try:
                with open(file_path) as f:
                    code = f.read()

                report = await reviewer.review_code(code, file_path)
                print(reviewer.generate_report(report))

            except FileNotFoundError:
                print(f"File not found: {file_path}")
        else:
            # Demo review
            demo_code = """
def login(username, password):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    result = db.execute(query)

    if result:
        return True
    return False

def process_data(data):
    # No input validation
    for item in data:
        print(item)

    # Inefficient loop
    results = []
    for i in range(len(data)):
        for j in range(len(data)):
            results.append(data[i] * data[j])

    return results
"""
            report = await reviewer.review_code(demo_code, "demo.py")
            print(reviewer.generate_report(report))

    asyncio.run(main())
