"""
AI Project Synthesizer - Code Fixer Agent

AI-powered agent that automatically fixes code issues:
- Linting errors
- Type errors
- Import issues
- Bug fixes
- Code style improvements

Integrates with LM Studio / Ollama for local AI inference.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.core.security import get_secure_logger
from src.llm.router import LLMRouter

secure_logger = get_secure_logger(__name__)
logger = secure_logger.logger


class FixCategory(str, Enum):
    """Categories of code fixes."""

    LINT = "lint"
    TYPE = "type"
    IMPORT = "import"
    BUG = "bug"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class CodeIssue:
    """Represents a code issue to fix."""

    file_path: str
    line_number: int | None
    category: FixCategory
    message: str
    code_context: str = ""
    severity: str = "warning"


@dataclass
class CodeFix:
    """Represents a proposed fix."""

    issue: CodeIssue
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float = 0.0
    applied: bool = False


@dataclass
class FixResult:
    """Result of fix operation."""

    success: bool
    fixes_applied: list[CodeFix] = field(default_factory=list)
    fixes_failed: list[CodeFix] = field(default_factory=list)
    summary: str = ""


class CodeFixerAgent:
    """
    AI-powered code fixer agent.

    Uses local LLM (LM Studio/Ollama) to analyze and fix code issues.
    """

    SYSTEM_PROMPT = """You are an expert Python code fixer. Your job is to fix code issues.

When given a code issue:
1. Analyze the problem carefully
2. Provide ONLY the fixed code, no explanations
3. Preserve the original code structure and style
4. Fix only the specific issue mentioned
5. Keep all existing comments and docstrings

Output format:
```python
<fixed code here>
```

Be precise and minimal in your changes."""

    FIX_PROMPT_TEMPLATE = """Fix this {category} issue in Python:

File: {file_path}
Line: {line_number}
Issue: {message}

Original code:
```python
{code_context}
```

Provide ONLY the fixed code block."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.settings = get_settings()
        self.llm_router: LLMRouter | None = None
        self._fixes_cache: dict[str, CodeFix] = {}

    async def initialize(self):
        """Initialize the LLM router."""
        if self.llm_router is None:
            self.llm_router = LLMRouter()
            await self.llm_router.initialize()

    async def analyze_issue(self, issue: CodeIssue) -> str | None:
        """Analyze an issue and get fix suggestion from LLM."""
        await self.initialize()

        prompt = self.FIX_PROMPT_TEMPLATE.format(
            category=issue.category.value,
            file_path=issue.file_path,
            line_number=issue.line_number or "N/A",
            message=issue.message,
            code_context=issue.code_context,
        )

        try:
            response = await self.llm_router.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for precise fixes
            )
            return response
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None

    def extract_code_from_response(self, response: str) -> str | None:
        """Extract code block from LLM response."""
        # Try to find Python code block
        pattern = r"```(?:python)?\s*\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # If no code block, return cleaned response
        lines = response.strip().split("\n")
        code_lines = [
            l for l in lines if not l.startswith("#") or "=" in l or "def " in l
        ]
        return "\n".join(code_lines) if code_lines else None

    def get_code_context(
        self, file_path: Path, line_number: int, context_lines: int = 10
    ) -> str:
        """Get code context around a specific line."""
        try:
            content = file_path.read_text()
            lines = content.split("\n")

            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)

            context_lines_list = []
            for i, line in enumerate(lines[start:end], start=start + 1):
                marker = ">>>" if i == line_number else "   "
                context_lines_list.append(f"{marker} {i}: {line}")

            return "\n".join(context_lines_list)
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return ""

    async def fix_issue(self, issue: CodeIssue) -> CodeFix | None:
        """Attempt to fix a single issue."""
        # Get code context if not provided
        if not issue.code_context and issue.line_number:
            file_path = self.project_root / issue.file_path
            if file_path.exists():
                issue.code_context = self.get_code_context(file_path, issue.line_number)

        # Get fix from LLM
        response = await self.analyze_issue(issue)
        if not response:
            return None

        # Extract fixed code
        fixed_code = self.extract_code_from_response(response)
        if not fixed_code:
            return None

        return CodeFix(
            issue=issue,
            original_code=issue.code_context,
            fixed_code=fixed_code,
            explanation=f"AI-generated fix for {issue.category.value} issue",
            confidence=0.8,
        )

    async def fix_multiple_issues(self, issues: list[CodeIssue]) -> FixResult:
        """Fix multiple issues."""
        result = FixResult(success=True)

        for issue in issues:
            try:
                fix = await self.fix_issue(issue)
                if fix:
                    result.fixes_applied.append(fix)
                else:
                    result.fixes_failed.append(
                        CodeFix(
                            issue=issue,
                            original_code="",
                            fixed_code="",
                            explanation="Could not generate fix",
                        )
                    )
            except Exception as e:
                logger.error(f"Error fixing issue: {e}")
                result.success = False

        result.summary = (
            f"Fixed {len(result.fixes_applied)}/{len(issues)} issues. "
            f"Failed: {len(result.fixes_failed)}"
        )

        return result

    def apply_fix(self, fix: CodeFix, dry_run: bool = False) -> bool:
        """Apply a fix to the actual file."""
        if dry_run:
            logger.info(f"[DRY RUN] Would apply fix to {fix.issue.file_path}")
            return True

        file_path = self.project_root / fix.issue.file_path
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        try:
            content = file_path.read_text()

            # Simple line replacement for single-line fixes
            if fix.issue.line_number:
                lines = content.split("\n")
                if 0 < fix.issue.line_number <= len(lines):
                    # Replace the specific line
                    fixed_lines = fix.fixed_code.split("\n")
                    if len(fixed_lines) == 1:
                        lines[fix.issue.line_number - 1] = fixed_lines[0]
                        file_path.write_text("\n".join(lines))
                        fix.applied = True
                        logger.info(
                            f"Applied fix to {fix.issue.file_path}:{fix.issue.line_number}"
                        )
                        return True

            logger.warning("Could not apply multi-line fix automatically")
            return False

        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return False

    async def auto_fix_file(self, file_path: Path, issues: list[dict]) -> FixResult:
        """Auto-fix all issues in a file."""
        code_issues = []
        for issue in issues:
            code_issues.append(
                CodeIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=issue.get("line"),
                    category=FixCategory(issue.get("category", "lint")),
                    message=issue.get("message", ""),
                    severity=issue.get("severity", "warning"),
                )
            )

        return await self.fix_multiple_issues(code_issues)


class AutoTestGenerator:
    """
    AI-powered unit test generator.

    Generates pytest tests for Python functions/classes.
    """

    SYSTEM_PROMPT = """You are an expert Python test writer. Generate comprehensive pytest tests.

Requirements:
1. Use pytest style (not unittest)
2. Include edge cases and error conditions
3. Use descriptive test names
4. Add docstrings explaining what each test verifies
5. Use fixtures where appropriate
6. Target 80%+ code coverage

Output format:
```python
import pytest
# ... test code ...
```"""

    TEST_PROMPT_TEMPLATE = """Generate pytest unit tests for this Python code:

```python
{code}
```

Requirements:
- Test all public methods/functions
- Include edge cases
- Test error handling
- Aim for 80%+ coverage

Generate ONLY the test code."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.settings = get_settings()
        self.llm_router: LLMRouter | None = None

    async def initialize(self):
        """Initialize LLM router."""
        if self.llm_router is None:
            self.llm_router = LLMRouter()
            await self.llm_router.initialize()

    async def generate_tests(self, source_code: str, file_name: str = "") -> str | None:
        """Generate tests for source code."""
        await self.initialize()

        prompt = self.TEST_PROMPT_TEMPLATE.format(code=source_code)

        try:
            response = await self.llm_router.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.2,
            )

            # Extract code block
            pattern = r"```(?:python)?\s*\n(.*?)\n```"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
            return response

        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            return None

    async def generate_tests_for_file(self, file_path: Path) -> str | None:
        """Generate tests for a Python file."""
        if not file_path.exists():
            return None

        source_code = file_path.read_text()
        return await self.generate_tests(source_code, file_path.name)


class CodeReviewAgent:
    """
    AI-powered code review agent.

    Reviews code for:
    - Best practices
    - Security issues
    - Performance problems
    - Code style
    """

    SYSTEM_PROMPT = """You are an expert Python code reviewer. Review code for:

1. **Security**: SQL injection, XSS, secrets in code, etc.
2. **Performance**: N+1 queries, unnecessary loops, memory leaks
3. **Best Practices**: SOLID principles, clean code, DRY
4. **Style**: PEP 8, type hints, docstrings
5. **Bugs**: Logic errors, edge cases, null checks

Output format:
```json
{
  "issues": [
    {
      "severity": "high|medium|low",
      "category": "security|performance|style|bug",
      "line": 10,
      "message": "Description",
      "suggestion": "How to fix"
    }
  ],
  "summary": "Overall assessment",
  "score": 85
}
```"""

    REVIEW_PROMPT_TEMPLATE = """Review this Python code:

File: {file_name}

```python
{code}
```

Provide a detailed review in JSON format."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.llm_router: LLMRouter | None = None

    async def initialize(self):
        """Initialize LLM router."""
        if self.llm_router is None:
            self.llm_router = LLMRouter()
            await self.llm_router.initialize()

    async def review_code(
        self, code: str, file_name: str = ""
    ) -> dict[str, Any] | None:
        """Review code and return structured feedback."""
        await self.initialize()

        prompt = self.REVIEW_PROMPT_TEMPLATE.format(file_name=file_name, code=code)

        try:
            response = await self.llm_router.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=1500,
                temperature=0.3,
            )

            # Extract JSON
            json_pattern = r"```(?:json)?\s*\n(.*?)\n```"
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                return json.loads(match.group(1))

            # Try to parse entire response as JSON
            return json.loads(response)

        except json.JSONDecodeError:
            logger.error("Could not parse review response as JSON")
            return {"summary": response, "issues": [], "score": 0}
        except Exception as e:
            logger.error(f"Error reviewing code: {e}")
            return None

    async def review_file(self, file_path: Path) -> dict[str, Any] | None:
        """Review a Python file."""
        if not file_path.exists():
            return None

        code = file_path.read_text()
        return await self.review_code(code, file_path.name)


# Convenience functions for CLI usage
async def fix_file(file_path: str, issues: list[dict]) -> FixResult:
    """Fix issues in a file."""
    agent = CodeFixerAgent()
    return await agent.auto_fix_file(Path(file_path), issues)


async def generate_tests(file_path: str) -> str | None:
    """Generate tests for a file."""
    generator = AutoTestGenerator()
    return await generator.generate_tests_for_file(Path(file_path))


async def review_file(file_path: str) -> dict[str, Any] | None:
    """Review a file."""
    agent = CodeReviewAgent()
    return await agent.review_file(Path(file_path))
