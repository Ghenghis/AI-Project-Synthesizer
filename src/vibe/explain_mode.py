"""
Explain Mode for VIBE MCP

Provides explanations for code decisions and changes:
- Code decision explanations
- Change impact analysis
- Implementation reasoning
- Best practice justifications
- Learning from explanations

Helps users understand why certain decisions were made.
"""

import ast
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.llm.litellm_router import LiteLLMRouter
from src.memory.mem0_integration import MemorySystem


class ExplanationType(Enum):
    """Types of explanations."""

    CODE_DECISION = "code_decision"
    ARCHITECTURAL = "architectural"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    FEATURE_ADDITION = "feature_addition"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTING = "testing"


class ExplanationLevel(Enum):
    """Detail levels for explanations."""

    BRIEF = "brief"  # One sentence explanation
    STANDARD = "standard"  # Paragraph with key points
    DETAILED = "detailed"  # Full explanation with examples
    TECHNICAL = "technical"  # Deep dive with technical details


@dataclass
class CodeChange:
    """Represents a code change."""

    file_path: str
    old_code: str | None
    new_code: str
    change_type: str  # add, modify, delete
    line_numbers: tuple[int, int]


@dataclass
class Explanation:
    """An explanation of code decisions."""

    id: str
    type: ExplanationType
    level: ExplanationLevel
    title: str
    summary: str
    reasoning: list[str]
    alternatives: list[str]
    impact: dict[str, Any]
    best_practices: list[str]
    examples: list[str] | None
    timestamp: datetime


class ExplainMode:
    """
    Provides explanations for code decisions and changes.

    Features:
    - Multiple explanation types
    - Configurable detail levels
    - Impact analysis
    - Best practice references
    - Learning from explanations
    """

    def __init__(self):
        self.config = get_settings()
        self.llm_router = LiteLLMRouter()
        self.memory = MemorySystem()

        # Explanation history
        self._explanations: list[Explanation] = []

        # Configuration
        self.default_level = ExplanationLevel.STANDARD
        self.max_examples = 3

    async def explain_code_change(
        self,
        change: CodeChange,
        context: dict[str, Any] | None = None,
        level: ExplanationLevel | None = None,
    ) -> Explanation:
        """
        Explain a code change.

        Args:
            change: The code change to explain
            context: Additional context (project, task, etc.)
            level: Detail level for explanation

        Returns:
            Detailed explanation
        """
        level = level or self.default_level

        # Determine explanation type
        exp_type = self._classify_change(change, context)

        # Generate explanation
        explanation = await self._generate_explanation(change, exp_type, level, context)

        # Store explanation
        self._explanations.append(explanation)

        # Save to memory for learning
        await self._save_explanation(explanation, change, context)

        return explanation

    async def explain_architectural_decision(
        self,
        decision: str,
        components: list[str],
        context: dict[str, Any] | None = None,
        level: ExplanationLevel | None = None,
    ) -> Explanation:
        """
        Explain an architectural decision.

        Args:
            decision: The architectural decision made
            components: Components affected by the decision
            context: Additional context
            level: Detail level for explanation

        Returns:
            Detailed explanation
        """
        level = level or self.default_level

        # Generate explanation
        explanation = await self._generate_architectural_explanation(
            decision, components, level, context
        )

        # Store and save
        self._explanations.append(explanation)
        await self._save_explanation(explanation, {"decision": decision}, context)

        return explanation

    async def explain_refactoring(
        self,
        before: str,
        after: str,
        file_path: str,
        context: dict[str, Any] | None = None,
        level: ExplanationLevel | None = None,
    ) -> Explanation:
        """
        Explain a refactoring decision.

        Args:
            before: Code before refactoring
            after: Code after refactoring
            file_path: Path to the file
            context: Additional context
            level: Detail level for explanation

        Returns:
            Detailed explanation
        """
        level = level or self.default_level

        # Analyze changes
        changes = self._analyze_refactoring(before, after)

        # Generate explanation
        explanation = await self._generate_refactoring_explanation(
            changes, file_path, level, context
        )

        # Store and save
        self._explanations.append(explanation)
        await self._save_explanation(explanation, {"file": file_path}, context)

        return explanation

    def _classify_change(
        self, change: CodeChange, context: dict[str, Any] | None
    ) -> ExplanationType:
        """Classify the type of change for explanation."""
        code_lower = change.new_code.lower()

        # Security patterns
        security_keywords = ["auth", "token", "encrypt", "hash", "validate", "sanitize"]
        if any(kw in code_lower for kw in security_keywords):
            return ExplanationType.SECURITY

        # Performance patterns
        perf_keywords = ["cache", "optimize", "async", "batch", "pool", "lazy"]
        if any(kw in code_lower for kw in perf_keywords):
            return ExplanationType.PERFORMANCE

        # Testing patterns
        test_keywords = ["test", "spec", "mock", "assert", "fixture"]
        if any(kw in code_lower for kw in test_keywords) or "test" in change.file_path:
            return ExplanationType.TESTING

        # Bug fix patterns
        if context and "fix" in context.get("task", "").lower():
            return ExplanationType.BUG_FIX

        # Feature addition
        if change.change_type == "add" and len(change.new_code) > 50:
            return ExplanationType.FEATURE_ADDITION

        # Default
        return ExplanationType.CODE_DECISION

    async def _generate_explanation(
        self,
        change: CodeChange,
        exp_type: ExplanationType,
        level: ExplanationLevel,
        context: dict[str, Any] | None,
    ) -> Explanation:
        """Generate explanation using LLM."""
        # Build prompt based on level
        if level == ExplanationLevel.BRIEF:
            prompt = f"""Explain this code change in one sentence:

File: {change.file_path}
Type: {change.change_type}
Code: {change.new_code[:500]}...

Focus on: {exp_type.value}"""
        elif level == ExplanationLevel.STANDARD:
            prompt = f"""Explain this code change:

File: {change.file_path}
Type: {change.change_type}
Lines: {change.line_numbers[0]}-{change.line_numbers[1]}
Code: {change.new_code}

Context: {json.dumps(context or {}, indent=2)}

Provide:
1. Clear summary of what was changed
2. Why this change was necessary
3. Impact on the system
4. Key best practices followed"""
        else:  # DETAILED or TECHNICAL
            prompt = f"""Provide a detailed explanation of this code change:

File: {change.file_path}
Type: {change.change_type}
Lines: {change.line_numbers[0]}-{change.line_numbers[1]}
Before: {change.old_code or "N/A"}
After: {change.new_code}

Context: {json.dumps(context or {}, indent=2)}

Provide comprehensive explanation including:
1. What was changed and why
2. Technical reasoning behind the approach
3. Alternative approaches considered
4. Impact on performance, security, and maintainability
5. Best practices and design patterns applied
6. Potential risks or considerations
7. Related code or documentation

Return as JSON:
{{
    "title": "Brief title",
    "summary": "One paragraph summary",
    "reasoning": ["Point 1", "Point 2", "Point 3"],
    "alternatives": ["Alternative 1", "Alternative 2"],
    "impact": {{
        "performance": "Low/Medium/High",
        "security": "Low/Medium/High",
        "maintainability": "Low/Medium/High"
    }},
    "best_practices": ["Practice 1", "Practice 2"],
    "examples": ["Example 1", "Example 2"]
}}"""

        try:
            # Get LLM response
            response = await self.llm_router.generate(
                prompt=prompt, model="claude-sonnet", max_tokens=1500
            )

            # Parse response
            if level in [ExplanationType.DETAILED, ExplanationType.TECHNICAL]:
                data = json.loads(response)
            else:
                # Convert text response to structured format
                data = self._parse_text_explanation(response, level)

            return Explanation(
                id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=exp_type,
                level=level,
                title=data.get(
                    "title", f"Code change in {Path(change.file_path).name}"
                ),
                summary=data.get("summary", response[:200]),
                reasoning=data.get("reasoning", []),
                alternatives=data.get("alternatives", []),
                impact=data.get("impact", {}),
                best_practices=data.get("best_practices", []),
                examples=data.get("examples")
                if level != ExplanationLevel.BRIEF
                else None,
                timestamp=datetime.now(),
            )

        except Exception as e:
            # Fallback explanation
            return Explanation(
                id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=exp_type,
                level=ExplanationLevel.BRIEF,
                title=f"Code change in {Path(change.file_path).name}",
                summary=f"Changed {change.change_type} code in {change.file_path}",
                reasoning=[f"Error generating explanation: {str(e)}"],
                alternatives=[],
                impact={},
                best_practices=[],
                examples=None,
                timestamp=datetime.now(),
            )

    async def _generate_architectural_explanation(
        self,
        decision: str,
        components: list[str],
        level: ExplanationLevel,
        context: dict[str, Any] | None,
    ) -> Explanation:
        """Generate architectural decision explanation."""
        prompt = f"""Explain this architectural decision:

Decision: {decision}
Components: {", ".join(components)}
Context: {json.dumps(context or {}, indent=2)}

Provide explanation including:
1. Why this architecture was chosen
2. How it addresses the requirements
3. Trade-offs made
4. Scalability and maintenance implications
5. Alternative patterns considered

Return as JSON:
{{
    "title": "Brief title",
    "summary": "One paragraph summary",
    "reasoning": ["Point 1", "Point 2", "Point 3"],
    "alternatives": ["Alternative 1", "Alternative 2"],
    "impact": {{
        "scalability": "Low/Medium/High",
        "complexity": "Low/Medium/High",
        "maintenance": "Low/Medium/High"
    }},
    "best_practices": ["Practice 1", "Practice 2"]
}}"""

        try:
            response = await self.llm_router.generate(
                prompt=prompt, model="claude-sonnet", max_tokens=1000
            )

            data = json.loads(response)

            return Explanation(
                id=f"arch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=ExplanationType.ARCHITECTURAL,
                level=level,
                title=data.get("title", "Architectural Decision"),
                summary=data.get("summary", decision[:200]),
                reasoning=data.get("reasoning", []),
                alternatives=data.get("alternatives", []),
                impact=data.get("impact", {}),
                best_practices=data.get("best_practices", []),
                examples=None,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return Explanation(
                id=f"arch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=ExplanationType.ARCHITECTURAL,
                level=ExplanationLevel.BRIEF,
                title="Architectural Decision",
                summary=decision,
                reasoning=[f"Error generating explanation: {str(e)}"],
                alternatives=[],
                impact={},
                best_practices=[],
                examples=None,
                timestamp=datetime.now(),
            )

    async def _generate_refactoring_explanation(
        self,
        changes: dict[str, Any],
        file_path: str,
        level: ExplanationLevel,
        context: dict[str, Any] | None,
    ) -> Explanation:
        """Generate refactoring explanation."""
        prompt = f"""Explain this refactoring:

File: {file_path}
Changes: {json.dumps(changes, indent=2)}
Context: {json.dumps(context or {}, indent=2)}

Explain:
1. What problems existed in the original code
2. How the refactoring addresses these issues
3. Benefits achieved
4. Risks or considerations

Return as JSON:
{{
    "title": "Brief title",
    "summary": "One paragraph summary",
    "reasoning": ["Point 1", "Point 2", "Point 3"],
    "alternatives": ["Alternative approach"],
    "impact": {{
        "readability": "Low/Medium/High",
        "performance": "Low/Medium/High",
        "maintainability": "Low/Medium/High"
    }},
    "best_practices": ["Practice 1", "Practice 2"]
}}"""

        try:
            response = await self.llm_router.generate(
                prompt=prompt, model="claude-sonnet", max_tokens=1000
            )

            data = json.loads(response)

            return Explanation(
                id=f"ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=ExplanationType.REFACTORING,
                level=level,
                title=data.get("title", f"Refactoring in {Path(file_path).name}"),
                summary=data.get("summary", "Code was refactored for improvement"),
                reasoning=data.get("reasoning", []),
                alternatives=data.get("alternatives", []),
                impact=data.get("impact", {}),
                best_practices=data.get("best_practices", []),
                examples=None,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return Explanation(
                id=f"ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=ExplanationType.REFACTORING,
                level=ExplanationLevel.BRIEF,
                title="Refactoring",
                summary=f"Refactored code in {file_path}",
                reasoning=[f"Error generating explanation: {str(e)}"],
                alternatives=[],
                impact={},
                best_practices=[],
                examples=None,
                timestamp=datetime.now(),
            )

    def _parse_text_explanation(
        self, text: str, _level: ExplanationLevel
    ) -> dict[str, Any]:
        """Parse text explanation into structured format."""
        lines = text.strip().split("\n")

        return {
            "title": lines[0] if lines else "Code Change",
            "summary": "\n".join(lines[:3]) if lines else "",
            "reasoning": [
                line.strip()
                for line in lines
                if line.strip() and not line.startswith(" ")
            ],
            "alternatives": [],
            "impact": {},
            "best_practices": [],
        }

    def _analyze_refactoring(self, before: str, after: str) -> dict[str, Any]:
        """Analyze what changed in a refactoring."""
        changes = {
            "lines_added": 0,
            "lines_removed": 0,
            "functions_added": [],
            "functions_removed": [],
            "complexity_change": "unknown",
        }

        try:
            before_tree = ast.parse(before)
            after_tree = ast.parse(after)

            # Count functions
            before_funcs = [
                node.name
                for node in ast.walk(before_tree)
                if isinstance(node, ast.FunctionDef)
            ]
            after_funcs = [
                node.name
                for node in ast.walk(after_tree)
                if isinstance(node, ast.FunctionDef)
            ]

            changes["functions_added"] = list(set(after_funcs) - set(before_funcs))
            changes["functions_removed"] = list(set(before_funcs) - set(after_funcs))

            # Count lines
            changes["lines_added"] = len(after.split("\n")) - len(before.split("\n"))
            changes["lines_removed"] = max(0, -changes["lines_added"])

        except Exception:
            # Fallback to line counting
            changes["lines_added"] = len(after.split("\n"))
            changes["lines_removed"] = len(before.split("\n"))

        return changes

    async def _save_explanation(
        self,
        explanation: Explanation,
        change_data: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> None:
        """Save explanation to memory for learning."""
        data = {
            "explanation": {
                "id": explanation.id,
                "type": explanation.type.value,
                "level": explanation.level.value,
                "title": explanation.title,
                "summary": explanation.summary,
                "reasoning": explanation.reasoning,
                "best_practices": explanation.best_practices,
            },
            "change": change_data,
            "context": context,
            "timestamp": explanation.timestamp.isoformat(),
        }

        await self.memory.add(
            content=json.dumps(data),
            category="EXPLANATION",
            tags=["explanation", explanation.type.value],
            importance=0.6,
        )

    def get_explanation_history(
        self, exp_type: ExplanationType | None = None
    ) -> list[Explanation]:
        """Get explanation history."""
        if exp_type:
            return [e for e in self._explanations if e.type == exp_type]
        return self._explanations.copy()

    def create_explanation_report(self, explanations: list[Explanation]) -> str:
        """Create a markdown report of explanations."""
        report = ["# Code Explanations Report\n"]

        for exp in explanations:
            report.append(f"## {exp.title}")
            report.append(f"**Type:** {exp.type.value} | **Level:** {exp.level.value}")
            report.append(f"**Time:** {exp.timestamp.strftime('%Y-%m-%d %H:%M')}")
            report.append("")
            report.append("### Summary")
            report.append(exp.summary)
            report.append("")

            if exp.reasoning:
                report.append("### Reasoning")
                for point in exp.reasoning:
                    report.append(f"- {point}")
                report.append("")

            if exp.alternatives:
                report.append("### Alternatives Considered")
                for alt in exp.alternatives:
                    report.append(f"- {alt}")
                report.append("")

            if exp.impact:
                report.append("### Impact Analysis")
                for aspect, level in exp.impact.items():
                    report.append(f"- **{aspect.title()}:** {level}")
                report.append("")

            if exp.best_practices:
                report.append("### Best Practices Applied")
                for practice in exp.best_practices:
                    report.append(f"- {practice}")
                report.append("")

            report.append("---\n")

        return "\n".join(report)


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        explain = ExplainMode()

        # Test code change explanation
        change = CodeChange(
            file_path="src/example.py",
            old_code="def add(a, b):\n    return a + b",
            new_code='def add(a: int, b: int) -> int:\n    """Add two integers."""\n    return a + b',
            change_type="modify",
            line_numbers=(1, 3),
        )

        context = {"task": "Add type hints to functions", "project": "VIBE MCP"}

        print("Generating explanation...")
        explanation = await explain.explain_code_change(
            change, context, level=ExplanationLevel.STANDARD
        )

        print(f"\nTitle: {explanation.title}")
        print(f"Type: {explanation.type.value}")
        print(f"\nSummary: {explanation.summary}")

        if explanation.reasoning:
            print("\nReasoning:")
            for point in explanation.reasoning:
                print(f"  - {point}")

        if explanation.best_practices:
            print("\nBest Practices:")
            for practice in explanation.best_practices:
                print(f"  - {practice}")

        # Test architectural explanation
        print("\n\nGenerating architectural explanation...")
        arch_exp = await explain.explain_architectural_decision(
            decision="Use microservices architecture for scalability",
            components=["API Gateway", "User Service", "Order Service"],
            context={"scale": "high", "team_size": "large"},
        )

        print(f"\nTitle: {arch_exp.title}")
        print(f"Summary: {arch_exp.summary}")

        # Create report
        report = explain.create_explanation_report([explanation, arch_exp])
        with open("explanations_report.md", "w") as f:
            f.write(report)
        print("\nReport saved to: explanations_report.md")

    asyncio.run(main())
